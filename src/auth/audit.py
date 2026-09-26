"""
Security and Administrative Audit Logger for Panama PortOps-AI v2.0
Records structured event telemetry for IAM, auth attempts, and administrative actions.
Author: Desarrollado v1.0 Miguel Benítez - GNU GPL-3.0
"""

import uuid
import hashlib
import sqlite3
from datetime import datetime, timezone
from typing import Optional, Dict, Any


class SecurityAuditLogger:
    """Logs security events with anonymized IP and user agent hashing."""

    @classmethod
    def _hash_val(cls, val: Optional[str]) -> str:
        if not val:
            return "none"
        return hashlib.sha256(val.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def log_event(
        cls,
        conn: sqlite3.Connection,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        result: str = "SUCCESS",
        reason: Optional[str] = None
    ) -> str:
        """Records a security event in the database."""
        event_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).isoformat()
        ip_hash = cls._hash_val(ip_address)
        ua_hash = cls._hash_val(user_agent)

        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO security_events (
            event_id, actor_id, action, resource_type, resource_id,
            ip_hash, user_agent_hash, result, reason, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (event_id, actor_id, action, resource_type, resource_id, ip_hash, ua_hash, result, reason, now_str))
        conn.commit()
        return event_id
