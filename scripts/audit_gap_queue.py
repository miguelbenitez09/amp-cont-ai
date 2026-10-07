"""Detect reproducible project gaps and update the Gold governance queue."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.governance.gap_queue import GapFinding, GapQueue


def command_lines(command: list[str]) -> list[str]:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=8, check=False)
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except (OSError, subprocess.SubprocessError):
        return []


def detect() -> list[GapFinding]:
    findings: list[GapFinding] = []
    vllm_enabled = os.getenv("VLLM_ENABLED", "false").lower() == "true"
    vllm_api_key = os.getenv("VLLM_API_KEY")
    try:
        headers = {"Authorization": f"Bearer {vllm_api_key}"} if vllm_api_key else {}
        response = requests.get("http://127.0.0.1:8080/v1/models", headers=headers, timeout=0.7)
        models = response.json().get("data", []) if response.status_code == 200 else []
    except requests.RequestException:
        models = []

    docker_version = command_lines(["docker", "version", "--format", "{{.Server.Version}}"])
    docker_runtimes = command_lines(["docker", "info", "--format", "{{json .Runtimes}}"])
    vllm_images = command_lines(["docker", "images", "vllm/vllm-openai", "--format", "{{.Repository}}:{{.Tag}}"])
    vllm_configured = vllm_enabled or bool(vllm_api_key) or bool(vllm_images)
    if vllm_configured and not models:
        findings.append(GapFinding(
            "RUNTIME-VLLM-NO-MODEL", "vLLM no sirve un modelo verificable", "runtime", "high",
            {"endpoint": "http://127.0.0.1:8080/v1/models", "model_count": 0,
             "docker_server": docker_version[0] if docker_version else "UNAVAILABLE",
             "enabled": vllm_enabled,
             "nvidia_runtime": any("nvidia" in item.lower() for item in docker_runtimes),
             "vllm_images": vllm_images}, "MlopsAdmin",
            "Desplegar un modelo compatible y aprobar los 15 controles con evidencia viva.",
        ))

    docker_models = command_lines(["docker", "volume", "ls", "--format", "{{.Name}}"])
    inventory = ROOT / "data" / "metadata" / "model_inventory.json"
    has_registered_weights = inventory.exists() and '"artifacts"' in inventory.read_text(encoding="utf-8")
    if not docker_models and not has_registered_weights:
        findings.append(GapFinding(
            "MODEL-DOCKER-VOLUME-ABSENT", "Docker no contiene volúmenes de modelos", "model_inventory", "info",
            {"docker_volumes": []}, "MlopsAdmin", "Registrar los pesos y su SHA-256 antes de habilitar vLLM.",
        ))

    try:
        tags = requests.get("http://127.0.0.1:11434/api/tags", timeout=0.7).json().get("models", [])
    except (requests.RequestException, ValueError):
        tags = []
    ollama_enabled = os.getenv("OLLAMA_ENABLED", "false").lower() == "true"
    if ollama_enabled and not tags:
        findings.append(GapFinding(
            "RUNTIME-OLLAMA-NO-MODEL", "Ollama no tiene modelos instalados", "runtime", "medium",
            {"endpoint": "http://127.0.0.1:11434/api/tags", "model_count": 0, "enabled": ollama_enabled}, "MlopsAdmin",
            "Instalar y evaluar un modelo local apto para el hardware.",
        ))

    external = ROOT / "src" / "data" / "connectors" / "external_sources.py"
    random_hits = []
    for path in (external,):
        if path.exists() and "np.random" in path.read_text(encoding="utf-8"):
            random_hits.append(str(path.relative_to(ROOT)))
    if random_hits:
        findings.append(GapFinding(
            "DATA-SYNTHETIC-PROVENANCE", "Generación aleatoria presente en conectores de datos", "data_provenance", "critical",
            {"files": random_hits}, "DataSteward",
            "Etiquetar datos sintéticos y bloquear su mezcla con observaciones en entrenamiento y publicación.",
        ))
    # An intentionally disabled integration is a supported state: the adapter
    # contract and authenticated endpoints remain available without secrets.
    # Only a partially configured or explicitly enabled-but-unreachable manager
    # is an operational gap.
    wazuh_values = [os.getenv(key, "") for key in ("WAZUH_API_URL", "WAZUH_API_USERNAME", "WAZUH_API_PASSWORD")]
    wazuh_enabled = os.getenv("WAZUH_ENABLED", "false").lower() == "true"
    if wazuh_enabled and not all(wazuh_values):
        findings.append(GapFinding(
            "SECURITY-WAZUH-UNCONFIGURED", "Integración Wazuh sin configurar", "security_integration", "medium",
            {"required_environment": ["WAZUH_API_URL", "WAZUH_API_USERNAME", "WAZUH_API_PASSWORD"]}, "SecurityAdmin",
            "Configurar credenciales en el almacén de secretos y verificar /manager/status con JWT.",
        ))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "gold" / "governance" / "gap_queue.json")
    args = parser.parse_args()
    payload = GapQueue(args.output).upsert(detect())
    summary = {"output": str(args.output), "total": len(payload["items"]), "open": sum(i["status"] == "open" for i in payload["items"])}
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
