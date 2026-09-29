"""
Tests for Domain Plugin API Routes & Scraper Live Status Endpoint.
Verifies:
1. GET /api/v1/plugins
2. GET /api/v1/plugins/portops
3. GET /api/v1/plugins/portops/regulations
4. GET /api/v1/plugins/portops/inventory
5. POST /api/v1/plugins/portops/capacity-check
6. GET /api/v1/data/scrapers/status

Author: Desarrollado v1.0.0 Miguel Benítez
License: GNU GPL-3.0 with Section 7 Mandatory Attribution
"""

import pytest
from fastapi.testclient import TestClient
from src.serving.api import app

client = TestClient(app)


def test_list_plugins_endpoint():
    res = client.get("/api/v1/plugins")
    assert res.status_code == 200
    data = res.json()
    assert data["total_plugins"] >= 1
    assert any(p["name"] == "portops" for p in data["plugins"])


def test_get_portops_plugin_details():
    res = client.get("/api/v1/plugins/portops")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "portops"
    assert data["version"] == "1.0.0"
    assert "tools" in data
    assert len(data["tools"]) >= 3


def test_portops_regulations_endpoint():
    res = client.get("/api/v1/plugins/portops/regulations")
    assert res.status_code == 200
    data = res.json()
    assert "regulations" in data
    assert len(data["regulations"]) >= 4

    # Search query
    res_search = client.get("/api/v1/plugins/portops/regulations?query=Ley 56")
    assert res_search.status_code == 200
    assert len(res_search.json()["regulations"]) == 1


def test_portops_inventory_endpoint():
    res = client.get("/api/v1/plugins/portops/inventory")
    assert res.status_code == 200
    data = res.json()
    assert "inventory" in data
    assert "container_movements_silver.parquet" in data["inventory"]


def test_portops_capacity_check_endpoint():
    res = client.post("/api/v1/plugins/portops/capacity-check?port_name=Puerto Balboa&monthly_teu=280000")
    assert res.status_code == 200
    data = res.json()
    assert data["port_name"] == "Puerto Balboa"
    assert data["utilization_pct"] > 0
    assert "congestion_status" in data


def test_scrapers_live_status_endpoint():
    res = client.get("/api/v1/data/scrapers/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "OPERATIONAL"
    assert "inec_imports_scraper" in data
    assert "inec_exports_scraper" in data
    assert "amp_lakehouse" in data
    assert data["author"] == "developed by Miguel Benítez"
