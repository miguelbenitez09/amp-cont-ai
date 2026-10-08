"""
Test suite for Advanced Simulation Engines (EVT Gumbel & Berth Queueing STS Crane)
and Universal WORM HTTP Request Audit Logging.

Desarrollado v1.0.0 Miguel Benítez / Ing. Miguel Antonio Benítez González (UTP) - GNU GPL-3.0
"""

import pytest
from fastapi.testclient import TestClient
from src.serving.api import app
from src.simulation.advanced_simulations import GumbelStressTester, BerthCraneQueueSimulator
from src.infrastructure.db.postgres_audit import audit_manager
from tests.test_workspace_control_plane import control, login


@pytest.fixture
def client():
    return TestClient(app)


def test_gumbel_stress_tester():
    tester = GumbelStressTester(seed=42)
    res = tester.run_gumbel_stress(
        port_name="Puerto Balboa",
        horizon_months=6,
        num_paths=100
    )
    assert res["status"] == "success"
    assert res["model_type"] == "gumbel_extreme_value_theory"
    assert res["expected_volume"] > 0
    assert res["var_95_volume"] <= res["expected_volume"]
    assert len(res["trajectory_profile"]) == 6
    assert "return_period_10yr_shock" in res


def test_berth_crane_queue_simulator():
    sim = BerthCraneQueueSimulator(seed=42)
    res = sim.run_berth_crane_simulation(
        port_name="Puerto Balboa",
        horizon_months=6,
        num_paths=100
    )
    assert res["status"] == "success"
    assert res["model_type"] == "berth_crane_queue_agent"
    assert res["berths_allocated"] > 0
    assert res["sts_cranes_operational"] > 0
    assert res["mean_berth_occupancy_pct"] > 0
    assert res["mean_vessel_turnaround_hrs"] > 0


def test_simulate_endpoint_gumbel(client):
    payload = {
        "port": "Puerto Balboa",
        "horizon_months": 3,
        "num_paths": 100,
        "scenario_type": "gumbel_extreme_shock",
        "user": "operador_puerto"
    }
    response = client.post("/api/simulation/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["scenario"] == "gumbel_extreme_shock"
    assert "audit_block" in data
    assert data["audit_block"]["tamper_evident"] is True


def test_simulate_endpoint_berth_queue(client):
    payload = {
        "port": "SSA Marine MIT",
        "horizon_months": 3,
        "num_paths": 100,
        "scenario_type": "berth_sts_queue",
        "user": "analista_amp"
    }
    response = client.post("/api/simulation/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["scenario"] == "berth_sts_queue"
    assert "audit_block" in data


def test_worm_request_audit_blocks_endpoint(control, tmp_path, monkeypatch):
    from src.serving import api
    from src.infrastructure.db.postgres_audit import PostgresAuditManager
    client, _ = control
    monkeypatch.setattr(api, 'audit_manager', PostgresAuditManager(tmp_path/'audit.db'))
    assert client.get('/api/v1/audit/worm/blocks?limit=5').status_code == 401
    login(client)
    # Perform a request to generate audit record
    client.get("/api/health")
    response = client.get("/api/v1/audit/worm/blocks?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "chain_integrity" in data
    assert data["chain_integrity"]["valid"] is True
    assert len(data["blocks"]) > 0
