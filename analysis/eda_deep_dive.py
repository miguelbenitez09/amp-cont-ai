"""
Comprehensive Exploratory Data Analysis & Statistical Profiling Engine.
Adheres to MLOps Masterclass Section 5, 11 & 16:
- Statistical measures: Mean, Variance, Std, Skewness, Kurtosis
- Distribution analysis
- Port market share & Herfindahl-Hirschman Index (HHI)
- Longitudinal trends & Seasonality
- Cross-domain correlations (Containers vs Ro-Ro vs Bunkering)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats
from src.utils.logger import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SILVER_DIR = PROJECT_ROOT / "data" / "silver"
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

class MaritimeEDA:
    """
    Performs deep exploratory data analysis across Silver tables and generates
    quantitative statistical profiles.
    """

    def __init__(self, silver_dir: Path = SILVER_DIR):
        self.silver_dir = silver_dir
        self.df_containers = pd.read_parquet(silver_dir / "fact_containers.parquet")
        self.df_bunkering = pd.read_parquet(silver_dir / "fact_bunkering.parquet")
        self.df_roro = pd.read_parquet(silver_dir / "fact_roro.parquet")
        self.df_macro = pd.read_parquet(silver_dir / "fact_port_macro.parquet")

    def analyze_container_statistics(self) -> dict:
        """
        Calculates central tendency, dispersion, and shape statistics for TEUs by port.
        """
        logger.info("Computing Container Statistical Profiles...")
        # Filter for Total TEU per port
        df_tot = self.df_containers[
            (self.df_containers["category"] == "TOTAL") & 
            (self.df_containers["metric_unit"] == "TEU")
        ].copy()
        
        stats_by_port = {}
        for port, group in df_tot.groupby("port"):
            vals = group["value"].values
            n = len(vals)
            if n < 2:
                continue
            mean_val = np.mean(vals)
            std_val = np.std(vals, ddof=1)
            skew_val = stats.skew(vals)
            kurt_val = stats.kurtosis(vals)
            
            stats_by_port[port] = {
                "observations": n,
                "mean_teu": round(float(mean_val), 2),
                "std_teu": round(float(std_val), 2),
                "cv_pct": round(float((std_val / mean_val) * 100), 2) if mean_val > 0 else 0.0,
                "median_teu": round(float(np.median(vals)), 2),
                "p25_teu": round(float(np.percentile(vals, 25)), 2),
                "p75_teu": round(float(np.percentile(vals, 75)), 2),
                "iqr_teu": round(float(np.percentile(vals, 75) - np.percentile(vals, 25)), 2),
                "skewness": round(float(skew_val), 3),
                "kurtosis": round(float(kurt_val), 3),
                "min_teu": round(float(np.min(vals)), 2),
                "max_teu": round(float(np.max(vals)), 2)
            }
        return stats_by_port

    def analyze_port_concentration_hhi(self) -> dict:
        """
        Computes the Herfindahl-Hirschman Index (HHI) for container ports in Panama
        to quantify port market concentration and competition dynamics.
        HHI = sum(s_i^2) where s_i is market share percentage (0-100).
        HHI < 1500: Unconcentrated / Competitive.
        1500 <= HHI <= 2500: Moderately concentrated.
        HHI > 2500: Highly concentrated.
        """
        logger.info("Computing Port Market Share and HHI Index...")
        df_tot = self.df_containers[
            (self.df_containers["category"] == "TOTAL") & 
            (self.df_containers["metric_unit"] == "TEU")
        ].copy()
        
        yearly_tot = df_tot.groupby(["year", "port"])["value"].sum().unstack(fill_value=0)
        yearly_shares = yearly_tot.div(yearly_tot.sum(axis=1), axis=0) * 100
        
        # Calculate HHI per year
        yearly_hhi = (yearly_shares ** 2).sum(axis=1).round(1).to_dict()
        latest_shares = yearly_shares.iloc[-1].round(2).to_dict()
        
        return {
            "yearly_hhi": yearly_hhi,
            "latest_year": int(yearly_shares.index[-1]),
            "latest_shares": latest_shares
        }

    def analyze_seasonality_and_trend(self) -> dict:
        """
        Evaluates monthly seasonal indices (averages normalized by annual mean).
        """
        logger.info("Computing Seasonal Indices for Container Movements...")
        df_tot = self.df_containers[
            (self.df_containers["category"] == "TOTAL") & 
            (self.df_containers["metric_unit"] == "TEU")
        ].copy()
        
        # Monthly national sum
        nat_monthly = df_tot.groupby(["year", "month"])["value"].sum().reset_index()
        # Compute monthly seasonal factor
        overall_mean = nat_monthly["value"].mean()
        monthly_avg = nat_monthly.groupby("month")["value"].mean()
        seasonal_index = (monthly_avg / overall_mean).round(3).to_dict()
        
        return {
            "overall_monthly_mean_teu": round(float(overall_mean), 2),
            "seasonal_indices": seasonal_index
        }

    def analyze_cross_domain_correlations(self) -> dict:
        """
        Evaluates Pearson and Spearman correlations between national metrics:
        - Total Container TEUs
        - Bunkering VLSFO Sales (TM)
        - Ro-Ro Vehicles Movement
        """
        logger.info("Computing Cross-Domain Correlations...")
        # Monthly national aggregates
        c_agg = self.df_containers[
            (self.df_containers["category"] == "TOTAL") & 
            (self.df_containers["metric_unit"] == "TEU")
        ].groupby("date")["value"].sum().rename("teu_total")
        
        b_agg = self.df_bunkering[
            self.df_bunkering["product"] == "VLSFO"
        ].groupby("date")["value"].sum().rename("vlsfo_tm")
        
        r_agg = self.df_roro.groupby("date")["value"].sum().rename("roro_units")
        
        combined = pd.concat([c_agg, b_agg, r_agg], axis=1).dropna()
        
        corr_pearson = combined.corr(method="pearson").round(3).to_dict()
        corr_spearman = combined.corr(method="spearman").round(3).to_dict()
        
        return {
            "samples_aligned": len(combined),
            "pearson": corr_pearson,
            "spearman": corr_spearman
        }

    def run_full_eda(self) -> dict:
        logger.info("=== Running Complete Maritime EDA Deep Dive ===")
        results = {
            "container_statistics": self.analyze_container_statistics(),
            "port_concentration_hhi": self.analyze_port_concentration_hhi(),
            "seasonality": self.analyze_seasonality_and_trend(),
            "cross_domain_correlations": self.analyze_cross_domain_correlations()
        }
        logger.info("=== EDA Computations Completed Successfully ===")
        return results

if __name__ == "__main__":
    eda = MaritimeEDA()
    res = eda.run_full_eda()
    print("EDA Results Summary:")
    print("HHI:", res["port_concentration_hhi"]["yearly_hhi"])
    print("Seasonality:", res["seasonality"]["seasonal_indices"])
    print("Correlations Pearson:", res["cross_domain_correlations"]["pearson"])
