"""
Monte Carlo Simulation Engine for Maritime Port Logistics.
Adheres to MLOps Masterclass Sections 9, 12, 13 & 50:
- Correlated Gaussian / Student-t Copula Simulation via Cholesky Factorization
- Merton (1976) Jump Diffusion Process for Black Swan Disruption Shocks (Canal Droughts, Strikes)
- Moving Block Bootstrap (Künsch 1989) for Non-Parametric Temporal Resampling
- Recursive Multi-Step Auto-regressive Feature Matrix Generation for ML Models
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
from typing import Dict, List, Tuple, Any, Optional, Union
import numpy as np
import pandas as pd

from src.utils.logger import logger
from src.simulation.distribution_profiler import DistributionProfiler

GOLD_DIR = PROJECT_ROOT / "data" / "gold"
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"


class MonteCarloEngine:
    """
    High-performance stochastic simulation engine producing multi-trajectory
    scenarios for terminal container volume, maritime ratios, and operational stress.
    """

    def __init__(
        self,
        seed: int = 42,
        profiler: Optional[DistributionProfiler] = None
    ):
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.profiler = profiler or DistributionProfiler()
        self._ensure_profiler_initialized()

    def _ensure_profiler_initialized(self) -> None:
        """Loads or computes distribution parameters and covariance structure."""
        if not self.profiler.profiles:
            dist_file = METADATA_DIR / "feature_distributions.json"
            if dist_file.exists():
                try:
                    with open(dist_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    self.profiler.profiles = meta.get("features", {})
                    self.profiler.covariance_matrix = pd.DataFrame(meta.get("covariance_matrix", {}))
                    self.profiler.correlation_matrix = pd.DataFrame(meta.get("correlation_matrix", {}))
                    cov_array = self.profiler.covariance_matrix.values
                    self.profiler.cholesky_matrix = np.linalg.cholesky(cov_array)
                    
                    if "cholesky_corr_matrix" in meta and meta["cholesky_corr_matrix"] is not None:
                        self.profiler.cholesky_corr_matrix = np.array(meta["cholesky_corr_matrix"])
                    else:
                        corr_array = self.profiler.correlation_matrix.values + np.eye(len(self.profiler.correlation_matrix)) * 1e-5
                        self.profiler.cholesky_corr_matrix = np.linalg.cholesky(corr_array)
                        
                    logger.info("MonteCarloEngine initialized with cached distribution profiles.")
                    return
                except Exception as e:
                    logger.warning(f"Could not load distribution metadata: {e}. Recomputing...")

            self.profiler.load_data()
            self.profiler.fit_feature_distributions()
            self.profiler.compute_correlation_structure()
            self.profiler.save_profiles()

    def simulate_correlated_shocks(
        self,
        num_paths: int = 1000,
        horizon: int = 12,
        volatility_scale: float = 1.0
    ) -> np.ndarray:
        r"""
        Generates correlated standard normal shocks across driver features using Cholesky factor L:
        $E_{t} = Z_{t} \cdot L^T$ where $Z_{t} \sim \mathcal{N}(0, I)$

        Returns:
            Array of shape (num_paths, horizon, num_driver_features)
        """
        L = getattr(self.profiler, "cholesky_corr_matrix", None)
        if L is None:
            L = self.profiler.cholesky_matrix
        num_features = L.shape[0]

        # Standard normal random matrix (num_paths, horizon, num_features)
        Z = self.rng.standard_normal(size=(num_paths, horizon, num_features))

        # Correlated shocks via linear transformation
        # E[i, t, :] = Z[i, t, :] @ L.T
        correlated_shocks = np.matmul(Z, L.T) * volatility_scale
        return correlated_shocks

    def simulate_jump_diffusion(
        self,
        initial_value: float,
        horizon: int = 12,
        num_paths: int = 1000,
        mu: float = 0.01,
        sigma: float = 0.08,
        lambda_jump: float = 0.15,
        mu_jump: float = -0.20,
        sigma_jump: float = 0.10,
        dt: float = 1.0,
        risk_neutral_compensator: bool = False
    ) -> np.ndarray:
        r"""
        Simulates trajectories using Merton's (1976) Jump-Diffusion stochastic process:
        $S_{t+1} = S_t \exp\left( (\mu - \frac{1}{2}\sigma^2 - \lambda \kappa)\Delta t + \sigma \sqrt{\Delta t} Z_t + \sum_{i=1}^{N_t} Y_i \right)$

        where:
        - $\kappa = \exp(\mu_J + \frac{1}{2}\sigma_J^2) - 1$ is the compensator drift adjustment.
        - $Z_t \sim \mathcal{N}(0, 1)$ represents continuous Brownian market fluctuations.
        - $N_t \sim \text{Poisson}(\lambda \Delta t)$ represents discrete disruption shocks (droughts, tariffs, canal delays).
        - $Y_i \sim \mathcal{N}(\mu_J, \sigma_J^2)$ represents the stochastic jump magnitude.
        - `risk_neutral_compensator`: If False (default for physical logistics), downward jumps
          directly reduce expected volume without financial martingale compensation.

        Returns:
            Array of shape (num_paths, horizon + 1) starting with initial_value at t=0.
        """
        kappa = np.exp(mu_jump + 0.5 * (sigma_jump ** 2)) - 1.0
        drift_comp = (lambda_jump * kappa) if risk_neutral_compensator else 0.0
        drift = (mu - 0.5 * (sigma ** 2) - drift_comp) * dt

        trajectories = np.zeros((num_paths, horizon + 1), dtype=np.float64)
        trajectories[:, 0] = initial_value

        for t in range(horizon):
            # Brownian continuous component
            Z = self.rng.standard_normal(num_paths)
            brownian = sigma * np.sqrt(dt) * Z

            # Poisson discrete jump component
            num_jumps = self.rng.poisson(lam=lambda_jump * dt, size=num_paths)
            jump_impact = np.zeros(num_paths)

            # Vectorized jump aggregation
            has_jumps = num_jumps > 0
            if np.any(has_jumps):
                for idx in np.where(has_jumps)[0]:
                    k = num_jumps[idx]
                    jumps = self.rng.normal(loc=mu_jump, scale=sigma_jump, size=k)
                    jump_impact[idx] = np.sum(jumps)

            # Step forward
            log_returns = drift + brownian + jump_impact
            trajectories[:, t + 1] = trajectories[:, t] * np.exp(log_returns)

        # Enforce non-negativity for physical cargo volumes
        return np.maximum(trajectories, 0.0)

    def simulate_block_bootstrap(
        self,
        historical_series: np.ndarray,
        horizon: int = 12,
        num_paths: int = 1000,
        block_size: int = 3
    ) -> np.ndarray:
        """
        Generates non-parametric trajectories via Moving Block Bootstrap (Künsch 1989).
        Preserves local autocorrelation and seasonal volatility clustering without
        imposing distributional assumptions.

        Returns:
            Array of shape (num_paths, horizon)
        """
        n = len(historical_series)
        if n <= block_size:
            raise ValueError(f"Historical series length ({n}) must be greater than block_size ({block_size}).")

        # Number of possible overlapping blocks
        num_blocks = n - block_size + 1
        blocks = [historical_series[i : i + block_size] for i in range(num_blocks)]

        # How many blocks needed to cover the horizon
        blocks_needed = int(np.ceil(horizon / block_size))
        trajectories = np.zeros((num_paths, horizon), dtype=np.float64)

        for p in range(num_paths):
            sampled_indices = self.rng.integers(0, num_blocks, size=blocks_needed)
            sampled_path = np.concatenate([blocks[i] for i in sampled_indices])[:horizon]
            trajectories[p, :] = sampled_path

        return trajectories

    def generate_stress_scenario_features(
        self,
        port_name: str,
        horizon: int = 6,
        num_paths: int = 500,
        scenario_type: str = "baseline",
        custom_params: Optional[Dict[str, float]] = None
    ) -> Tuple[List[pd.DataFrame], pd.DataFrame]:
        r"""
        Generates full feature matrices compliant with the 81 features required by
        the trained Champion LightGBM models.

        Scenarios:
        - 'baseline': Stochastic simulation following historical mean and covariance.
        - 'canal_drought': Severe canal draft restrictions, causing -35% drop in transshipment.
        - 'empty_imbalance': Surge in empty container repositioning (+45% empty ratio).
        - 'bunker_crisis': Global fuel spike and general freight disruption.
        - 'black_swan_compound': Simultaneous volume jump down (-40%) and empty container surge (+50%).

        Returns:
            Tuple of (list_of_feature_dfs_per_horizon_step, summary_dataframe)
        """
        df_gold = pd.read_parquet(GOLD_DIR / "container_features.parquet")
        port_df = df_gold[df_gold["port"] == port_name].sort_values(by="date").reset_index(drop=True)

        if len(port_df) == 0:
            available = df_gold["port"].unique().tolist()
            raise ValueError(f"Port '{port_name}' not found. Available: {available}")

        last_row = port_df.iloc[-1].copy()
        last_date = pd.to_datetime(last_row["date"])

        # Baseline parameters from last historical records
        base_teu = float(last_row["teu_total"])
        base_transshipment = float(last_row["transshipment_ratio"])
        base_empty = float(last_row["empty_ratio"])
        base_local = float(last_row["local_ratio"])
        base_factor = float(last_row["teu_unit_factor"])

        # Configure scenario multipliers
        params = {
            "transshipment_mult": 1.0,
            "empty_mult": 1.0,
            "volatility_mult": 1.0,
            "jump_lambda": 0.0,
            "jump_mu": -0.20
        }

        if scenario_type == "canal_drought":
            params["transshipment_mult"] = 0.65
            params["volatility_mult"] = 1.5
            params["jump_lambda"] = 0.35
            params["jump_mu"] = -0.30
        elif scenario_type == "empty_imbalance":
            params["empty_mult"] = 1.45
            params["volatility_mult"] = 1.3
        elif scenario_type == "bunker_crisis":
            params["transshipment_mult"] = 0.80
            params["volatility_mult"] = 1.8
            params["jump_lambda"] = 0.20
            params["jump_mu"] = -0.15
        elif scenario_type in ["us_recession", "recession_us"]:
            params["transshipment_mult"] = 0.78
            params["volatility_mult"] = 1.4
            params["jump_lambda"] = 0.15
            params["jump_mu"] = -0.22
        elif scenario_type in ["geopolitical_red_sea", "red_sea_crisis"]:
            params["transshipment_mult"] = 0.85
            params["empty_mult"] = 1.30
            params["volatility_mult"] = 1.6
            params["jump_lambda"] = 0.25
            params["jump_mu"] = -0.18
        elif scenario_type in ["black_swan_compound", "compound_black_swan"]:
            params["transshipment_mult"] = 0.55
            params["empty_mult"] = 1.50
            params["volatility_mult"] = 2.2
            params["jump_lambda"] = 0.50
            params["jump_mu"] = -0.35

        if custom_params:
            params.update(custom_params)

        # Generate correlated stochastic driver shocks
        correlated_shocks = self.simulate_correlated_shocks(
            num_paths=num_paths,
            horizon=horizon,
            volatility_scale=params["volatility_mult"]
        )

        driver_cols = self.profiler.driver_cols
        teu_idx = driver_cols.index("teu_total") if "teu_total" in driver_cols else 0
        trans_idx = driver_cols.index("transshipment_ratio") if "transshipment_ratio" in driver_cols else 1
        empty_idx = driver_cols.index("empty_ratio") if "empty_ratio" in driver_cols else 2

        # Step forward across horizon
        horizon_feature_dfs = []
        historical_teu_history = port_df["teu_total"].tolist()
        historical_trans_history = port_df["transshipment_ratio"].tolist()
        historical_empty_history = port_df["empty_ratio"].tolist()

        # Track per-path states: list of history lists per path
        path_teu_history = [list(historical_teu_history) for _ in range(num_paths)]
        path_trans_history = [list(historical_trans_history) for _ in range(num_paths)]
        path_empty_history = [list(historical_empty_history) for _ in range(num_paths)]

        for h in range(1, horizon + 1):
            future_date = last_date + pd.DateOffset(months=h)
            month = future_date.month
            year = future_date.year

            # Temporal cyclic features
            month_sin = np.sin(2 * np.pi * month / 12)
            month_cos = np.cos(2 * np.pi * month / 12)
            quarter = (month - 1) // 3 + 1
            quarter_sin = np.sin(2 * np.pi * quarter / 4)
            quarter_cos = np.cos(2 * np.pi * quarter / 4)
            is_cny = 1 if month in [1, 2] else 0
            is_peak = 1 if month in [8, 9, 10] else 0
            time_step = int(last_row.get("time_step", 115)) + h

            step_rows = []
            for p in range(num_paths):
                # Retrieve shocks for this step
                shock = correlated_shocks[p, h - 1, :]
                shock_std = self.profiler.profiles.get("teu_total", {}).get("descriptive", {}).get("std", 15000.0)

                # Stochastic jump component if active
                jump = 0.0
                if params["jump_lambda"] > 0:
                    if self.rng.random() < params["jump_lambda"]:
                        jump = self.rng.normal(params["jump_mu"], 0.10)

                # Structural volume transition factor
                effective_mult = 1.0 + (params["transshipment_mult"] - 1.0) * base_transshipment
                if params["empty_mult"] > 1.1:
                    # Operational congestion penalty
                    effective_mult -= 0.05 * (params["empty_mult"] - 1.0)
                effective_mult = max(0.2, effective_mult)
                monthly_drift = effective_mult ** (1.0 / max(1, horizon))

                # Driver innovation via Copula shocks (unit normal shocks)
                prev_teu = path_teu_history[p][-1]
                delta_teu = shock[teu_idx] * (0.04 * prev_teu) * params["volatility_mult"]
                simulated_teu = max(100.0, prev_teu * monthly_drift * (1.0 + jump) + delta_teu)

                sim_trans = np.clip(
                    base_transshipment * params["transshipment_mult"] + shock[trans_idx] * 0.02 * params["volatility_mult"],
                    0.05,
                    0.99
                )
                sim_empty = np.clip(
                    base_empty * params["empty_mult"] + shock[empty_idx] * 0.02 * params["volatility_mult"],
                    0.05,
                    0.95
                )
                sim_local = np.clip(1.0 - sim_trans, 0.01, 0.95)

                # Update path state history
                path_teu_history[p].append(simulated_teu)
                path_trans_history[p].append(sim_trans)
                path_empty_history[p].append(sim_empty)

                teu_hist = path_teu_history[p]
                trans_hist = path_trans_history[p]
                empty_hist = path_empty_history[p]

                # Assemble feature dictionary
                row_dict = {
                    "transshipment_ratio": sim_trans,
                    "local_ratio": sim_local,
                    "empty_ratio": sim_empty,
                    "teu_unit_factor": base_factor,
                    "month_sin": month_sin,
                    "month_cos": month_cos,
                    "quarter_sin": quarter_sin,
                    "quarter_cos": quarter_cos,
                    "is_cny_impact_month": is_cny,
                    "is_peak_shipping_season": is_peak,
                    "time_step": time_step,
                    # Lags
                    "teu_total_lag_1": teu_hist[-2],
                    "teu_total_lag_2": teu_hist[-3] if len(teu_hist) >= 3 else teu_hist[-2],
                    "teu_total_lag_3": teu_hist[-4] if len(teu_hist) >= 4 else teu_hist[-2],
                    "teu_total_lag_12": teu_hist[-13] if len(teu_hist) >= 13 else teu_hist[-2],
                    # Rolling stats for teu_total
                    "teu_total_rolling_mean_3m": float(np.mean(teu_hist[-4:-1])),
                    "teu_total_rolling_std_3m": float(np.std(teu_hist[-4:-1], ddof=1)) if len(teu_hist) >= 4 else 0.0,
                    "teu_total_rolling_min_3m": float(np.min(teu_hist[-4:-1])),
                    "teu_total_rolling_max_3m": float(np.max(teu_hist[-4:-1])),
                    "teu_total_rolling_mean_6m": float(np.mean(teu_hist[-7:-1])),
                    "teu_total_rolling_std_6m": float(np.std(teu_hist[-7:-1], ddof=1)) if len(teu_hist) >= 7 else 0.0,
                    "teu_total_rolling_min_6m": float(np.min(teu_hist[-7:-1])),
                    "teu_total_rolling_max_6m": float(np.max(teu_hist[-7:-1])),
                    "teu_total_rolling_mean_12m": float(np.mean(teu_hist[-13:-1])),
                    "teu_total_rolling_std_12m": float(np.std(teu_hist[-13:-1], ddof=1)) if len(teu_hist) >= 13 else 0.0,
                    "teu_total_rolling_min_12m": float(np.min(teu_hist[-13:-1])),
                    "teu_total_rolling_max_12m": float(np.max(teu_hist[-13:-1])),
                    "teu_total_ewma_span_3": float(np.mean(teu_hist[-4:-1])),
                    "teu_total_ewma_span_6": float(np.mean(teu_hist[-7:-1])),
                    "teu_total_growth_mom": (teu_hist[-2] - teu_hist[-3]) / max(1.0, teu_hist[-3]),
                    "teu_total_growth_yoy": (teu_hist[-2] - teu_hist[-13]) / max(1.0, teu_hist[-13]) if len(teu_hist) >= 13 else 0.0,
                    # Transshipment ratio lags & rollings
                    "transshipment_ratio_lag_1": trans_hist[-2],
                    "transshipment_ratio_lag_2": trans_hist[-3] if len(trans_hist) >= 3 else trans_hist[-2],
                    "transshipment_ratio_lag_3": trans_hist[-4] if len(trans_hist) >= 4 else trans_hist[-2],
                    "transshipment_ratio_lag_12": trans_hist[-13] if len(trans_hist) >= 13 else trans_hist[-2],
                    "transshipment_ratio_rolling_mean_3m": float(np.mean(trans_hist[-4:-1])),
                    "transshipment_ratio_rolling_std_3m": float(np.std(trans_hist[-4:-1], ddof=1)) if len(trans_hist) >= 4 else 0.0,
                    "transshipment_ratio_rolling_min_3m": float(np.min(trans_hist[-4:-1])),
                    "transshipment_ratio_rolling_max_3m": float(np.max(trans_hist[-4:-1])),
                    "transshipment_ratio_rolling_mean_6m": float(np.mean(trans_hist[-7:-1])),
                    "transshipment_ratio_rolling_std_6m": float(np.std(trans_hist[-7:-1], ddof=1)) if len(trans_hist) >= 7 else 0.0,
                    "transshipment_ratio_rolling_min_6m": float(np.min(trans_hist[-7:-1])),
                    "transshipment_ratio_rolling_max_6m": float(np.max(trans_hist[-7:-1])),
                    "transshipment_ratio_rolling_mean_12m": float(np.mean(trans_hist[-13:-1])),
                    "transshipment_ratio_rolling_std_12m": float(np.std(trans_hist[-13:-1], ddof=1)) if len(trans_hist) >= 13 else 0.0,
                    "transshipment_ratio_rolling_min_12m": float(np.min(trans_hist[-13:-1])),
                    "transshipment_ratio_rolling_max_12m": float(np.max(trans_hist[-13:-1])),
                    "transshipment_ratio_ewma_span_3": float(np.mean(trans_hist[-4:-1])),
                    "transshipment_ratio_ewma_span_6": float(np.mean(trans_hist[-7:-1])),
                    "transshipment_ratio_growth_mom": trans_hist[-2] - trans_hist[-3],
                    "transshipment_ratio_growth_yoy": trans_hist[-2] - trans_hist[-13] if len(trans_hist) >= 13 else 0.0,
                    # Empty ratio lags & rollings
                    "empty_ratio_lag_1": empty_hist[-2],
                    "empty_ratio_lag_2": empty_hist[-3] if len(empty_hist) >= 3 else empty_hist[-2],
                    "empty_ratio_lag_3": empty_hist[-4] if len(empty_hist) >= 4 else empty_hist[-2],
                    "empty_ratio_lag_12": empty_hist[-13] if len(empty_hist) >= 13 else empty_hist[-2],
                    "empty_ratio_rolling_mean_3m": float(np.mean(empty_hist[-4:-1])),
                    "empty_ratio_rolling_std_3m": float(np.std(empty_hist[-4:-1], ddof=1)) if len(empty_hist) >= 4 else 0.0,
                    "empty_ratio_rolling_min_3m": float(np.min(empty_hist[-4:-1])),
                    "empty_ratio_rolling_max_3m": float(np.max(empty_hist[-4:-1])),
                    "empty_ratio_rolling_mean_6m": float(np.mean(empty_hist[-7:-1])),
                    "empty_ratio_rolling_std_6m": float(np.std(empty_hist[-7:-1], ddof=1)) if len(empty_hist) >= 7 else 0.0,
                    "empty_ratio_rolling_min_6m": float(np.min(empty_hist[-7:-1])),
                    "empty_ratio_rolling_max_6m": float(np.max(empty_hist[-7:-1])),
                    "empty_ratio_rolling_mean_12m": float(np.mean(empty_hist[-13:-1])),
                    "empty_ratio_rolling_std_12m": float(np.std(empty_hist[-13:-1], ddof=1)) if len(empty_hist) >= 13 else 0.0,
                    "empty_ratio_rolling_min_12m": float(np.min(empty_hist[-13:-1])),
                    "empty_ratio_rolling_max_12m": float(np.max(empty_hist[-13:-1])),
                    "empty_ratio_ewma_span_3": float(np.mean(empty_hist[-4:-1])),
                    "empty_ratio_ewma_span_6": float(np.mean(empty_hist[-7:-1])),
                    "empty_ratio_growth_mom": empty_hist[-2] - empty_hist[-3],
                    "empty_ratio_growth_yoy": empty_hist[-2] - empty_hist[-13] if len(empty_hist) >= 13 else 0.0,
                    # Macro domain lags
                    "nat_vlsfo_sales_tm_lag1": float(last_row.get("nat_vlsfo_sales_tm_lag1", 400000.0)),
                    "nat_roro_units_lag1": float(last_row.get("nat_roro_units_lag1", 12000.0)),
                    # Port dummies
                    "port_Bocas Fruit Co.": 1 if port_name == "Bocas Fruit Co." else 0,
                    "port_Colon Container Terminal": 1 if port_name == "Colon Container Terminal" else 0,
                    "port_PSA Panama International Terminal": 1 if port_name == "PSA Panama International Terminal" else 0,
                    "port_Puerto Balboa": 1 if port_name == "Puerto Balboa" else 0,
                    "port_Puerto Cristóbal": 1 if port_name in ["Puerto Cristóbal", "Puerto Cristobal"] else 0,
                    "port_SSA Marine MIT": 1 if port_name == "SSA Marine MIT" else 0,
                    "littoral_Atlántico": 1 if last_row.get("littoral") in ["Atlántico", "Atlantico"] else 0,
                    "littoral_Pacífico": 1 if last_row.get("littoral") in ["Pacífico", "Pacifico"] else 0
                }
                step_rows.append(row_dict)

            step_df = pd.DataFrame(step_rows)
            step_df["horizon_step"] = h
            step_df["forecast_date"] = future_date.strftime("%Y-%m-%d")
            step_df["path_id"] = list(range(num_paths))
            horizon_feature_dfs.append(step_df)

        combined_df = pd.concat(horizon_feature_dfs, ignore_index=True)
        logger.info(
            f"Generated scenario '{scenario_type}' for {port_name}: "
            f"{num_paths} paths over {horizon} months ({len(combined_df)} records)."
        )
        return horizon_feature_dfs, combined_df


if __name__ == "__main__":
    engine = MonteCarloEngine()
    print("Testing Jump Diffusion...")
    jumps = engine.simulate_jump_diffusion(initial_value=150000.0, horizon=6, num_paths=100)
    print(f"Jump diffusion shape: {jumps.shape}, mean endpoint: {np.mean(jumps[:, -1]):.2f}")

    print("Testing Scenario Feature Generation for Balboa...")
    dfs, combined = engine.generate_stress_scenario_features(
        port_name="Puerto Balboa",
        horizon=3,
        num_paths=50,
        scenario_type="canal_drought"
    )
    print(f"Scenario features shape: {combined.shape}")
    print("Monte Carlo Engine test completed successfully.")
