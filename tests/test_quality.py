"""
Unit tests for Maritime Data Quality Gates.
Adheres to MLOps Masterclass Section 1.1, 16 & 25 (CI testing with pytest).
"""

from pathlib import Path
import pandas as pd
import pytest
from src.data.quality import MaritimeDataQualityGate, DataQualityError

SILVER_DIR = Path("data/silver")

@pytest.fixture
def sample_containers_df():
    path = SILVER_DIR / "fact_containers.parquet"
    if not path.exists():
        pytest.skip("fact_containers.parquet does not exist yet")
    return pd.read_parquet(path)

@pytest.fixture
def sample_bunkering_df():
    path = SILVER_DIR / "fact_bunkering.parquet"
    if not path.exists():
        pytest.skip("fact_bunkering.parquet does not exist yet")
    return pd.read_parquet(path)

def test_container_no_nulls(sample_containers_df):
    """Verifies that no null values exist in mandatory container columns."""
    assert sample_containers_df["date"].notna().all(), "Found null timestamps in containers"
    assert sample_containers_df["port"].notna().all(), "Found null ports in containers"
    assert sample_containers_df["value"].notna().all(), "Found null values in containers"

def test_container_date_range(sample_containers_df):
    """Verifies that dates are within valid bounds (2015-2026)."""
    min_date = sample_containers_df["date"].min()
    max_date = sample_containers_df["date"].max()
    assert min_date >= pd.Timestamp("2015-01-01"), f"Min date {min_date} is before 2015"
    assert max_date <= pd.Timestamp("2026-12-31"), f"Max date {max_date} is after 2026"

def test_container_non_negative_values(sample_containers_df):
    """Verifies that all container movements are >= 0."""
    assert (sample_containers_df["value"] >= 0).all(), "Found negative container movements"

def test_container_known_ports(sample_containers_df):
    """Verifies that only authorized Panamanian ports are present."""
    known_ports = {
        "Bocas Fruit Co.", "Colon Container Terminal", "SSA Marine MIT",
        "Puerto Balboa", "Puerto Cristóbal", "PSA Panama International Terminal"
    }
    found_ports = set(sample_containers_df["port"].unique())
    assert found_ports.issubset(known_ports), f"Unknown ports found: {found_ports - known_ports}"

def test_bunkering_litorals(sample_bunkering_df):
    """Verifies that bunkering litorals are valid."""
    valid_litorals = {"Pacífico", "Atlántico", "Nacional"}
    found_litorals = set(sample_bunkering_df["littoral"].unique())
    assert found_litorals.issubset(valid_litorals), f"Unknown litorals: {found_litorals - valid_litorals}"
