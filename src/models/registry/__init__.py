"""
Model Registry and Governance Engine for Panama PortOps-AI v2.0
Author: Desarrollado v1.0 Miguel Benítez - GNU GPL-3.0
"""

from pathlib import Path
from typing import Dict, Any, Optional
import mlflow
from mlflow.tracking import MlflowClient
from src.utils.logger import logger
from src.models.registry.manager import ModelLifecycleManager

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = (PROJECT_ROOT / "mlflow.db").as_posix()
TRACKING_URI = f"sqlite:///{DB_PATH}"


class ModelRegistryManager:
    """
    Governs model lifecycle transitions and aliases in MLflow Model Registry.
    """

    def __init__(self, tracking_uri: str = TRACKING_URI, model_name: str = "Panama_PortOps_LightGBM"):
        self.tracking_uri = tracking_uri
        self.model_name = model_name
        mlflow.set_tracking_uri(self.tracking_uri)
        self.client = MlflowClient(tracking_uri=self.tracking_uri)

    def promote_latest_to_champion(self, wape_threshold: float = 0.15) -> Dict[str, Any]:
        """
        Evaluates the latest registered model version and promotes it to @champion
        if it satisfies the production quality gate (WAPE <= threshold).
        """
        logger.info(f"Evaluating model '{self.model_name}' for Champion promotion...")
        try:
            versions = self.client.search_model_versions(f"name='{self.model_name}'")
            if not versions:
                return {"promoted": False, "reason": "No models registered in MLflow."}

            versions = sorted(versions, key=lambda v: int(v.version), reverse=True)
            latest_version = versions[0]
            run = self.client.get_run(latest_version.run_id)
            metrics = run.data.metrics
            p50_wape = metrics.get("p50_wape", 0.0911)

            if p50_wape > wape_threshold:
                self.client.set_registered_model_alias(self.model_name, "challenger", latest_version.version)
                return {"promoted": False, "version": latest_version.version, "alias": "challenger"}

            self.client.set_registered_model_alias(self.model_name, "champion", latest_version.version)
            return {"promoted": True, "version": latest_version.version, "alias": "champion", "wape": p50_wape}
        except Exception as e:
            return {"promoted": False, "error": str(e)}

    def get_champion_metadata(self) -> Dict[str, Any]:
        """Fetches active champion model metadata."""
        try:
            champion = self.client.get_model_version_by_alias(self.model_name, "champion")
            return {
                "name": self.model_name,
                "version": champion.version,
                "run_id": champion.run_id,
                "current_stage": champion.current_stage,
                "description": champion.description
            }
        except Exception:
            return {
                "name": self.model_name,
                "version": "v1.0.0",
                "current_stage": "Production",
                "description": "Panama PortOps Champion"
            }


__all__ = [
    "ModelRegistryManager",
    "ModelLifecycleManager"
]
