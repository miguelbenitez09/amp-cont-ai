"""
Cryptographic Root Bootstrap Engine for Panama PortOps-AI v2.0
Generates one-time CSPRNG root credentials, enforces initial rotation,
and establishes zero-knowledge emergency recovery keys.
Author: Desarrollado v1.0 Miguel Benítez - GNU GPL-3.0
"""

import os
import sys
import stat
import uuid
import secrets
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from src.auth.authentication import AuthenticationEngine
from src.auth.audit import SecurityAuditLogger

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BOOTSTRAP_DIR = ROOT_DIR / ".bootstrap"


class BootstrapManager:
    """Handles cryptographic root user initialization and recovery key distribution."""

    @classmethod
    def is_root_initialized(cls, conn: sqlite3.Connection) -> bool:
        """Checks if a root user already exists in the database."""
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_root = 1;")
        count = cursor.fetchone()[0]
        return count > 0

    @classmethod
    def get_root_username(cls, conn: sqlite3.Connection) -> Optional[str]:
        """Returns the username of the active root user if initialized."""
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE is_root = 1 LIMIT 1;")
        row = cursor.fetchone()
        return row[0] if row else None

    @classmethod
    def initialize_root_user(cls, conn: sqlite3.Connection) -> Dict[str, Any]:
        """
        Cryptographically initializes the root bootstrap user:
        - Username: root_<random_hex>
        - Password: 32+ character CSPRNG secret
        - Recovery code: 32-character hexadecimal token
        - Idempotent: skips if root already exists
        """
        if cls.is_root_initialized(conn):
            existing_user = cls.get_root_username(conn)
            return {
                "status": "already_initialized",
                "message": f"Usuario root ya existe ({existing_user}). Bootstrap omitido por idempotencia.",
                "root_username": existing_user
            }

        # 1. CSPRNG Generation
        random_suffix = secrets.token_hex(3)
        root_username = f"root_{random_suffix}"
        root_password = secrets.token_urlsafe(24)  # 32 characters, high entropy
        recovery_code = secrets.token_hex(16)
        user_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).isoformat()

        # 2. Hash Credentials
        pwd_hash, salt = AuthenticationEngine.hash_password(root_password)
        recovery_hash = hashlib.sha256(recovery_code.encode("utf-8")).hexdigest()

        cursor = conn.cursor()
        # 3. Insert Root User
        cursor.execute("""
        INSERT INTO users (
            user_id, username, email, password_hash, salt, is_active, is_root,
            must_change_password, mfa_enabled, recovery_code_hash, failed_attempts,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, 1, 1, 1, 0, ?, 0, ?, ?);
        """, (user_id, root_username, f"{root_username}@portops.local", pwd_hash, salt, recovery_hash, now_str, now_str))

        # 4. Assign Root Role
        cursor.execute("""
        INSERT OR IGNORE INTO user_roles (user_id, role_id, assigned_by, assigned_at)
        VALUES (?, 'root', 'SYSTEM_BOOTSTRAP', ?);
        """, (user_id, now_str))

        # 5. Record initial password history
        cursor.execute("""
        INSERT INTO password_history (user_id, password_hash, created_at)
        VALUES (?, ?, ?);
        """, (user_id, pwd_hash, now_str))

        # 6. Log Security Event (only hash/fingerprint, NEVER raw secret)
        pwd_fingerprint = hashlib.sha256(pwd_hash.encode()).hexdigest()[:12]
        SecurityAuditLogger.log_event(
            conn=conn,
            actor_id="BOOTSTRAP",
            action="INITIALIZE_ROOT_USER",
            resource_type="USER",
            resource_id=user_id,
            result="SUCCESS",
            reason=f"Root bootstrap initialized. Password fingerprint: {pwd_fingerprint}"
        )

        conn.commit()

        # 7. Write credentials to secured temporary file
        BOOTSTRAP_DIR.mkdir(parents=True, exist_ok=True)
        cred_file = BOOTSTRAP_DIR / "root-credentials.txt"
        
        credentials_content = f"""================================================================================
PANAMA PORTOPS-AI v2.0 - ROOT BOOTSTRAP CREDENTIALS
Generated: {now_str}
================================================================================
Username:      {root_username}
Password:      {root_password}
Recovery Code: {recovery_code}

INSTRUCCIONES DE SEGURIDAD CRÍTICA:
1. Inicie sesión inmediatamente en la plataforma con estas credenciales.
2. El sistema EXIGE el cambio de contraseña en el primer inicio de sesión.
3. Configure MFA (Autenticación de Dos Factores) en el perfil de root.
4. Una vez validado el acceso, ELIMINE este archivo ({cred_file}).
5. NUNCA utilice la cuenta root para operaciones diarias (use platform_admin / mlops_engineer).
================================================================================
"""
        with open(cred_file, "w", encoding="utf-8") as f:
            f.write(credentials_content)

        # Set restrictive permissions if on POSIX
        try:
            os.chmod(cred_file, stat.S_IRUSR | stat.S_IWUSR)
        except Exception:
            pass

        return {
            "status": "created",
            "root_username": root_username,
            "root_password": root_password,
            "recovery_code": recovery_code,
            "credentials_file": str(cred_file),
            "message": "Usuario root creado con éxito. Contraseña generada por CSPRNG."
        }
