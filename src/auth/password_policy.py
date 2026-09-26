"""
Password Policy Enforcement Module for Panama PortOps-AI v2.0
Implements NIST SP 800-63B guidelines and strict enterprise complexity.
Author: Desarrollado v1.0 Miguel Benítez - GNU GPL-3.0
"""

import re
from typing import Tuple, List, Optional
import sqlite3
import hashlib


class PasswordPolicy:
    """Enforces strict password complexity and history checks."""

    MIN_LENGTH = 12
    HISTORY_LIMIT = 5

    @classmethod
    def validate_complexity(cls, password: str) -> Tuple[bool, List[str]]:
        """
        Validates password against complexity requirements:
        - Min length 12
        - Uppercase, lowercase, numbers, special characters
        """
        errors = []
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"La contraseña debe tener al menos {cls.MIN_LENGTH} caracteres.")
        if not re.search(r"[A-Z]", password):
            errors.append("Debe contener al menos una letra mayúscula (A-Z).")
        if not re.search(r"[a-z]", password):
            errors.append("Debe contener al menos una letra minúscula (a-z).")
        if not re.search(r"[0-9]", password):
            errors.append("Debe contener al menos un dígito numérico (0-9).")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
            errors.append("Debe contener al menos un carácter especial (!@#$%^&*...).")

        return len(errors) == 0, errors

    @classmethod
    def check_history(cls, conn: sqlite3.Connection, user_id: str, new_password_hash: str) -> Tuple[bool, Optional[str]]:
        """Ensures password has not been used in the last N changes."""
        cursor = conn.cursor()
        cursor.execute("""
        SELECT password_hash FROM password_history
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?;
        """, (user_id, cls.HISTORY_LIMIT))
        previous_hashes = [r[0] for r in cursor.fetchall()]

        if new_password_hash in previous_hashes:
            return False, f"La contraseña no puede ser igual a ninguna de las últimas {cls.HISTORY_LIMIT} contraseñas utilizadas."

        return True, None
