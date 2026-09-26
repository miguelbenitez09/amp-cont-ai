"""
Enterprise Model Registry and Promotion Lifecycle Manager for Panama PortOps-AI v2.0
Governs model states: DRAFT -> TRAINED -> VALIDATED -> REVIEW -> APPROVED -> STAGED -> PRODUCTION -> RETIRED
Author: Desarrollado v1.0 Miguel Benítez - GNU GPL-3.0
"""

import uuid
import json
import sqlite3
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone


class ModelLifecycleManager:
    """Manages model registration, approvals, champion/challenger status, and promotions."""

    VALID_STATES = [
        "DRAFT", "TRAINED", "VALIDATED", "REVIEW", "APPROVED", "STAGED", "PRODUCTION", "RETIRED", "REJECTED"
    ]

    @classmethod
    def register_model(
        cls,
        conn: sqlite3.Connection,
        model_name: str,
        version_tag: str,
        algorithm: str,
        dataset_hash: str,
        parameters: Dict[str, Any],
        metrics: Dict[str, float],
        created_by: str = "mlops_engineer"
    ) -> str:
        """Registers a newly trained model in VALIDATED state."""
        model_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).isoformat()
        params_json = json.dumps(parameters)

        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO model_registry (
            model_id, model_name, version_tag, algorithm, dataset_hash,
            parameters_json, wape_score, mae_score, rmse_score, r2_score,
            pinball_loss, status, is_champion, created_by, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'VALIDATED', 0, ?, ?, ?);
        """, (
            model_id, model_name, version_tag, algorithm, dataset_hash,
            params_json, metrics.get("wape"), metrics.get("mae"), metrics.get("rmse"),
            metrics.get("r2"), metrics.get("pinball_loss"), created_by, now_str, now_str
        ))
        conn.commit()
        return model_id

    @classmethod
    def request_promotion(
        cls,
        conn: sqlite3.Connection,
        model_id: str,
        requested_by: str,
        notes: str = ""
    ) -> Tuple[bool, str, Optional[str]]:
        """Moves model to REVIEW state and creates an approval request."""
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM model_registry WHERE model_id = ?;", (model_id,))
        row = cursor.fetchone()
        if not row:
            return False, "Modelo no encontrado en el registro.", None

        request_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).isoformat()

        cursor.execute("""
        UPDATE model_registry
        SET status = 'REVIEW', updated_at = ?
        WHERE model_id = ?;
        """, (now_str, model_id))

        cursor.execute("""
        INSERT INTO model_approvals (
            request_id, model_id, requested_by, target_environment, status,
            reviewer_notes, created_at
        ) VALUES (?, ?, ?, 'production', 'PENDING', ?, ?);
        """, (request_id, model_id, requested_by, notes, now_str))

        conn.commit()
        return True, "Solicitud de promoción enviada para dictamen de ML Reviewer.", request_id

    @classmethod
    def approve_promotion(
        cls,
        conn: sqlite3.Connection,
        request_id: str,
        reviewer_id: str,
        reviewer_roles: List[str],
        notes: str = ""
    ) -> Tuple[bool, str]:
        """
        Approves model promotion to PRODUCTION.
        Enforces rule: reviewer MUST have 'ml_reviewer' or 'root' role.
        """
        if "ml_reviewer" not in reviewer_roles and "root" not in reviewer_roles:
            return False, "Permiso denegado: Solo usuarios con rol 'ml_reviewer' o 'root' pueden aprobar promociones a producción."

        cursor = conn.cursor()
        cursor.execute("SELECT model_id, status FROM model_approvals WHERE request_id = ?;", (request_id,))
        row = cursor.fetchone()
        if not row:
            return False, "Solicitud de aprobación no encontrada."

        model_id, req_status = row
        if req_status != "PENDING":
            return False, f"La solicitud ya se encuentra en estado '{req_status}'."

        now_str = datetime.now(timezone.utc).isoformat()

        # Retire current champion
        cursor.execute("""
        UPDATE model_registry
        SET is_champion = 0, status = 'RETIRED', updated_at = ?
        WHERE is_champion = 1;
        """, (now_str,))

        # Promote new champion
        cursor.execute("""
        UPDATE model_registry
        SET is_champion = 1, status = 'PRODUCTION', approved_by = ?, updated_at = ?
        WHERE model_id = ?;
        """, (reviewer_id, now_str, model_id))

        # Update approval request
        cursor.execute("""
        UPDATE model_approvals
        SET status = 'APPROVED', reviewer_notes = ?, approved_by = ?, approved_at = ?
        WHERE request_id = ?;
        """, (notes, reviewer_id, now_str, request_id))

        conn.commit()
        return True, "Modelo promovido exitosamente a Champion de Producción."

    @classmethod
    def list_models(cls, conn: sqlite3.Connection) -> List[Dict[str, Any]]:
        """Lists all registered models with their metadata."""
        cursor = conn.cursor()
        cursor.execute("""
        SELECT model_id, model_name, version_tag, algorithm, dataset_hash,
               wape_score, mae_score, rmse_score, r2_score, pinball_loss,
               status, is_champion, created_by, approved_by, created_at, updated_at
        FROM model_registry
        ORDER BY created_at DESC;
        """)
        cols = [c[0] for c in cursor.description]
        return [dict(zip(cols, r)) for r in cursor.fetchall()]

    @classmethod
    def get_champion_model(cls, conn: sqlite3.Connection) -> Optional[Dict[str, Any]]:
        """Retrieves the active production champion model."""
        cursor = conn.cursor()
        cursor.execute("""
        SELECT model_id, model_name, version_tag, algorithm, dataset_hash,
               wape_score, mae_score, rmse_score, r2_score, pinball_loss,
               status, is_champion, created_by, approved_by, created_at
        FROM model_registry
        WHERE is_champion = 1
        LIMIT 1;
        """)
        row = cursor.fetchone()
        if not row:
            return None
        cols = [c[0] for c in cursor.description]
        return dict(zip(cols, row))
