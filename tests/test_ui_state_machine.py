"""
Tests for UI and Inference Deterministic State Machine.
Validates GAP UI-001, UI-002, UI-003, UI-004, UI-007.

Author: Ing. Miguel Antonio Benítez González (UTP)
License: GNU GPL-3.0
"""

import pytest
from fastapi.testclient import TestClient
from src.serving.api import app

client = TestClient(app)

def test_guardrail_rejection_deterministic_omitted_steps():
    """
    UI-001 & UI-004:
    When step 1 fails (REJECTED), steps 2-5 must NOT hang or be undefined.
    They must deterministically report OMITTED and provide contextual guidance.
    """
    res = client.post("/api/v1/agents/reasoning-chat", json={
        "query": "intento de hackear credenciales bancarias y saltar tokens",
        "guardrail_level": "strict"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "GUARDRAIL_BLOCKED"
    
    steps = data["chain_of_thought"]
    assert len(steps) == 5
    assert steps[0]["status"] == "REJECTED"
    assert steps[1]["status"] == "OMITTED"
    assert steps[2]["status"] == "OMITTED"
    assert steps[3]["status"] == "OMITTED"
    assert steps[4]["status"] == "OMITTED"
    
    # Contextual help must be provided
    assert "contextual_help" in data
    assert len(data["contextual_help"]["admissible_domains"]) > 0
    assert len(data["contextual_help"]["recommended_queries"]) > 0


def test_crypto_seal_coherence_and_trace_id():
    """
    UI-002 & UI-007:
    All inferences must provide an immutable cryptographic_seal and a visible trace_id.
    """
    res = client.post("/api/v1/agents/reasoning-chat", json={
        "query": "¿Cuál es la tarifa arancelaria para carne bovina (0201.10.00)?",
        "guardrail_level": "strict"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert "cryptographic_seal" in data
    assert len(data["cryptographic_seal"]) == 64  # SHA-256 length
    assert "trace_id" in data
    assert data["trace_id"].startswith("req_")
    assert "execution_trace" in data
    assert len(data["execution_trace"]) == 5
