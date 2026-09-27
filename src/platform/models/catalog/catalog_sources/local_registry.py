"""
Local Registry Model Catalog Source — amp-cont-ai
Reads verified models from SQLite database and declarative configs/models.yaml.
Author: Desarrollado v1.0.0 Miguel Benítez - GNU GPL-3.0
"""

import os
import json
import sqlite3
import yaml
from typing import List, Dict, Any, Optional
from ..catalog_normalizer import NormalizedModel, CatalogNormalizer


class LocalRegistryCatalogSource:
    """Retrieves models registered within the database and YAML declarative configs."""

    def __init__(self, db_path: str = "data/enterprise_db/portops_platform.db", config_path: str = "configs/models.yaml"):
        self.db_path = db_path
        self.config_path = config_path

    def get_registered_models(self) -> List[NormalizedModel]:
        """Loads models from SQLite registry and merges with declarative defaults."""
        models_by_id: Dict[str, NormalizedModel] = {}

        # 1. Load from declarative config first
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
                    raw_list = cfg.get("models", [])
                    for item in raw_list:
                        norm = CatalogNormalizer.normalize_dict(item, default_source="config_declarative")
                        models_by_id[norm.model_id] = norm
            except Exception:
                pass

        # 2. Query SQLite DB model_registry
        if os.path.exists(self.db_path):
            try:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT model_id, model_name, version_tag, algorithm, dataset_hash,
                           parameters_json, wape_score, mae_score, rmse_score, r2_score,
                           pinball_loss, status, is_champion, created_by, created_at
                    FROM model_registry
                """)
                rows = cursor.fetchall()
                for r in rows:
                    m_dict = dict(r)
                    m_id = m_dict.get("model_id")
                    norm = CatalogNormalizer.normalize_dict({
                        "model_id": m_id,
                        "name": m_dict.get("model_name"),
                        "version": m_dict.get("version_tag", "1.0.0"),
                        "algorithm": m_dict.get("algorithm"),
                        "status": m_dict.get("status", "VALIDATED"),
                        "is_champion": bool(m_dict.get("is_champion", False)),
                        "metrics": {
                            "wape": m_dict.get("wape_score"),
                            "mae": m_dict.get("mae_score"),
                            "rmse": m_dict.get("rmse_score"),
                            "r2": m_dict.get("r2_score")
                        },
                        "source": "sqlite_registry"
                    }, default_source="sqlite_registry")
                    models_by_id[m_id] = norm
                conn.close()
            except Exception:
                pass

        return list(models_by_id.values())
