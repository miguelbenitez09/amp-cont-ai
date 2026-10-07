"""
vLLM Deployment Verification Probe — amp-cont-ai
Executes the comprehensive 15-point deployment verification checklist.
Author: Desarrollado v1.0.0 Miguel Benítez - GNU GPL-3.0
"""

import time
import subprocess
import urllib.request
import json
import os
from typing import Dict, Any, List, Optional
from .runtime_probe import BaseRuntimeProbe


class VllmDeploymentProbe(BaseRuntimeProbe):
    """Probes vLLM runtime and performs 15-point verification."""

    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:8080/v1",
        health_endpoint: str = "http://127.0.0.1:8080/health",
        expected_model: Optional[str] = None
    ):
        self.endpoint = endpoint.rstrip("/")
        self.health_endpoint = health_endpoint
        self.expected_model = expected_model

    def probe(self) -> Dict[str, Any]:
        """Runs the 15-point verification check."""
        checklist: Dict[str, Any] = {}
        t0 = time.perf_counter()
        auth_headers = {"Authorization": f"Bearer {os.environ['VLLM_API_KEY']}"} if os.environ.get("VLLM_API_KEY") else {}

        # Check 1: GPU detectable
        gpu_detected = False
        gpu_name = "N/A"
        try:
            res = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], capture_output=True, text=True, timeout=2)
            if res.returncode == 0 and res.stdout.strip():
                gpu_detected = True
                gpu_name = res.stdout.strip()
        except Exception:
            pass
        checklist["check_1_gpu_detectable"] = {"passed": gpu_detected, "detail": gpu_name}

        # Check 2: CUDA functional
        cuda_ok = False
        try:
            import torch
            cuda_ok = torch.cuda.is_available()
            cuda_ver = torch.version.cuda if cuda_ok else "N/A"
        except Exception:
            cuda_ver = "Torch not installed or CPU-only"
        checklist["check_2_cuda_functional"] = {"passed": cuda_ok, "detail": cuda_ver}

        # Check 3: Docker GPU runtime functional
        docker_gpu = False
        try:
            res = subprocess.run(["docker", "info", "--format", "{{json .Runtimes}}"], capture_output=True, text=True, timeout=2)
            docker_gpu = res.returncode == 0 and "nvidia" in res.stdout.lower()
        except Exception:
            pass
        checklist["check_3_docker_gpu_runtime"] = {"passed": docker_gpu, "detail": "Docker engine active" if docker_gpu else "Docker unavailable"}

        # Check 4: vLLM image pullable / available
        image_available = False
        try:
            image_res = subprocess.run(["docker", "images", "vllm/vllm-openai", "--format", "{{.ID}}"], capture_output=True, text=True, timeout=2)
            image_available = image_res.returncode == 0 and bool(image_res.stdout.strip())
        except Exception:
            pass
        checklist["check_4_vllm_image"] = {"passed": image_available, "detail": "Local vLLM image present" if image_available else "No local vLLM image"}

        # Check 5: Model downloadable
        model_path = os.environ.get("MODEL_WEIGHTS_PATH", "")
        model_available = bool(model_path and os.path.exists(model_path) and any(os.scandir(model_path)))
        checklist["check_5_model_downloadable"] = {"passed": model_available, "detail": f"Local weights: {model_path}" if model_available else "No local vLLM weights verified"}

        # Check 6: Artifact hash valid
        checklist["check_6_artifact_hash"] = {"passed": False, "detail": "No verified model artifact digest recorded"}

        # Check 7: Container started
        # Check 8: Health endpoint valid
        # Check 9: /v1/models returns expected model
        container_started = False
        health_valid = False
        models_found: List[str] = []
        latency_ms = 0.0

        try:
            req = urllib.request.Request(self.health_endpoint, headers={"User-Agent": "amp-cont-ai-probe/1.0"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    container_started = True
                    health_valid = True
        except Exception:
            pass

        if health_valid:
            try:
                m_req = urllib.request.Request(f"{self.endpoint}/models", headers={"User-Agent": "amp-cont-ai-probe/1.0", **auth_headers})
                with urllib.request.urlopen(m_req, timeout=1.5) as resp:
                    m_data = json.loads(resp.read().decode("utf-8"))
                    models_found = [m.get("id") for m in m_data.get("data", [])]
            except Exception:
                pass

        checklist["check_7_container_started"] = {"passed": container_started, "detail": f"{self.health_endpoint} responding" if container_started else f"Container not listening on {self.health_endpoint}"}
        checklist["check_8_health_endpoint"] = {"passed": health_valid, "detail": f"Status 200 at {self.health_endpoint}" if health_valid else "Unhealthy or unreachable"}
        checklist["check_9_models_endpoint"] = {"passed": len(models_found) > 0, "detail": f"Discovered models: {models_found}"}

        # Check 10: Chat completion
        chat_ok = False
        if models_found:
            try:
                body = json.dumps({"model": models_found[0], "messages": [{"role": "user", "content": "Responde únicamente: OK"}], "max_tokens": 4, "temperature": 0}).encode("utf-8")
                c_req = urllib.request.Request(f"{self.endpoint}/chat/completions", data=body, headers={"Content-Type": "application/json", "User-Agent": "amp-cont-ai-probe/1.0", **auth_headers}, method="POST")
                with urllib.request.urlopen(c_req, timeout=5) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
                    chat_ok = resp.status == 200 and bool(payload.get("choices"))
            except Exception:
                pass
        checklist["check_10_chat_completion"] = {"passed": chat_ok, "detail": "Live completion returned choices" if chat_ok else "Live completion not verified"}

        # Check 11: Token streaming
        streaming_ok = False
        streaming_detail = "Live streaming not verified"
        if models_found:
            try:
                stream_body = json.dumps({"model": models_found[0], "messages": [{"role": "user", "content": "OK"}], "max_tokens": 4, "temperature": 0, "stream": True}).encode("utf-8")
                s_req = urllib.request.Request(f"{self.endpoint}/chat/completions", data=stream_body,
                    headers={"Content-Type": "application/json", "Accept": "text/event-stream", "User-Agent": "amp-cont-ai-probe/1.0", **auth_headers}, method="POST")
                with urllib.request.urlopen(s_req, timeout=5) as resp:
                    content_type = resp.headers.get("Content-Type", "")
                    chunks = []
                    while len(chunks) < 8:
                        line = resp.readline()
                        if not line:
                            break
                        decoded = line.decode("utf-8", errors="replace").strip()
                        if decoded.startswith("data:"):
                            chunks.append(decoded)
                        if decoded == "data: [DONE]":
                            break
                    streaming_ok = resp.status == 200 and "text/event-stream" in content_type.lower() and bool(chunks)
                    streaming_detail = f"SSE chunks={len(chunks)} content_type={content_type}" if streaming_ok else "SSE response did not satisfy protocol"
            except Exception as exc:
                streaming_detail = f"Streaming probe failed: {exc}"
        checklist["check_11_token_streaming"] = {"passed": streaming_ok, "detail": streaming_detail}

        # Check 12: Tool calling
        checklist["check_12_tool_calling"] = {"passed": False, "detail": "Tool calling not verified for the served model"}

        # Check 13: Model returned matches registry
        matches_registry = bool(self.expected_model in models_found) if self.expected_model else bool(models_found)
        checklist["check_13_registry_match"] = {"passed": matches_registry, "detail": f"Expected: {self.expected_model}, Found: {models_found}"}

        # Check 14: Authentication policy
        auth_configured = bool(os.environ.get("VLLM_API_KEY"))
        checklist["check_14_auth_policy"] = {"passed": auth_configured, "detail": "API key configured" if auth_configured else "No vLLM API key configured"}

        # Check 15: Telemetry metrics
        checklist["check_15_observability"] = {"passed": False, "detail": "Runtime metrics endpoint not verified"}

        total_latency = round((time.perf_counter() - t0) * 1000, 2)
        passed_count = sum(1 for v in checklist.values() if v["passed"])
        
        # Overall status calculation
        if health_valid and len(models_found) > 0:
            overall_status = "SERVING"
        elif container_started:
            overall_status = "MISCONFIGURED"
        elif gpu_detected:
            overall_status = "CONFIGURED"
        else:
            overall_status = "NOT_LOADED"

        return {
            "runtime": "vllm",
            "endpoint": self.endpoint,
            "status": overall_status,
            "passed_checks": f"{passed_count}/15",
            "score_pct": round((passed_count / 15) * 100, 1),
            "latency_ms": total_latency,
            "gpu": {"detected": gpu_detected, "name": gpu_name},
            "discovered_models": models_found,
            "checklist": checklist
        }

    def list_served_models(self) -> List[str]:
        probe_res = self.probe()
        return probe_res.get("discovered_models", [])
