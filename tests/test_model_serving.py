"""
Integration & Contract Tests for FastAPI Inference Serving.
Adheres to MLOps Masterclass Section 1.1, 19 & 25 (Pytest API contract testing).
"""

import pytest
from fastapi.testclient import TestClient
from src.serving.api import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client

def test_api_health_endpoint(client):
    """Verifies that the /health endpoint returns 200 OK and model is loaded."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True

def test_api_model_metadata(client):
    """Verifies that /model/metadata exposes Champion version lineage."""
    response = client.get("/model/metadata")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Panama_PortOps_LightGBM"
    assert "version" in data

def test_api_predict_single_port(client):
    """Verifies prediction output structure, quantiles monotonicity, and latency."""
    payload = {
        "port": "Puerto Balboa",
        "horizon_months": 3,
        "what_if_bunkering_shift_pct": 0.0,
        "what_if_transshipment_shift_pct": 0.0
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["port"] == "Puerto Balboa"
    assert len(data["predictions"]) == 3
    assert data["latency_ms"] < 500.0  # Production latency SLA < 500ms
    
    for pred in data["predictions"]:
        p10 = pred["pred_p10_teu"]
        p50 = pred["pred_p50_teu"]
        p90 = pred["pred_p90_teu"]
        assert 0.0 <= p10 <= p50 <= p90, f"Quantile monotonicity violated: P10={p10}, P50={p50}, P90={p90}"
        assert pred["imbalance_status"] in ["NORMAL_BALANCED", "DEFICIT_CONTAINERS", "CRITICAL_SURPLUS_CONTAINERS"]

def test_api_predict_invalid_port(client):
    """Verifies that invalid ports are rejected with 400 Bad Request."""
    payload = {
        "port": "Puerto Fantasma",
        "horizon_months": 1
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 400
    assert "Invalid port" in response.json()["detail"]

def test_api_predict_horizon_bounds(client):
    """Verifies that horizon_months out of bounds [1, 6] triggers 422 Unprocessable Entity."""
    payload = {
        "port": "Puerto Balboa",
        "horizon_months": 12  # Exceeds max 6
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422

def test_api_predict_batch(client):
    """Verifies batch inference across all 6 ports."""
    response = client.post("/predict/batch?horizon_months=2")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total_ports"] == 6
    assert len(data["batch_forecasts"]) == 6

def test_api_models_compare(client):
    """Verifies multi-algorithm benchmark endpoint returns comparison metrics."""
    response = client.get("/api/models/compare")
    assert response.status_code == 200
    data = response.json()
    assert "benchmark_comparison" in data
    assert "lightgbm" in data["benchmark_comparison"]
    assert "random_forest" in data["benchmark_comparison"]

def test_api_models_diagnostics(client):
    """Verifies statistical diagnostics endpoint returns residuals, VIF and confounders."""
    response = client.get("/api/models/diagnostics")
    assert response.status_code == 200
    data = response.json()
    assert "residual_stats" in data
    assert "collinearity" in data
    assert "confounders" in data

def test_api_methodology(client):
    """Verifies methodology endpoint returns scientific data treatment overview."""
    response = client.get("/api/methodology")
    assert response.status_code == 200
    data = response.json()
    assert "data_cleaning" in data
    assert "normalization_standardization" in data
    assert "anonymization_and_privacy" in data
    assert "Miguel Benítez" in data["author"]
