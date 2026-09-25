"""
Port Risk Stress Testing and VaR / CVaR Engine.
Adheres to MLOps Masterclass Sections 9, 12, 13 & 50:
- Forward pass of Champion LightGBM Quantile Models (P10, P50, P90) over Monte Carlo scenarios
- Quantification of Value at Risk (VaR 95%, VaR 99%) and Conditional Value at Risk (CVaR / Expected Shortfall)
- Reverse Stress Testing (RST) to detect structural operational tipping points
- Executive audit and reporting for port authorities and terminal operators
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd
import joblib

from src.utils.logger import logger
from src.simulation.monte_carlo_engine import MonteCarloEngine

MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
REPORTS_DIR.mkdir(exist_ok=True, parents=True)
METADATA_DIR.mkdir(exist_ok=True, parents=True)


class PortStressTester:
    """
    Executes stress testing workflows on trained Champion models using
    Monte Carlo stochastic trajectories, calculating logistical and financial risk metrics.
    """

    def __init__(
        self,
        model_bundle_path: Path = MODELS_DIR / "champion_models.joblib",
        engine: Optional[MonteCarloEngine] = None
    ):
        self.model_bundle_path = model_bundle_path
        self.engine = engine or MonteCarloEngine()
        self.bundle: Optional[Dict[str, Any]] = None
        self.models: Optional[Dict[str, Any]] = None
        self.feature_cols: Optional[List[str]] = None
        self._load_champion_models()

    def _load_champion_models(self) -> None:
        """Loads champion model bundle from disk."""
        if not self.model_bundle_path.exists():
            raise FileNotFoundError(f"Champion model bundle not found at {self.model_bundle_path}")
        self.bundle = joblib.load(self.model_bundle_path)
        self.models = self.bundle["models"]
        self.feature_cols = self.bundle["feature_cols"]
        logger.info(f"Loaded Champion model suite ({list(self.models.keys())}) with {len(self.feature_cols)} features.")

    def run_stress_test(
        self,
        port_name: str,
        horizon: int = 6,
        num_paths: int = 1000,
        scenarios: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Runs comprehensive multi-scenario stress test for a given port.

        Parameters:
            port_name: Name of port (e.g. 'Puerto Balboa', 'PSA Panama International Terminal')
            horizon: Number of forward forecast months (e.g. 6)
            num_paths: Number of Monte Carlo stochastic trajectories (e.g. 1000)
            scenarios: List of scenario names. Defaults to standard stress scenarios.

        Returns:
            Dictionary containing metrics, quantiles, and distribution statistics per scenario.
        """
        target_scenarios = scenarios or [
            "baseline",
            "canal_drought",
            "empty_imbalance",
            "bunker_crisis",
            "black_swan_compound"
        ]

        logger.info(f"Initiating Stress Test Suite for '{port_name}' across {len(target_scenarios)} scenarios.")
        suite_results = {}

        for sc_name in target_scenarios:
            logger.info(f"Executing Monte Carlo simulation for scenario '{sc_name}'...")
            _, combined_features_df = self.engine.generate_stress_scenario_features(
                port_name=port_name,
                horizon=horizon,
                num_paths=num_paths,
                scenario_type=sc_name
            )

            # Ensure all required features are present and aligned
            X_scenario = combined_features_df[self.feature_cols].fillna(0)

            # Predict across quantiles
            preds_p50 = np.clip(self.models["p50"].predict(X_scenario), 0, None)
            preds_p10 = np.clip(self.models["p10"].predict(X_scenario), 0, None)
            preds_p90 = np.clip(self.models["p90"].predict(X_scenario), 0, None)

            # Ensure quantile monotonicity
            preds_p10 = np.minimum(preds_p10, preds_p50)
            preds_p90 = np.maximum(preds_p90, preds_p50)

            combined_features_df["pred_p50"] = preds_p50
            combined_features_df["pred_p10"] = preds_p10
            combined_features_df["pred_p90"] = preds_p90

            # Compute risk metrics per horizon step and endpoint
            endpoint_mask = combined_features_df["horizon_step"] == horizon
            endpoint_preds = combined_features_df.loc[endpoint_mask, "pred_p50"].values

            # Baseline expected volume
            mean_endpoint = float(np.mean(endpoint_preds))
            median_endpoint = float(np.median(endpoint_preds))
            std_endpoint = float(np.std(endpoint_preds, ddof=1))

            # Value at Risk (VaR): Lower percentiles of projected volume
            var_95_level = float(np.percentile(endpoint_preds, 5.0))
            var_99_level = float(np.percentile(endpoint_preds, 1.0))

            # Conditional Value at Risk (CVaR / Expected Shortfall):
            # The expected volume conditional on being in the worst 5% and 1% outcomes
            cvar_95_mask = endpoint_preds <= var_95_level
            cvar_95_level = float(np.mean(endpoint_preds[cvar_95_mask])) if np.any(cvar_95_mask) else var_95_level

            cvar_99_mask = endpoint_preds <= var_99_level
            cvar_99_level = float(np.mean(endpoint_preds[cvar_99_mask])) if np.any(cvar_99_mask) else var_99_level

            # Severe drop probability (e.g. drop > 25% from mean endpoint)
            severe_threshold = mean_endpoint * 0.75
            p_severe_drop = float(np.mean(endpoint_preds < severe_threshold))

            # Horizon step trajectory summary (P10, P50, P90 across paths for fan chart)
            trajectory_profile = []
            for h in range(1, horizon + 1):
                step_vals = combined_features_df.loc[combined_features_df["horizon_step"] == h, "pred_p50"].values
                forecast_dt = combined_features_df.loc[combined_features_df["horizon_step"] == h, "forecast_date"].iloc[0]
                trajectory_profile.append({
                    "horizon_step": h,
                    "forecast_date": str(forecast_dt),
                    "mean": float(np.mean(step_vals)),
                    "p10": float(np.percentile(step_vals, 10.0)),
                    "p25": float(np.percentile(step_vals, 25.0)),
                    "p50": float(np.percentile(step_vals, 50.0)),
                    "p75": float(np.percentile(step_vals, 75.0)),
                    "p90": float(np.percentile(step_vals, 90.0)),
                    "std": float(np.std(step_vals, ddof=1))
                })

            suite_results[sc_name] = {
                "expected_volume": mean_endpoint,
                "median_volume": median_endpoint,
                "volatility_std": std_endpoint,
                "var_95_volume": var_95_level,
                "var_99_volume": var_99_level,
                "cvar_95_expected_shortfall": cvar_95_level,
                "cvar_99_expected_shortfall": cvar_99_level,
                "prob_severe_drop_25pct": p_severe_drop,
                "trajectory_profile": trajectory_profile,
                "endpoint_sample": endpoint_preds[:100].tolist()  # Sample for distribution rendering
            }

        logger.info(f"Completed stress test suite for '{port_name}'.")
        return {
            "port_name": port_name,
            "horizon_months": horizon,
            "num_paths": num_paths,
            "scenarios": suite_results
        }

    def reverse_stress_test(
        self,
        port_name: str,
        critical_drop_pct: float = 0.30,
        horizon: int = 3
    ) -> Dict[str, Any]:
        r"""
        Reverse Stress Testing (RST):
        Finds the critical combination of operational shocks that causes projected
        container volume to drop by more than `critical_drop_pct` (e.g. 30%).

        Explores 2D Grid:
        - Transshipment drop: 0% to -60%
        - Empty ratio surge: 0% to +80%

        Returns:
            Heatmap grid and identified tipping point boundary.
        """
        logger.info(f"Running Reverse Stress Testing for {port_name} (Threshold: -{critical_drop_pct*100}%)...")

        # Baseline prediction
        _, base_df = self.engine.generate_stress_scenario_features(
            port_name=port_name,
            horizon=horizon,
            num_paths=30,
            scenario_type="baseline"
        )
        base_X = base_df[self.feature_cols].fillna(0)
        base_preds = self.models["p50"].predict(base_X)
        baseline_endpoint = float(np.mean(base_preds[base_df["horizon_step"] == horizon]))

        trans_mults = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4]  # 0% to -60% drop
        empty_mults = [1.0, 1.15, 1.30, 1.45, 1.60, 1.80]   # 0% to +80% surge

        grid_results = []
        tipping_points = []

        for tm in trans_mults:
            row_items = []
            for em in empty_mults:
                custom_params = {
                    "transshipment_mult": tm,
                    "empty_mult": em,
                    "volatility_mult": 1.0,
                    "jump_lambda": 0.0
                }
                _, test_df = self.engine.generate_stress_scenario_features(
                    port_name=port_name,
                    horizon=horizon,
                    num_paths=20,
                    scenario_type="baseline",
                    custom_params=custom_params
                )
                test_X = test_df[self.feature_cols].fillna(0)
                test_preds = self.models["p50"].predict(test_X)
                endpoint_pred = float(np.mean(test_preds[test_df["horizon_step"] == horizon]))

                drop_pct = (baseline_endpoint - endpoint_pred) / baseline_endpoint
                is_breach = bool(drop_pct >= critical_drop_pct)

                cell_info = {
                    "transshipment_multiplier": tm,
                    "transshipment_drop_pct": round((1.0 - tm) * 100, 1),
                    "empty_multiplier": em,
                    "empty_surge_pct": round((em - 1.0) * 100, 1),
                    "projected_teu": round(endpoint_pred, 1),
                    "drop_percentage": round(drop_pct * 100, 2),
                    "is_breach": is_breach
                }
                row_items.append(cell_info)

                if is_breach and not any(tp["transshipment_multiplier"] == tm for tp in tipping_points):
                    tipping_points.append(cell_info)

            grid_results.append(row_items)

        logger.info(f"Reverse Stress Test identified {len(tipping_points)} boundary failure combinations.")
        return {
            "port_name": port_name,
            "baseline_endpoint_teu": baseline_endpoint,
            "critical_drop_threshold_pct": critical_drop_pct * 100,
            "tipping_point_boundaries": tipping_points,
            "grid": grid_results
        }

    def generate_simulation_report(
        self,
        stress_results: Dict[str, Any],
        rst_results: Dict[str, Any],
        output_path: Path = REPORTS_DIR / "MONTE_CARLO_SIMULATION_REPORT.md"
    ) -> Path:
        """Writes an exhaustive analytical markdown report of the stress simulation."""
        port = stress_results["port_name"]
        scenarios = stress_results["scenarios"]
        base = scenarios.get("baseline", {})
        base_exp = base.get("expected_volume", 1.0)

        lines = [
            f"# Reporte Ejecutivo de Simulación Monte Carlo y Pruebas de Estrés: {port}",
            "",
            "## 1. Fundamentos Teóricos y Marco de Gobernanza de Riesgo MLOps",
            "La validación de modelos de Machine Learning no concluye con métricas de test set histórico (WAPE, RMSE).",
            "En logística portuaria y de comercio global, los choques estructurales (*Black Swan events*) alteran la dinámica",
            "operacional. Para cuantificar la solvencia y resiliencia del modelo de pronóstico de la **Autoridad Marítima de Panamá**,",
            "se ejecutó una simulación estocástica de **Monte Carlo** basada en:",
            "- **Perturbaciones Correlacionadas (Cholesky Factorization)**: Preservan las covarianzas entre ratios de transbordo, contenedores vacíos y volumen.",
            "- **Difusión con Saltos de Merton (1976)**: Modela interrupciones abruptas mediante procesos de Poisson ($N_t \\sim \\text{Poisson}(\\lambda \\Delta t)$).",
            "- **Métricas de Riesgo Financiero y Logístico**: Value at Risk (**VaR 95%**, **VaR 99%**) y Conditional Value at Risk (**CVaR / Expected Shortfall**).",
            "",
            "## 2. Resultados de las Pruebas de Estrés por Escenario (Horizonte: 6 meses)",
            "",
            "| Escenario | Volumen Esperado (TEU) | Desv. Est. (TEU) | VaR 95% (Piso) | CVaR 95% (Cola Crítica) | Prob. Caída > 25% | Impacto vs Base |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |"
        ]

        for sc_name, data in scenarios.items():
            impact_pct = ((data["expected_volume"] - base_exp) / base_exp) * 100
            name_label = sc_name.replace("_", " ").title()
            lines.append(
                f"| **{name_label}** | {data['expected_volume']:,.0f} | {data['volatility_std']:,.0f} | "
                f"{data['var_95_volume']:,.0f} | {data['cvar_95_expected_shortfall']:,.0f} | "
                f"{data['prob_severe_drop_25pct']*100:.1f}% | {impact_pct:+.1f}% |"
            )

        lines.extend([
            "",
            "### Análisis de Métricas de Cola:",
            "- **Value at Risk (VaR 95%)**: Nivel de volumen que garantiza un 95% de confianza de no ser perforado a la baja.",
            "- **Expected Shortfall (CVaR 95%)**: Promedio del volumen en el 5% de las peores trayectorias simuladas. A diferencia del VaR, el CVaR es una **medida coherente de riesgo** (satisface sub-aditividad), crucial para la asignación de reservas de patio de maniobra.",
            "- **Canal Drought**: La caída del 35% en transbordo combinada con saltos de Poisson eleva la probabilidad de caída severa a niveles críticos.",
            "- **Black Swan Compound**: El choque simultáneo de caída de transbordo (-45%) y alza de vacíos (+50%) provoca una contracción extrema en el P10.",
            "",
            "## 3. Pruebas de Estrés Inversas (Reverse Stress Testing - RST)",
            "El Reverse Stress Testing no pregunta *'¿qué pasa si ocurre este escenario?'*, sino *'¿cuál es la mínima combinación de fallas operacionales que provoca el colapso del sistema portuario?'*",
            f"- **Umbral de Falla Crítica Definido**: Caída de volumen $\\ge {rst_results['critical_drop_threshold_pct']:.0f}\\%$ respecto al baseline.",
            "",
            "### Puntos de Inflexión Críticos Detectados (Tipping Points):",
            "| Caída Transbordo (%) | Alza Vacíos (%) | Volumen Proyectado (TEU) | Caída Estimada (%) | ¿Brecha Crítica? |",
            "| :---: | :---: | :---: | :---: | :---: |"
        ])

        for tp in rst_results.get("tipping_point_boundaries", []):
            lines.append(
                f"| -{tp['transshipment_drop_pct']}% | +{tp['empty_surge_pct']}% | {tp['projected_teu']:,.0f} | "
                f"-{tp['drop_percentage']:.1f}% | **{'SÍ' if tp['is_breach'] else 'NO'}** |"
            )

        lines.extend([
            "",
            "## 4. Recomendaciones Operacionales para la Autoridad Marítima de Panamá (AMP)",
            "1. **Monitoreo de Umbral de Vacíos**: Mantener el `empty_ratio` por debajo del 45% en terminales del Pacífico (Balboa/PSA) para evitar estrangulamiento logístico.",
            "2. **Activación de Buffer de Capacidad**: Establecer la capacidad operativa de contingencia alineada con el **CVaR 95%** en lugar del P50 mediano.",
            "3. **Gobernanza de Re-entrenamiento**: Si el drift monitor (`Evidently`) detecta desviaciones multivariadas hacia la frontera del Reverse Stress Test, disparar el pipeline de re-entrenamiento continuo (`make train-champion`).",
            "",
            f"*(Reporte generado automáticamente por `src/simulation/stress_tester.py`)*"
        ])

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        # Also save JSON metadata
        summary_json = METADATA_DIR / "stress_test_results.json"
        with open(summary_json, "w", encoding="utf-8") as f:
            json.dump({
                "stress_results": stress_results,
                "rst_results": rst_results
            }, f, indent=2)

        logger.info(f"Monte Carlo stress report written to {output_path} and JSON saved to {summary_json}")
        return output_path


if __name__ == "__main__":
    tester = PortStressTester()
    res = tester.run_stress_test(port_name="Puerto Balboa", horizon=6, num_paths=100)
    rst = tester.reverse_stress_test(port_name="Puerto Balboa", critical_drop_pct=0.25, horizon=3)
    tester.generate_simulation_report(res, rst)
    print("Stress testing and Reverse Stress Testing successfully executed.")
