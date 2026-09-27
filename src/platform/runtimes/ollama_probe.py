"""
Ollama Runtime Probe — amp-cont-ai
Probes local Ollama instance on port 11434 and discovers local models.
Author: Desarrollado v1.0.0 Miguel Benítez - GNU GPL-3.0
"""

import time
import urllib.request
import json
from typing import Dict, Any, List
from .runtime_probe import BaseRuntimeProbe


class OllamaProbe(BaseRuntimeProbe):
    """Probes Ollama REST API."""

    def __init__(self, endpoint: str = "http://127.0.0.1:11434", timeout: float = 1.5):
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout

    def probe(self) -> Dict[str, Any]:
        t0 = time.perf_counter()
        try:
            req = urllib.request.Request(f"{self.endpoint}/api/version", headers={"User-Agent": "amp-cont-ai-probe/1.0"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                ver_data = json.loads(resp.read().decode("utf-8"))
                version = ver_data.get("version", "unknown")
                latency = round((time.perf_counter() - t0) * 1000, 2)
                
                # Fetch tags/models
                models = self.list_served_models()
                return {
                    "runtime": "ollama",
                    "reachable": True,
                    "version": version,
                    "endpoint": self.endpoint,
                    "status": "SERVING" if models else "HEALTHY",
                    "latency_ms": latency,
                    "discovered_models": models
                }
        except Exception as e:
            return {
                "runtime": "ollama",
                "reachable": False,
                "endpoint": self.endpoint,
                "status": "NOT_LOADED",
                "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
                "error": str(e)
            }

    def list_served_models(self) -> List[str]:
        try:
            req = urllib.request.Request(f"{self.endpoint}/api/tags", headers={"User-Agent": "amp-cont-ai-probe/1.0"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                tags_data = json.loads(resp.read().decode("utf-8"))
                return [m.get("name") for m in tags_data.get("models", [])]
        except Exception:
            return []
