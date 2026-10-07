"""
Pruebas automatizadas de integración y validación para el Extractor del
Arancel Interactivo de Aduanas de Panamá (ANA).
Autor: Desarrollado v1.0.0 Miguel Benítez / Ing. Miguel Antonio Benítez González (UTP) - GNU GPL-3.0
"""
import json
import pytest
from pathlib import Path
import pandas as pd

from src.data.scrapers.ana_interactive_tariff_scraper import (
    ANATariffScraper,
    SILVER_DIR,
    BRONZE_ANA_DIR
)


def test_ana_bronze_files_exist_and_valid_json():
    """Verifica que los archivos Bronze de la ANA existan y tengan estructura válida."""
    bronze_files = list(BRONZE_ANA_DIR.glob("*.json"))
    assert len(bronze_files) > 0, "Debe existir al menos un archivo JSON en bronze/ana_tariff"
    for bf in bronze_files[:5]:
        with open(bf, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "query_code" in data
        assert "regime" in data
        assert "products" in data
        assert "raw_bytes_sha256" in data


def test_ana_silver_parquet_tables_and_manifests():
    """Verifica que las tablas normalizadas Silver de aranceles existan con sus manifiestos SHA-256."""
    expected_tables = [
        "dim_ana_hs_catalog",
        "dim_ana_hs_taxes",
        "dim_ana_hs_permits_oga",
        "dim_ana_hs_trade_agreements",
        "dim_ana_hs_legal_notes"
    ]
    for table_name in expected_tables:
        pq_path = SILVER_DIR / f"{table_name}.parquet"
        manifest_path = SILVER_DIR / f"{table_name}.parquet.source.json"

        assert pq_path.exists(), f"Falta tabla Parquet: {pq_path}"
        assert manifest_path.exists(), f"Falta manifiesto de procedencia: {manifest_path}"

        df = pd.read_parquet(pq_path)
        assert len(df) > 0, f"La tabla {table_name} no debe estar vacía"

        with open(manifest_path, "r", encoding="utf-8") as mf:
            manifest = json.load(mf)
        assert manifest["records_count"] == len(df)
        assert "sha256" in manifest
        assert "Miguel Benítez" in manifest["author"]


def test_ana_taxes_consistency():
    """Valida consistencia en tributos aduaneros (DAI, ITBMS >= 0, columnas clave)."""
    taxes_path = SILVER_DIR / "dim_ana_hs_taxes.parquet"
    df = pd.read_parquet(taxes_path)
    assert "dai_pct" in df.columns
    assert "itbms_pct" in df.columns
    assert "isc_pct" in df.columns
    assert (df["dai_pct"] >= 0).all()
    assert (df["itbms_pct"] >= 0).all()


def test_ana_oga_permits_structure():
    """Valida que los órganos anuentes identifiquen instituciones y canales SIGA."""
    oga_path = SILVER_DIR / "dim_ana_hs_permits_oga.parquet"
    df = pd.read_parquet(oga_path)
    assert "institucion" in df.columns
    assert "permiso_requisito" in df.columns
    assert "canal_siga" in df.columns
    # Debe haber instituciones regulatorias reconocidas en Panamá
    insts = set(df["institucion"].str.upper())
    assert any("APA" in i or "ALIMENTO" in i or "ENERG" in i or "NORMAS" in i for i in insts)


def test_ana_trade_agreements_coverage():
    """Valida acuerdos comerciales y columnas de desgravamen."""
    agr_path = SILVER_DIR / "dim_ana_hs_trade_agreements.parquet"
    df = pd.read_parquet(agr_path)
    assert "pais_socio" in df.columns
    assert "acuerdo_tratado" in df.columns
    assert "tasa_degravamen" in df.columns
    assert len(df) >= 100, "Debe contener múltiples acuerdos preferenciales registrados"
