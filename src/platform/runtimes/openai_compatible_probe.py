"""
OpenAI-Compatible Runtime Probe — amp-cont-ai
Probes generic OpenAI-compatible API endpoints (/v1/models).
Author: Desarrollado v1.0.0 Miguel Benítez - GNU GPL-3.0
"""

import time
import urllib.request
import json
from typing import Dict, Any, List, Optional
from .runtime_probe import BaseRuntimeProbe


class OpenAICompatibleProbe(BaseRuntimeProbe):
    """Probes generic OpenAI-compatible endpoints."""

    def __init__(self, endpoint: str = "http://127.0.0.1:8001/v1", api_key: Optional[str] = None, timeout: float = 1.5):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def probe(self) -> Dict[str, Any]:
        t0 = time.perf_counter()
        headers = {"User-Agent": "amp-cont-ai-probe/1.0"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            req = urllib.request.Request(f"{self.endpoint}/models", headers=headers)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("id") for m in data.get("data", [])]
                latency = round((time.perf_counter() - t0) * 1000, 2)
                return {
                    "runtime": "openai_compatible",
                    "reachable": True,
                    "endpoint": self.endpoint,
                    "status": "SERVING" if models else "HEALTHY",
                    "latency_ms": latency,
                    "discovered_models": models
                }
        except Exception as e:
            return {
                "runtime": "openai_compatible",
                "reachable": False,
                "endpoint": self.endpoint,
                "status": "NOT_LOADED",
                "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
                "error": str(e)
            }

    def list_served_models(self) -> List[str]:
        res = self.probe()
        return res.get("discovered_models", [])
