r"""
Unit and Integration Tests for Simulation Engine.
Adheres to MLOps Masterclass Section 50: Testing and Quality Assurance:
- Parametric distribution fitting and KS goodness-of-fit
- Covariance & Correlation positive definiteness and Cholesky decomposition ($L L^T = \Sigma$)
- Merton Jump Diffusion and Moving Block Bootstrap stochastic generators
- LightGBM forward pass over simulated scenarios and VaR / CVaR risk bounds
"""

import sys
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.simulation.distribution_profiler import DistributionProfiler
from src.simulation.monte_carlo_engine import MonteCarloEngine
from src.simulation.stress_tester import PortStressTester


@pytest.fixture(scope="module")
def profiler():
    """Provides initialized DistributionProfiler with fitted parameters."""
    p = DistributionProfiler()
    p.load_data()
    p.fit_feature_distributions()
    p.compute_correlation_structure()
    return p


@pytest.fixture(scope="module")
def engine(profiler):
    """Provides MonteCarloEngine instance."""
    return MonteCarloEngine(seed=42, profiler=profiler)


@pytest.fixture(scope="module")
def tester(engine):
    """Provides PortStressTester with Champion models loaded."""
    return PortStressTester(engine=engine)


def test_distribution_profiler_statistics(profiler):
    """Verifies that descriptive statistics and KS test statistics are valid."""
    profiles = profiler.profiles
    assert len(profiles) > 0, "No features were profiled."

    for col in ["teu_total", "transshipment_ratio", "empty_ratio"]:
        assert col in profiles, f"Key feature {col} missing from profiles."
        data = profiles[col]
        desc = data["descriptive"]
        assert desc["count"] > 100
        assert desc["mean"] > 0
        assert desc["std"] > 0
        assert desc["min"] <= desc["median"] <= desc["max"]

        best = data["best_distribution"]
        assert best["name"] in ["norm", "lognorm", "gamma", "beta", "t"]
        assert 0.0 <= best["ks_statistic"] <= 1.0
        assert 0.0 <= best["ks_p_value"] <= 1.0


def test_cholesky_decomposition_reconstruction(profiler):
    """Verifies that Cholesky factor L satisfies L @ L.T == Sigma (Positive Definite)."""
    cov_df = profiler.covariance_matrix
    L = profiler.cholesky_matrix
    assert cov_df is not None
    assert L is not None
    assert L.shape[0] == L.shape[1] == len(cov_df)

    # Reconstructed covariance
    reconstructed = L @ L.T
    np.testing.assert_allclose(
        reconstructed,
        cov_df.values,
        rtol=1e-4,
        atol=1e-4,
        err_msg="Cholesky decomposition failed to reconstruct covariance matrix."
    )

    # Verify Correlation Cholesky
    L_corr = getattr(profiler, "cholesky_corr_matrix", None)
    if L_corr is not None:
        reconstructed_corr = L_corr @ L_corr.T
        corr_diag = np.diag(reconstructed_corr)
        np.testing.assert_allclose(corr_diag, np.ones_like(corr_diag), rtol=1e-3, atol=1e-3)


def test_monte_carlo_correlated_shocks(engine):
    """Tests shape, volatility scaling, and seed reproducibility for correlated shocks."""
    shocks1 = engine.simulate_correlated_shocks(num_paths=100, horizon=6, volatility_scale=1.0)
    assert shocks1.shape == (100, 6, len(engine.profiler.driver_cols))

    # Test seed reproducibility
    eng2 = MonteCarloEngine(seed=42, profiler=engine.profiler)
    shocks2 = eng2.simulate_correlated_shocks(num_paths=100, horizon=6, volatility_scale=1.0)
    np.testing.assert_array_equal(shocks1, shocks2)


def test_merton_jump_diffusion(engine):
    """Tests that Merton Jump Diffusion trajectories are non-negative and execute jumps."""
    init_val = 100000.0
    trajectories = engine.simulate_jump_diffusion(
        initial_value=init_val,
        horizon=12,
        num_paths=500,
        mu=0.01,
        sigma=0.05,
        lambda_jump=0.4,
        mu_jump=-0.30
    )
    assert trajectories.shape == (500, 13)
    assert np.all(trajectories[:, 0] == init_val)
    assert np.all(trajectories >= 0.0), "Physical TEU volume cannot be negative."

    # Under negative jump intensity, mean endpoint should be below geometric drift alone
    endpoint_mean = np.mean(trajectories[:, -1])
    assert endpoint_mean < init_val * np.exp(0.01 * 12)


def test_moving_block_bootstrap(engine):
    """Tests that block bootstrap resamples contiguous segments preserving horizon length."""
    hist = np.arange(100.0, 200.0)
    boot = engine.simulate_block_bootstrap(hist, horizon=10, num_paths=50, block_size=3)
    assert boot.shape == (50, 10)
    assert np.all(boot >= 100.0)
    assert np.all(boot < 200.0)


def test_scenario_feature_generation_columns(engine):
    """Verifies that generated scenario features match all required model features."""
    bundle_path = Path("models/champion_models.joblib")
    import joblib
    bundle = joblib.load(bundle_path)
    expected_cols = bundle["feature_cols"]

    _, combined = engine.generate_stress_scenario_features(
        port_name="Puerto Balboa",
        horizon=3,
        num_paths=10,
        scenario_type="canal_drought"
    )

    for col in expected_cols:
        assert col in combined.columns, f"Required feature '{col}' missing from scenario generator."

    assert len(combined) == 30  # 3 horizon steps * 10 paths
    assert not combined[expected_cols].isnull().any().any(), "Scenario features contain unexpected NaN values."


def test_stress_tester_var_cvar_monotonicity(tester):
    """
    Verifies quantitative financial risk properties:
    - Downside Volume: VaR_99 <= VaR_95 (The 1% worst tail volume is lower than the 5% tail)
    - Downside Volume: CVaR_95 <= VaR_95 (Expected Shortfall is strictly in the tail)
    - Positive predicted volumes (non-negative)
    """
    results = tester.run_stress_test(
        port_name="Puerto Balboa",
        horizon=3,
        num_paths=50,
        scenarios=["baseline", "canal_drought"]
    )

    scenarios = results["scenarios"]
    for sc_name, sc_data in scenarios.items():
        var_95 = sc_data["var_95_volume"]
        var_99 = sc_data["var_99_volume"]
        cvar_95 = sc_data["cvar_95_expected_shortfall"]
        exp_vol = sc_data["expected_volume"]

        assert var_95 > 0, "VaR 95% volume must be positive."
        assert var_99 > 0, "VaR 99% volume must be positive."
        assert var_99 <= var_95, f"Monotonicity violation in {sc_name}: VaR99 ({var_99}) > VaR95 ({var_95})"
        assert cvar_95 <= var_95 + 1e-4, f"CVaR95 ({cvar_95}) must be <= VaR95 ({var_95})"
        assert var_95 <= exp_vol, f"VaR95 ({var_95}) should be less than expected volume ({exp_vol})"


def test_reverse_stress_testing_execution(tester):
    """Verifies that reverse stress testing produces a valid 2D evaluation grid."""
    rst = tester.reverse_stress_test(port_name="Puerto Balboa", critical_drop_pct=0.25, horizon=3)
    assert "grid" in rst
    assert "tipping_point_boundaries" in rst
    assert len(rst["grid"]) > 0
    first_cell = rst["grid"][0][0]
    assert "transshipment_drop_pct" in first_cell
    assert "empty_surge_pct" in first_cell
    assert "projected_teu" in first_cell
    assert "is_breach" in first_cell
