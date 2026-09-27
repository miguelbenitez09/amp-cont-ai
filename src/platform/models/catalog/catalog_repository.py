"""
Catalog & Registry Repository — amp-cont-ai
Data access layer for model registry, versions, deployments and access rules in SQLite.
Author: Desarrollado v1.0.0 Miguel Benítez - GNU GPL-3.0
"""

import sqlite3
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from .catalog_normalizer import NormalizedModel, CatalogNormalizer


class CatalogRepository:
    """Provides structured persistence methods for MLOps platform entities."""

    def __init__(self, db_path: str = "data/enterprise_db/portops_platform.db"):
        self.db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def list_registry_models(self) -> List[Dict[str, Any]]:
        """Queries model_registry with version and alias information."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT mr.*, 
                   COALESCE(ma.alias_name, '') AS active_alias,
                   COALESCE(mv.lifecycle_state, mr.status) AS current_lifecycle
            FROM model_registry mr
            LEFT JOIN model_aliases ma ON mr.model_id = ma.model_id
            LEFT JOIN model_versions mv ON mr.model_id = mv.model_id
            ORDER BY mr.created_at DESC
        """)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def register_new_model(
        self,
        model_name: str,
        version: str,
        algorithm: str,
        family: str,
        model_type: str,
        created_by: str,
        metrics: Optional[Dict[str, float]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        access_policy: str = "PUBLIC"
    ) -> str:
        """Inserts a new model entry and initial version into SQLite."""
        conn = self._get_conn()
        cursor = conn.cursor()
        model_id = f"model-{str(uuid.uuid4())[:8]}"
        version_id = f"ver-{str(uuid.uuid4())[:8]}"
        now_str = datetime.now(timezone.utc).isoformat()
        metrics = metrics or {}
        params = parameters or {}

        cursor.execute("""
            INSERT INTO model_registry (
                model_id, model_name, version_tag, algorithm, dataset_hash,
                parameters_json, wape_score, mae_score, rmse_score, r2_score,
                pinball_loss, status, is_champion, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'TRAINED', 0, ?, ?, ?)
        """, (
            model_id, model_name, version, algorithm, "manual-reg-hash",
            json.dumps(params), metrics.get("wape"), metrics.get("mae"),
            metrics.get("rmse"), metrics.get("r2"), metrics.get("pinball_loss"),
            created_by, now_str, now_str
        ))

        cursor.execute("""
            INSERT INTO model_versions (
                version_id, model_id, version_tag, revision, artifact_hash,
                parameters_json, lifecycle_state, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, 'rev-1', 'pending-hash', ?, 'TRAINED', ?, ?, ?)
        """, (
            version_id, model_id, version, json.dumps(params), created_by, now_str, now_str
        ))

        cursor.execute("""
            INSERT INTO model_access_rules (
                rule_id, model_id, access_policy, allowed_roles_json, allowed_depts_json,
                require_mfa, max_context_tokens, rate_limit_rpm, created_at
            ) VALUES (?, ?, ?, '["*"]', '["*"]', 0, 2048, 60, ?)
        """, (
            str(uuid.uuid4()), model_id, access_policy, now_str
        ))

        conn.commit()
        conn.close()
        return model_id

    def list_deployments(self) -> List[Dict[str, Any]]:
        """Queries model_deployments with runtime details."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT md.*, mr.model_name, ri.runtime_type, ri.endpoint
            FROM model_deployments md
            JOIN model_registry mr ON md.model_id = mr.model_id
            LEFT JOIN runtime_instances ri ON md.runtime_id = ri.runtime_id
            ORDER BY md.deployed_at DESC
        """)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def record_deployment(
        self,
        model_id: str,
        version_id: str,
        runtime_id: str,
        serving_name: str,
        deployed_by: str,
        port: int = 8000,
        checklist: Optional[Dict[str, Any]] = None
    ) -> str:
        """Records a verified deployment instance in the database."""
        conn = self._get_conn()
        cursor = conn.cursor()
        dep_id = f"dep-{str(uuid.uuid4())[:8]}"
        now_str = datetime.now(timezone.utc).isoformat()
        checklist_json = json.dumps(checklist or {})

        cursor.execute("""
            INSERT INTO model_deployments (
                deployment_id, model_id, version_id, runtime_id, serving_name,
                port, replicas, status, verification_checklist_json, deployed_by,
                deployed_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 1, 'HEALTHY', ?, ?, ?, ?)
        """, (
            dep_id, model_id, version_id, runtime_id, serving_name,
            port, checklist_json, deployed_by, now_str, now_str
        ))
        conn.commit()
        conn.close()
        return dep_id
