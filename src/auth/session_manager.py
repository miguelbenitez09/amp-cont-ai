"""
Session Manager and Secure Cookie Handler for Panama PortOps-AI v2.0
Handles session state, token hashing, revocation, and security headers.
Author: Desarrollado v1.0 Miguel Benítez - GNU GPL-3.0
"""

import uuid
import hashlib
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple


class SessionManager:
    """Manages active user sessions with token hashing and instant revocation."""

    SESSION_TTL_HOURS = 12

    @classmethod
    def _hash_token(cls, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    def create_session(
        cls,
        conn: sqlite3.Connection,
        user_id: str,
        token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """Stores a new session with hashed token."""
        session_id = str(uuid.uuid4())
        token_hash = cls._hash_token(token)
        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(hours=cls.SESSION_TTL_HOURS)).isoformat()
        now_str = now.isoformat()

        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO sessions (session_id, user_id, token_hash, ip_address, user_agent, expires_at, is_revoked, last_activity_at)
        VALUES (?, ?, ?, ?, ?, ?, 0, ?);
        """, (session_id, user_id, token_hash, ip_address or "127.0.0.1", user_agent or "Unknown", expires_at, now_str))
        conn.commit()
        return session_id

    @classmethod
    def validate_session(cls, conn: sqlite3.Connection, token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Validates that session is active, not revoked, and not expired."""
        token_hash = cls._hash_token(token)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT session_id, user_id, expires_at, is_revoked, last_activity_at
        FROM sessions
        WHERE token_hash = ?;
        """, (token_hash,))
        row = cursor.fetchone()

        if not row:
            return False, None, "Sesión no encontrada en el registro activo."

        session_id, user_id, expires_at_str, is_revoked, _ = row

        if is_revoked:
            return False, None, "Esta sesión ha sido revocada por razones de seguridad."

        now = datetime.now(timezone.utc)
        expires_at = datetime.fromisoformat(expires_at_str)
        if now > expires_at:
            return False, None, "La sesión ha expirado por inactividad."

        # Update last activity
        cursor.execute("UPDATE sessions SET last_activity_at = ? WHERE session_id = ?;", (now.isoformat(), session_id))
        conn.commit()

        return True, {"session_id": session_id, "user_id": user_id}, None

    @classmethod
    def revoke_session(cls, conn: sqlite3.Connection, token: str) -> bool:
        """Revokes a specific session by token."""
        token_hash = cls._hash_token(token)
        cursor = conn.cursor()
        cursor.execute("UPDATE sessions SET is_revoked = 1 WHERE token_hash = ?;", (token_hash,))
        conn.commit()
        return cursor.rowcount > 0

    @classmethod
    def revoke_all_user_sessions(cls, conn: sqlite3.Connection, user_id: str) -> int:
        """Revokes all active sessions for a user upon credential rotation."""
        cursor = conn.cursor()
        cursor.execute("UPDATE sessions SET is_revoked = 1 WHERE user_id = ? AND is_revoked = 0;", (user_id,))
        conn.commit()
        return cursor.rowcount
