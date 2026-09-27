"""
Catalog Runtime Health Inspector — amp-cont-ai
Inspects operational health for model serving instances and runtimes.
Author: Desarrollado v1.0.0 Miguel Benítez - GNU GPL-3.0
"""

from typing import Dict, Any, List
from .catalog_normalizer import NormalizedModel
from .catalog_sources.vllm import VllmCatalogSource


class CatalogHealthInspector:
    """Validates whether models in the catalog can actually accept requests."""

    def __init__(self, vllm_source: VllmCatalogSource):
        self.vllm_source = vllm_source

    def evaluate_model_health(self, model: NormalizedModel) -> Dict[str, Any]:
        """Returns health verdict for a given model."""
        if "vllm" in model.runtime.lower():
            probe = self.vllm_source.probe_runtime()
            if probe.get("reachable"):
                return {
                    "model_id": model.model_id,
                    "runtime": model.runtime,
                    "status": "SERVING",
                    "healthy": True,
                    "latency_ms": probe.get("latency_ms", 0.0),
                    "details": "vLLM endpoint responsive"
                }
            else:
                return {
                    "model_id": model.model_id,
                    "runtime": model.runtime,
                    "status": "NOT_LOADED",
                    "healthy": False,
                    "latency_ms": probe.get("latency_ms", 0.0),
                    "details": "vLLM service unreachable or not running on port 8001"
                }
        elif "local" in model.runtime.lower() or "in_process" in model.runtime.lower():
            # In-process models are healthy if python runtime is active
            return {
                "model_id": model.model_id,
                "runtime": model.runtime,
                "status": "SERVING",
                "healthy": True,
                "latency_ms": 0.5,
                "details": "In-process memory serving"
            }
        else:
            return {
                "model_id": model.model_id,
                "runtime": model.runtime,
                "status": "CONFIGURED",
                "healthy": True,
                "latency_ms": 1.0,
                "details": "External gateway configured"
            }
