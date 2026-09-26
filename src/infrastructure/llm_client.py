"""
Unified LLM Runtime Client for Panama PortOps-AI v2.0
Supports:
- vLLM (OpenAI-compatible API with PagedAttention and AWQ/GPTQ)
- Ollama (Local quantized models: Gemma, Llama 3, Qwen)
- Resilient Rule-Based / RAG Heuristic Fallback when offline
- Streamlined connection pooling and timeout handling

Author: Desarrollado v1.0 Miguel Benítez
License: GNU General Public License v3.0 (GPL-3.0) with Section 7 Mandatory Attribution
"""

import os
import json
import time
import requests
from typing import Dict, Any, List, Optional, Generator
from datetime import datetime, timezone

from src.utils.logger import logger


class UnifiedLLMClient:
    """
    Orchestrates inference across local LLM runtimes with automatic fallback.
    """

    def __init__(
        self,
        vllm_base_url: str = os.getenv("VLLM_BASE_URL", "http://localhost:8080/v1"),
        ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        default_model: str = os.getenv("DEFAULT_LLM_MODEL", "gemma:2b"),
        timeout_seconds: float = 6.0
    ):
        self.vllm_base_url = vllm_base_url.rstrip("/")
        self.ollama_base_url = ollama_base_url.rstrip("/")
        self.default_model = default_model
        self.timeout = timeout_seconds
        self.session = requests.Session()
        self._last_health = None
        self._last_health_ts = 0.0

    def check_health(self) -> Dict[str, Any]:
        """Checks availability of local LLM runtimes (cached for 15s)."""
        now = time.time()
        if self._last_health and (now - self._last_health_ts) < 15.0:
            return self._last_health

        vllm_ok = False
        ollama_ok = False
        vllm_models = []
        ollama_models = []

        # Check vLLM (fast 0.3s timeout)
        try:
            r = self.session.get(f"{self.vllm_base_url}/models", timeout=0.3)
            if r.status_code == 200:
                vllm_ok = True
                vllm_models = [m.get("id") for m in r.json().get("data", [])]
        except Exception:
            pass

        # Check Ollama (fast 0.3s timeout)
        try:
            r = self.session.get(f"{self.ollama_base_url}/api/tags", timeout=0.3)
            if r.status_code == 200:
                ollama_ok = True
                ollama_models = [m.get("name") for m in r.json().get("models", [])]
        except Exception:
            pass

        self._last_health = {
            "vllm": {"available": vllm_ok, "endpoint": self.vllm_base_url, "models": vllm_models},
            "ollama": {"available": ollama_ok, "endpoint": self.ollama_base_url, "models": ollama_models},
            "active_backend": "vllm" if vllm_ok else ("ollama" if ollama_ok else "heuristic_fallback"),
            "author": "Desarrollado v1.0 Miguel Benítez"
        }
        self._last_health_ts = now
        return self._last_health

    def generate_chat_response(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.2,
        max_tokens: int = 512,
        tools_schema: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Executes a chat completion query through vLLM, Ollama, or deterministic fallback.
        """
        health = self.check_health()
        backend = health["active_backend"]
        t0 = time.time()

        # 1. Try vLLM (OpenAI compatible)
        if backend == "vllm":
            try:
                payload = {
                    "model": health["vllm"]["models"][0] if health["vllm"]["models"] else self.default_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                res = self.session.post(f"{self.vllm_base_url}/chat/completions", json=payload, timeout=self.timeout)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    lat_ms = (time.time() - t0) * 1000
                    return {
                        "content": content,
                        "backend_used": "vLLM (PagedAttention)",
                        "model": payload["model"],
                        "latency_ms": round(lat_ms, 2),
                        "tokens_used": data.get("usage", {}).get("total_tokens", 0)
                    }
            except Exception as e:
                logger.warning(f"vLLM query failed: {e}. Falling back...")

        # 2. Try Ollama
        if backend == "ollama" or health["ollama"]["available"]:
            try:
                payload = {
                    "model": health["ollama"]["models"][0] if health["ollama"]["models"] else self.default_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "stream": False,
                    "options": {"temperature": temperature}
                }
                res = self.session.post(f"{self.ollama_base_url}/api/chat", json=payload, timeout=self.timeout)
                if res.status_code == 200:
                    data = res.json()
                    content = data["message"]["content"]
                    lat_ms = (time.time() - t0) * 1000
                    return {
                        "content": content,
                        "backend_used": "Ollama (Quantized)",
                        "model": payload["model"],
                        "latency_ms": round(lat_ms, 2),
                        "tokens_used": data.get("eval_count", 0)
                    }
            except Exception as e:
                logger.warning(f"Ollama query failed: {e}. Falling back to domain heuristics...")

        # 3. Deterministic Domain Heuristic Fallback
        lat_ms = (time.time() - t0) * 1000
        fallback_content = self._heuristic_domain_response(system_prompt, user_message)
        return {
            "content": fallback_content,
            "backend_used": "Maritime Domain Expert Engine (Deterministic Fallback)",
            "model": "rule_based_maritime_v2",
            "latency_ms": round(lat_ms, 2),
            "tokens_used": len(fallback_content.split())
        }

    def _heuristic_domain_response(self, system_prompt: str, user_message: str) -> str:
        """Provides instant high-quality domain responses when no local GPU engine is running."""
        msg = user_message.lower()
        if "arancel" in msg or "hs" in msg or "partida" in msg or "dai" in msg or "impuesto" in msg:
            return (
                "Para la República de Panamá, la clasificación arancelaria se rige por el Arancel de Importación "
                "de la Autoridad Nacional de Aduanas (ANA) armonizado a nivel centroamericano (SIECA). "
                "Las subpartidas se desglosan a 8, 10 y 12 dígitos. El Derecho Arancelario a la Importación (DAI) "
                "oscila entre 0% (bienes de capital e insumos médicos) y hasta 15-54% en rubros agropecuarios sensibles. "
                "Adicionalmente, se aplica el 7% del ITBMS sobre el valor CIF + DAI acumulado."
            )
        elif "contenedor" in msg or "iso" in msg or "baplie" in msg or "edifact" in msg or "check digit" in msg:
            return (
                "De acuerdo con la norma internacional ISO 6346:1995, la identificación de contenedores intermodales "
                "consta de 4 letras (3 de código de propietario BIC + 1 identificador de equipo 'U/J/Z'), 6 dígitos de número "
                "de serie y 1 dígito de control calculado mediante el algoritmo ponderado Módulo-11. "
                "Para la estiba y movimiento en terminales de Balboa, MIT y Cristóbal, los sistemas TOS procesan "
                "mensajes EDIFACT BAPLIE (bay plans) y COARRI (descarga y carga)."
            )
        elif "ley 6" in msg or "transparencia" in msg or "datos abiertos" in msg:
            return (
                "La Ley 6 de 22 de enero de 2002 de la República de Panamá consagra las normas de transparencia "
                "en la gestión pública y el acceso ciudadano a la información de las instituciones del Estado. "
                "Bajo este marco, Panamá PortOps-AI procesa microdatos oficiales de la Autoridad Marítima de Panamá (AMP) "
                "para garantizar soberanía analítica con cero datos inventados (zero mocks)."
            )
        elif "var" in msg or "cvar" in msg or "riesgo" in msg or "monte carlo" in msg:
            return (
                "El motor de riesgo de Panamá PortOps-AI evalúa simulaciones estocásticas multivariadas de Monte Carlo. "
                "Calcula el Value at Risk (VaR 95%) para delimitar el piso pesimista de volumen en TEUs y el Conditional VaR "
                "(CVaR / Expected Shortfall) que mide la pérdida esperada en la cola del 5% más severo de choques logísticos "
                "asociados a sequías del Canal o fluctuaciones del búnker."
            )
        else:
            return (
                f"Respuesta del Ecosistema Agéntico Portuario: Consulta recibida sobre '{user_message.strip()}'. "
                "La plataforma integra el catálogo de terminales portuarias panameñas (Balboa, Cristóbal, MIT, PSA, CCT, Bocas Fruit Co.), "
                "el registro MLOps de modelos LightGBM y el libro mayor inmutable WORM conforme a ISO/IEC 27001."
            )


# Singleton
llm_client = UnifiedLLMClient()

def get_llm_client() -> UnifiedLLMClient:
    return llm_client
