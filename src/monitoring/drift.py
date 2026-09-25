"""
Data and Concept Drift Monitoring Engine with Evidently AI.
Adheres to MLOps Masterclass Section 0, 48 & 50:
- Detects covariate shift (Data Drift) between Training baseline and Production batches.
- Statistical tests: Kolmogorov-Smirnov for numerical continuous features, Wasserstein distance.
- Generates interactive HTML observability dashboard and JSON alert summaries.
- Recommends automated retraining triggers upon drift threshold violations.
"""

from pathlib import Path
import json
from typing import Dict, Any, List
import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset

from src.utils.logger import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GOLD_DIR = PROJECT_ROOT / "data" / "gold"
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

class MaritimeDriftMonitor:
    """
    Evaluates covariate and concept drift on container forecasting features.
    """

    def __init__(
        self,
        gold_dir: Path = GOLD_DIR,
        reports_dir: Path = REPORTS_DIR,
        split_date: str = "2024-01-01",
        drift_share_threshold: float = 0.25
    ):
        self.gold_dir = gold_dir
        self.reports_dir = reports_dir
        self.split_date = split_date
        self.drift_share_threshold = drift_share_threshold

    def run_drift_analysis(self) -> Dict[str, Any]:
        """
        Executes statistical drift tests comparing Reference (pre-2024) vs Current (2024-2026).
        """
        logger.info("Initiating Evidently AI Data Drift Analysis...")
        feat_path = self.gold_dir / "container_features.parquet"
        df = pd.read_parquet(feat_path)
        
        # Key monitored features: Targets, Ratios, Lags, Rolling Stats, and Bunkering context
        monitored_cols = [
            "teu_total", "transshipment_ratio", "empty_ratio", "teu_unit_factor",
            "teu_total_lag_1", "teu_total_lag_2", "teu_total_lag_3", "teu_total_lag_12",
            "teu_total_rolling_mean_3m", "teu_total_rolling_mean_6m", "teu_total_rolling_std_3m",
            "transshipment_ratio_lag_1", "empty_ratio_lag_1", "month_sin", "month_cos",
            "nat_vlsfo_sales_tm_lag1"
        ]
        available_cols = [c for c in monitored_cols if c in df.columns]
        
        ref_df = df[df["date"] < self.split_date][available_cols].dropna()
        curr_df = df[df["date"] >= self.split_date][available_cols].dropna()
        
        logger.info(f"Reference samples (Train): {len(ref_df)} | Current samples (Production): {len(curr_df)}")
        
        # Build and run Evidently Report
        report = Report(metrics=[DataDriftPreset()])
        snapshot = report.run(reference_data=ref_df, current_data=curr_df)
        
        # Save Interactive HTML Report
        html_path = self.reports_dir / "data_drift_report.html"
        snapshot.save_html(str(html_path))
        logger.info(f"Interactive Data Drift HTML Report saved to {html_path}")
        
        # Parse JSON results for programmatic threshold alerts
        report_dict = snapshot.dict()
        
        # Extract drift summary
        metrics = report_dict.get("metrics", [])
        dataset_drift_metric = next((m for m in metrics if "DatasetDriftMetric" in m.get("metric", "") or "DataDriftTable" in m.get("metric", "")), None)
        
        drift_share = 0.0
        number_of_drifted = 0
        total_features = len(available_cols)
        drift_detected = False
        
        if dataset_drift_metric:
            res = dataset_drift_metric.get("result", {})
            drift_share = res.get("share_of_drifted_columns", 0.0)
            number_of_drifted = res.get("number_of_drifted_columns", 0)
            drift_detected = res.get("dataset_drift", False)
            
        alert_triggered = drift_share >= self.drift_share_threshold
        
        summary = {
            "status": "DRIFT_ALERT" if alert_triggered else "STABLE",
            "reference_window": f"2015-01 to {self.split_date}",
            "current_window": f"{self.split_date} to 2026-08",
            "total_monitored_features": total_features,
            "drifted_features_count": number_of_drifted,
            "share_of_drifted_features": round(float(drift_share), 4),
            "drift_share_threshold": self.drift_share_threshold,
            "retraining_recommended": alert_triggered,
            "html_report_path": str(html_path)
        }
        
        json_path = self.reports_dir / "data_drift_summary.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
            
        if alert_triggered:
            logger.warning(
                f"DATA DRIFT ALERT: {number_of_drifted}/{total_features} features ({drift_share*100:.1f}%) drifted! "
                f"Automated retraining pipeline recommended."
            )
        else:
            logger.info(f"Features Stable: Drift share {drift_share*100:.1f}% below threshold {self.drift_share_threshold*100:.1f}%.")
            
        return summary

if __name__ == "__main__":
    monitor = MaritimeDriftMonitor()
    res = monitor.run_drift_analysis()
    print("Drift Analysis Summary:")
    print(res)
