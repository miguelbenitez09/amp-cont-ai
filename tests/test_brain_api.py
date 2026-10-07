"""
Tests for Project Brain API Endpoints and Governance Engine.
Validates BRAIN-001.

Author: Ing. Miguel Antonio Benítez González (UTP)
License: GNU GPL-3.0
"""

import pytest
from fastapi.testclient import TestClient
from src.serving.api import app

client = TestClient(app)

def test_brain_status_endpoint():
    res = client.get("/api/v1/brain/status")
    assert res.status_code == 200
    data = res.json()
    assert data["system"]["name"] == "AMP-CONT-AI"
    assert data["system"]["lifecycle_state"] == "PRODUCTION_CANDIDATE"

def test_brain_capabilities_endpoint():
    res = client.get("/api/v1/brain/capabilities")
    assert res.status_code == 200
    data = res.json()
    assert "roles" in data
    assert len(data["roles"]) >= 6

def test_brain_gaps_endpoint():
    res = client.get("/api/v1/brain/gaps")
    assert res.status_code == 200
    data = res.json()
    assert "gaps" in data
    gap_ids = [g["id"] for g in data["gaps"]]
    assert "UI-001" in gap_ids
    assert "UI-002" in gap_ids
    assert "UI-003" in gap_ids

def test_brain_proposal_evaluation_decision():
    # Test valid proposal
    valid_prop = {
        "proposal_id": "prop_pgvector_migration",
        "scores": {
            "correctness": 4.5,
            "security": 4.8,
            "robustness": 4.2,
            "performance": 4.0,
            "dx": 4.0
        }
    }
    res = client.post("/api/v1/brain/evaluate-proposal", json=valid_prop)
    assert res.status_code == 200
    assert res.json()["decision"] == "APPROVED"

    # Test proposal violating security eliminatory condition (< 3.0)
    insecure_prop = {
        "proposal_id": "prop_disable_tls",
        "scores": {
            "correctness": 4.5,
            "security": 2.0,
            "robustness": 4.0,
            "performance": 4.5,
            "dx": 4.0
        }
    }
    res2 = client.post("/api/v1/brain/evaluate-proposal", json=insecure_prop)
    assert res2.status_code == 200
    assert res2.json()["decision"] == "REJECTED"
    assert "Eliminatory condition" in res2.json()["reason"]
