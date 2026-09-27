"""
Canonical Model Schema Normalizer — amp-cont-ai
Enforces consistent data structures across Model Registry, Runtime Catalog, and Benchmark Catalog.
Author: Desarrollado v1.0.0 Miguel Benítez - GNU GPL-3.0
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class NormalizedModel(BaseModel):
    model_id: str
    name: str
    version: str = "1.0.0"
    revision: Optional[str] = None
    family: str = "general"
    type: str = "tabular_regression"  # 'tabular_regression', 'llm', 'vlm', 'embedding', 'reranker'
    task: str = "time_series_forecasting"
    runtime: str = "local_tabular"
    runtime_endpoint: Optional[str] = None
    status: str = "READY"  # 'CONFIGURED', 'READY', 'HEALTHY', 'SERVING', 'DEGRADED', 'FAILED', 'NOT_LOADED'
    access_policy: str = "PUBLIC"
    is_champion: bool = False
    alias: Optional[str] = None
    context_length: Optional[int] = None
    quantization: Optional[str] = None
    parameters_count: Optional[str] = None
    artifact_hash: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)
    hardware_requirements: Dict[str, Any] = Field(default_factory=dict)
    source: str = "local_registry"
    capabilities: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class CatalogNormalizer:
    """Normalizes raw model metadata from different sources into Canonical NormalizedModel."""

    @staticmethod
    def normalize_dict(data: Dict[str, Any], default_source: str = "local_registry") -> NormalizedModel:
        model_id = str(data.get("id") or data.get("model_id") or data.get("model_name") or "unknown-model")
        name = str(data.get("name") or data.get("model_name") or model_id)
        version = str(data.get("version") or data.get("version_tag") or "1.0.0")
        
        # Family detection
        family = data.get("family")
        if not family:
            algo = str(data.get("algorithm", "")).lower()
            if "lightgbm" in algo or "lgbm" in algo:
                family = "gradient_boosting"
            elif "xgboost" in algo or "xgb" in algo:
                family = "gradient_boosting"
            elif "forest" in algo or "tree" in algo:
                family = "ensemble_trees"
            elif "gemma" in model_id.lower():
                family = "gemma"
            elif "llama" in model_id.lower():
                family = "llama"
            elif "bge" in model_id.lower() or "bert" in model_id.lower():
                family = "bert"
            else:
                family = "statistical"

        # Type detection
        m_type = data.get("type")
        if not m_type:
            if family in ("gemma", "llama", "mistral", "qwen"):
                m_type = "llm"
            elif family in ("bert", "embedding"):
                m_type = "embedding"
            else:
                m_type = "tabular_regression"

        # Runtime normalization
        runtime = data.get("runtime") or data.get("runtime_target") or "local_tabular"

        # Metrics extraction
        raw_metrics = data.get("metrics") or {}
        if not raw_metrics:
            for k in ("wape", "wape_score", "r2", "r2_score", "mae", "mae_score", "rmse", "rmse_score"):
                if k in data and data[k] is not None:
                    raw_metrics[k.replace("_score", "")] = float(data[k])

        return NormalizedModel(
            model_id=model_id,
            name=name,
            version=version,
            revision=data.get("revision"),
            family=family,
            type=m_type,
            task=data.get("task", "general_inference"),
            runtime=runtime,
            runtime_endpoint=data.get("runtime_endpoint"),
            status=data.get("status", "READY"),
            access_policy=data.get("access_policy", "PUBLIC"),
            is_champion=bool(data.get("is_champion", False)),
            alias=data.get("alias"),
            context_length=data.get("context_length"),
            quantization=data.get("quantization"),
            parameters_count=data.get("parameters_count"),
            artifact_hash=data.get("artifact_hash"),
            metrics=raw_metrics,
            hardware_requirements=data.get("hardware_requirements", {}),
            source=data.get("source", default_source),
            capabilities=data.get("capabilities", []),
            description=data.get("description")
        )
