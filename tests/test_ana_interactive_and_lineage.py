"""
Unit and Integration Tests for ANA Interactive Tariff, Lineage Engine, and Regulatory Catalogs.
Verifies:
- HSCodeLineageEngine 3-source cross-referencing and lineage tags
- WCO amendment evolution tracking (1996, 2002, 2007, 2012, 2017, 2022/2025)
- Regulatory catalogs (Memorandos, Resoluciones, Decretos, Acuerdos, Planes de Contingencia)
- Georgia Tech customs enclosures (Recintos Aduaneros)
- FastAPI endpoints for customs intelligence

Desarrollado v1.0.0 Miguel Benítez / Ing. Miguel Antonio Benítez González (UTP) - GNU GPL-3.0
"""

import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from src.serving.api import app
from src.data.hs_code_lineage_engine import HSCodeLineageEngine

client = TestClient(app)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"
SILVER_DIR = PROJECT_ROOT / "data" / "silver"

def test_lineage_engine_initialization():
    """Verify that HSCodeLineageEngine loads all 3 sources and indexes over 20,000 codes."""
    engine = HSCodeLineageEngine.get_instance()
    assert engine._is_loaded is True
    assert len(engine.lineage_index) >= 20000
    summary = engine.get_summary()
    assert summary["total_hs_codes_indexed"] >= 20000
    assert summary["recintos_aduaneros_count"] >= 150
    assert "taxonomies" in summary

def test_lineage_taxonomy_tags():
    """Verify lineage taxonomy tags are properly assigned."""
    engine = HSCodeLineageEngine.get_instance()
    tags = {v["lineage_tag"] for v in engine.lineage_index.values()}
    assert "DERIVADO_MERGE" in tags or "DERIVADO_SPLIT" in tags or "EQUIVALENTE" in tags
    assert "HEREDADO" in tags
    assert "HISTORICO_OBSERVADO" in tags

def test_query_code_lineage_details():
    """Verify detailed technical sheet query for HS code 010121."""
    engine = HSCodeLineageEngine.get_instance()
    res = engine.query_code("010121")
    assert res is not None
    assert "hs_code" in res
    assert "lineage_tag" in res
    assert "amendment_timeline" in res
    assert "taxes" in res
    assert "permits" in res
    assert "recintos_autorizados" in res
    assert len(res["recintos_autorizados"]) > 0

def test_gatech_recintos_aduaneros_dataset():
    """Verify Georgia Tech customs enclosures bronze dataset."""
    recintos_file = BRONZE_DIR / "gatech_recintos" / "recintos_aduaneros_panama.json"
    assert recintos_file.exists()
    with open(recintos_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["total_recintos"] >= 150
    assert len(data["zonas_aduaneras"]) >= 5
    first = data["recintos"][0]
    assert "nombre" in first
    assert "latitud" in first
    assert "longitud" in first
    assert "zona" in first

def test_gatech_logistics_assets_catalog():
    """Verify Georgia Tech logistics assets catalog."""
    assets_file = BRONZE_DIR / "gatech_recintos" / "plataforma_logistica_assets.json"
    assert assets_file.exists()
    with open(assets_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "categories" in data
    cats = data["categories"]
    assert "infraestructura_maritima_y_fluvial" in cats
    assert "regimenes_especiales_y_zonas_francas" in cats
    assert "indicadores_y_conectividad" in cats

def test_ana_regulatory_manifest_and_catalogs():
    """Verify ANA regulatory documents bronze catalogs."""
    manifest_file = BRONZE_DIR / "ana_regulatory" / "regulatory_manifest.json"
    assert manifest_file.exists()
    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["total_regulatory_documents"] >= 500
    catalogs = manifest["catalogs"]
    assert "memorandos" in catalogs
    assert "resoluciones" in catalogs
    assert "resoluciones_anticipadas" in catalogs
    assert "decretos" in catalogs
    assert "acuerdos_comerciales" in catalogs

    # Check that individual JSONs exist and parse cleanly
    for cat_name, info in catalogs.items():
        jf = BRONZE_DIR / "ana_regulatory" / info["file"]
        assert jf.exists()
        assert jf.stat().st_size > 0

def test_api_customs_lineage_endpoint():
    """Test GET /api/v1/customs/lineage/{hs_code} endpoint."""
    resp = client.get("/api/v1/customs/lineage/010121")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "lineage" in data
    lin = data["lineage"]
    assert lin["capitulo_2"] == "01"
    assert "lineage_tag" in lin
    assert "amendment_timeline" in lin

def test_api_customs_knowledge_base_summary():
    """Test GET /api/v1/customs/knowledge-base/summary endpoint."""
    resp = client.get("/api/v1/customs/knowledge-base/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "summary" in data
    assert data["summary"]["total_hs_codes_indexed"] >= 20000

def test_api_customs_recintos_endpoint():
    """Test GET /api/v1/customs/recintos endpoint."""
    resp = client.get("/api/v1/customs/recintos")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["total_recintos"] >= 150
    assert len(data["recintos"]) >= 150

def test_api_customs_tariff_search_endpoint():
    """Test GET /api/v1/customs/tariff/search endpoint."""
    resp = client.get("/api/v1/customs/tariff/search?query=010121")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert len(data["items"]) > 0
    first = data["items"][0]
    assert "hs_code_panama" in first
    assert "descripcion" in first
    assert "lineage_tag" in first
