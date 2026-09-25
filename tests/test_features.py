"""
Unit tests for Feature Engineering Transformations.
Adheres to MLOps Masterclass Section 12, 17 & 25 (Testing feature validity & no data leakage).
"""

from pathlib import Path
import pandas as pd
import numpy as np
import pytest
from src.features.temporal import TemporalFeatureExtractor
from src.features.maritime_ratios import MaritimeRatioExtractor

GOLD_DIR = Path("data/gold")

@pytest.fixture
def gold_container_features():
    path = GOLD_DIR / "container_features.parquet"
    if not path.exists():
        pytest.skip("container_features.parquet does not exist yet")
    return pd.read_parquet(path)

def test_cyclic_features_bounds(gold_container_features):
    """Verifies that sine and cosine features are strictly within [-1.0, 1.0]."""
    for col in ["month_sin", "month_cos", "quarter_sin", "quarter_cos"]:
        assert gold_container_features[col].between(-1.0001, 1.0001).all(), f"Cyclic feature {col} out of [-1, 1] bounds!"

def test_maritime_ratios_bounds(gold_container_features):
    """Verifies that percentage ratios are strictly in [0.0, 1.0]."""
    assert gold_container_features["transshipment_ratio"].between(0.0, 1.0).all(), "Transshipment ratio out of bounds"
    assert gold_container_features["local_ratio"].between(0.0, 1.0).all(), "Local ratio out of bounds"
    assert (gold_container_features["empty_ratio"] >= 0.0).all(), "Empty ratio cannot be negative"

def test_zero_leakage_lags(gold_container_features):
    """
    Verifies that lag_1 for time t strictly equals target value at time t-1
    for the same port.
    """
    df = gold_container_features.sort_values(by=["port", "date"]).reset_index(drop=True)
    for port in df["port"].unique():
        port_df = df[df["port"] == port].reset_index(drop=True)
        # For rows starting from index 1, lag_1 must match previous row's teu_total
        actual_lag1 = port_df["teu_total_lag_1"].iloc[1:].values
        prev_actual = port_df["teu_total"].iloc[:-1].values
        # Compare (ignoring NaNs if any)
        valid_mask = ~np.isnan(actual_lag1)
        np.testing.assert_allclose(actual_lag1[valid_mask], prev_actual[valid_mask], rtol=1e-5)
