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

def test_api_models_compare_eight_algorithms(client):
    """Verifies that /api/models/compare returns all 8 benchmarked machine learning models."""
    response = client.get("/api/models/compare")
    assert response.status_code == 200
    data = response.json()
    comparison = data["benchmark_comparison"]
    expected_models = [
        "lightgbm", "random_forest", "gradient_boosting", "ridge_elasticnet",
        "extra_trees", "catboost_gbdt", "bayesian_ridge", "neural_mlp_quantile"
    ]
    for model_key in expected_models:
        assert model_key in comparison, f"Model {model_key} missing from benchmark comparison"
        entry = comparison[model_key]
        assert "avg_wape" in entry or "wape" in entry
        assert "avg_mae" in entry or "mae" in entry
        assert "avg_rmse" in entry or "rmse" in entry
        assert "avg_r2" in entry or "r2" in entry
        assert "avg_latency_ms" in entry or "latency_ms" in entry

def test_api_diagnostics_detail_endpoints(client):
    """Verifies detailed diagnostic modal endpoints for residuals, features, and correlations."""
    # 1. Residual detail
    resp_res = client.get("/api/diagnostics/residual-detail/mean_residual")
    assert resp_res.status_code == 200
    res_data = resp_res.json()
    assert res_data["metric_key"] == "mean_residual"
    detail = res_data["detail"]
    assert "formula_latex" in detail
    assert "mathematical_deduction" in detail
    assert "operational_impact" in detail

    # 2. Feature detail
    resp_feat = client.get("/api/diagnostics/feature-detail/teu_lag1")
    assert resp_feat.status_code == 200
    feat_data = resp_feat.json()
    assert feat_data["feature_name"] == "teu_lag1"
    feat_detail = feat_data["detail"]
    assert "formula_latex" in feat_detail
    assert "domain_rationale" in feat_detail
    assert "split_gain_pct" in feat_detail

    # 3. Correlation detail
    resp_corr = client.get("/api/diagnostics/correlation-detail/teu_total/teu_lag1")
    assert resp_corr.status_code == 200
    corr_data = resp_corr.json()
    assert corr_data["feature1"] == "teu_total"
    corr_detail = corr_data["detail"]
    assert "pearson_r" in corr_detail
    assert "vif_impact" in corr_detail
    assert "tree_invariance_rationale" in corr_detail

def test_api_simulation_run_and_worm_audit(client):
    """Verifies simulation execution, WORM ledger logging, history retrieval, and quotas."""
    sim_payload = {
        "port": "Puerto Balboa",
        "scenario": "us_recession",
        "n_paths": 1000,
        "horizon_months": 6,
        "user": "operador_terminal_balboa"
    }
    resp_run = client.post("/api/simulation/run", json=sim_payload)
    assert resp_run.status_code == 200
    run_data = resp_run.json()
    assert run_data["status"] == "success"
    assert "metrics" in run_data
    assert "audit_block" in run_data
    assert run_data["audit_block"]["block_hash"].startswith("0x") or len(run_data["audit_block"]["block_hash"]) == 64
    assert run_data["audit_block"]["tamper_evident"] is True

    # Check history
    resp_hist = client.get("/api/simulation/history?limit=10")
    assert resp_hist.status_code == 200
    hist_data = resp_hist.json()
    assert "history" in hist_data
    assert len(hist_data["history"]) >= 1
    latest_run = hist_data["history"][0]
    assert latest_run["user_id"] == "operador_terminal_balboa"
    assert latest_run["port"] == "Puerto Balboa"

    # Check quotas
    resp_quotas = client.get("/api/simulation/quotas")
    assert resp_quotas.status_code == 200
    quotas_data = resp_quotas.json()
    assert "quotas" in quotas_data
    quota_usernames = [q["username"] for q in quotas_data["quotas"]]
    assert "root" in quota_usernames
    assert "admin_amp" in quota_usernames

def test_postgres_audit_manager_worm_tamper_evident():
    """Direct verification of PostgresAuditManager WORM chain integrity and resource tracking."""
    from src.infrastructure.db.postgres_audit import get_audit_manager
    mgr = get_audit_manager()
    record = mgr.log_simulation_run(
        user_id="test_auditor_amp",
        port="Manzanillo International Terminal (MIT)",
        scenario="geopolitical_red_sea",
        n_paths=1000,
        horizon_months=6,
        expected_volume=215000.0,
        var_95=168000.0,
        cvar_95=152000.0,
        severe_drop_prob=0.125,
        execution_latency_ms=45.2,
        vcpu_used=2.0,
        gpu_used=0.0
    )
    assert record["block_number"] >= 1
    assert "block_hash" in record
    assert "prev_block_hash" in record

    # Verify WORM chain
    chain_status = mgr.verify_worm_chain()
    assert chain_status["valid"] is True
    assert chain_status["tampering_detected"] is False
    assert chain_status["verified_blocks"] >= 1

