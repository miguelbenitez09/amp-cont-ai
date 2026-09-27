"""
vLLM Runtime Catalog Source & Probe — amp-cont-ai
Discovers models actually served by vLLM instance and probes runtime health.
Author: Desarrollado v1.0.0 Miguel Benítez - GNU GPL-3.0
"""

import time
import urllib.request
import json
from typing import List, Dict, Any, Optional
from ..catalog_normalizer import NormalizedModel, CatalogNormalizer


class VllmCatalogSource:
    """Probes vLLM server to discover models physically loaded and serving."""

    def __init__(self, endpoint: str = "http://127.0.0.1:8001/v1", health_endpoint: str = "http://127.0.0.1:8001/health", timeout: float = 2.0):
        self.endpoint = endpoint.rstrip("/")
        self.health_endpoint = health_endpoint
        self.timeout = timeout

    def probe_runtime(self) -> Dict[str, Any]:
        """Probes the vLLM runtime and returns live status."""
        start_t = time.perf_counter()
        try:
            req = urllib.request.Request(self.health_endpoint, headers={"User-Agent": "amp-cont-ai-probe/1.0"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                status_code = resp.status
                latency = round((time.perf_counter() - start_t) * 1000, 2)
                is_healthy = status_code == 200
                return {
                    "reachable": True,
                    "status_code": status_code,
                    "latency_ms": latency,
                    "status": "HEALTHY" if is_healthy else "DEGRADED"
                }
        except Exception as e:
            return {
                "reachable": False,
                "error": str(e),
                "latency_ms": round((time.perf_counter() - start_t) * 1000, 2),
                "status": "NOT_LOADED"
            }

    def discover_models(self) -> List[NormalizedModel]:
        """Queries /v1/models and returns normalized model instances."""
        probe = self.probe_runtime()
        if not probe["reachable"]:
            return []

        models_url = f"{self.endpoint}/models"
        try:
            req = urllib.request.Request(models_url, headers={"User-Agent": "amp-cont-ai-probe/1.0"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models_list = data.get("data", [])
                
                normalized = []
                for item in models_list:
                    m_id = item.get("id", "vllm-model")
                    normalized.append(CatalogNormalizer.normalize_dict({
                        "model_id": m_id,
                        "name": f"vLLM Served: {m_id}",
                        "family": "vllm_llm",
                        "type": "llm",
                        "task": "text_generation",
                        "runtime": "vllm",
                        "runtime_endpoint": self.endpoint,
                        "status": "SERVING",
                        "source": "vllm_probe",
                        "access_policy": "AUTHENTICATED",
                        "capabilities": ["streaming", "chat_completions", "tool_calling"]
                    }))
                return normalized
        except Exception:
            return []
