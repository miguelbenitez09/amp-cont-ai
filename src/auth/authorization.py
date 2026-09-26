"""
Authorization Engine (RBAC + ABAC) for Panama PortOps-AI v2.0
Backend is the final authority for all authorization decisions.
Author: Desarrollado v1.0 Miguel Benítez - GNU GPL-3.0
"""

import sqlite3
from typing import Dict, Any, List, Optional, Tuple


class AuthorizationEngine:
    """Evaluates Subject + Role + Permission + Resource + Action + Context (RBAC + ABAC)."""

    @classmethod
    def get_user_roles(cls, conn: sqlite3.Connection, user_id: str) -> List[str]:
        """Retrieves active role IDs for a given user."""
        cursor = conn.cursor()
        cursor.execute("SELECT role_id FROM user_roles WHERE user_id = ?;", (user_id,))
        return [r[0] for r in cursor.fetchall()]

    @classmethod
    def get_user_permissions(cls, conn: sqlite3.Connection, user_id: str) -> List[str]:
        """Retrieves combined permissions assigned through all roles of a user."""
        cursor = conn.cursor()
        cursor.execute("""
        SELECT DISTINCT rp.permission_id
        FROM user_roles ur
        JOIN role_permissions rp ON ur.role_id = rp.role_id
        WHERE ur.user_id = ?;
        """, (user_id,))
        return [r[0] for r in cursor.fetchall()]

    @classmethod
    def has_permission(
        cls,
        conn: sqlite3.Connection,
        user_id: str,
        permission_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Evaluates whether user has the requested permission, factoring in RBAC and ABAC rules.
        """
        cursor = conn.cursor()
        
        # 1. Check if user is root (root has full emergency override)
        cursor.execute("SELECT is_root, is_active FROM users WHERE user_id = ?;", (user_id,))
        user_row = cursor.fetchone()
        if not user_row:
            return False, "Usuario no encontrado."
        if not user_row[1]:
            return False, "Cuenta de usuario desactivada."
        if user_row[0] == 1:
            return True, "Acceso concedido vía Root Emergency Privilege."

        # 2. Check RBAC permissions
        roles = cls.get_user_roles(conn, user_id)
        if not roles:
            return False, "El usuario no tiene roles asignados."

        permissions = cls.get_user_permissions(conn, user_id)
        has_perm = (permission_id in permissions)

        if not has_perm:
            # Check wildcard prefix (e.g. "data.*")
            prefix = permission_id.split(".")[0] + ".*"
            has_perm = (prefix in permissions) or ("*" in permissions)

        if not has_perm:
            return False, f"Permiso denegado: falta permiso requerido '{permission_id}'."

        # 3. ABAC Policy Rules (Context evaluation)
        if context:
            # Rule A: Production model promotion requires ML Reviewer or Root approval
            if permission_id == "model.promote" and context.get("environment") == "production":
                if "ml_reviewer" not in roles and "root" not in roles:
                    return False, "ABAC Denied: Promoción a producción requiere rol 'ml_reviewer' con aprobación formal."

            # Rule B: High compute simulation requires quota check
            if permission_id == "simulation.run":
                requested_paths = context.get("paths", 1000)
                if requested_paths > 10000 and "platform_admin" not in roles and "root" not in roles:
                    return False, "ABAC Denied: Simulaciones superiores a 10,000 trayectorias requieren privilegios administrativos."

            # Rule C: Secret management restricted to security_admin or root
            if permission_id.startswith("secret."):
                if "security_admin" not in roles and "root" not in roles:
                    return False, "ABAC Denied: Gestión de secretos restringida a 'security_admin' o 'root'."

        return True, "Acceso concedido."
