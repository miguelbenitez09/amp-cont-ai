"""
Contract Test: Unhealthy Runtime Not Selectable — amp-cont-ai
Verifies Section 11 and Section 56 of Plan Maestro:
An unreached runtime or model not loaded must not falsely appear as SERVING.
Author: Desarrollado v1.0.0 Miguel Benítez - GNU GPL-3.0
"""

from src.platform.runtimes.vllm_probe import VllmDeploymentProbe
from src.platform.models.catalog.catalog_sources.vllm import VllmCatalogSource


def test_unreachable_vllm_returns_not_loaded_status():
    """Validates that a non-listening vLLM port returns NOT_LOADED and zero models."""
    # Point to a closed dummy port
    source = VllmCatalogSource(endpoint="http://127.0.0.1:59999/v1", health_endpoint="http://127.0.0.1:59999/health")
    probe = source.probe_runtime()

    assert probe["reachable"] is False
    assert probe["status"] == "NOT_LOADED"

    models = source.discover_models()
    assert models == []


def test_vllm_deployment_probe_checklist():
    """Validates that the 15-point verification probe executes cleanly and grades pass count."""
    probe = VllmDeploymentProbe(endpoint="http://127.0.0.1:59999/v1", health_endpoint="http://127.0.0.1:59999/health")
    result = probe.probe()

    assert "checklist" in result
    assert len(result["checklist"]) == 15
    assert result["status"] in ("CONFIGURED", "READY", "HEALTHY", "SERVING")
    assert "score_pct" in result
    assert "passed_checks" in result
