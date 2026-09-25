"""
Gold Feature Store Generator.
Adheres to MLOps Masterclass Section 17, 18 & 50:
- Offline Feature Store persistence in Apache Parquet.
- Orchestrates Temporal, Maritime Ratios, and Lag/Rolling extractors.
- Produces training-ready feature matrices for Container Forecasting & Bunkering Demand.
"""

from pathlib import Path
import json
import pandas as pd
from src.utils.logger import logger
from src.features.temporal import TemporalFeatureExtractor
from src.features.maritime_ratios import MaritimeRatioExtractor
from src.features.lags_rolling import LagAndRollingFeatureExtractor

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SILVER_DIR = PROJECT_ROOT / "data" / "silver"
GOLD_DIR = PROJECT_ROOT / "data" / "gold"
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
GOLD_DIR.mkdir(exist_ok=True, parents=True)

class FeatureStorePipeline:
    """
    Coordinates end-to-end transformation of Silver facts into Gold feature tables.
    """

    def __init__(self, silver_dir: Path = SILVER_DIR, gold_dir: Path = GOLD_DIR):
        self.silver_dir = silver_dir
        self.gold_dir = gold_dir

    def build_container_feature_store(self) -> pd.DataFrame:
        """
        Builds the comprehensive feature store for container throughput forecasting.
        """
        logger.info("Building Container Gold Feature Store...")
        
        # 1. Load Silver containers
        cont_path = self.silver_dir / "fact_containers.parquet"
        df_containers = pd.read_parquet(cont_path)
        
        # 2. Extract Maritime Domain Ratios
        df_base = MaritimeRatioExtractor.compute_ratios_by_port_and_date(df_containers)
        
        # 3. Add Temporal & Calendar Features
        df_temp = TemporalFeatureExtractor.add_cyclic_features(df_base, date_col="date")
        
        # 4. Add Lags, Rolling Statistics, and Momentum
        lag_extractor = LagAndRollingFeatureExtractor(
            lags=[1, 2, 3, 12],
            rolling_windows=[3, 6, 12],
            ewma_spans=[3, 6]
        )
        df_featured = lag_extractor.add_lags_and_rolling(
            df_temp,
            target_cols=["teu_total", "transshipment_ratio", "empty_ratio"],
            group_col="port",
            date_col="date"
        )
        
        # 5. Enrich with Cross-Domain Context (National Bunkering & Ro-Ro totals)
        bunk_path = self.silver_dir / "fact_bunkering.parquet"
        if bunk_path.exists():
            df_b = pd.read_parquet(bunk_path)
            vlsfo_monthly = df_b[df_b["product"] == "VLSFO"].groupby("date")["value"].sum().rename("nat_vlsfo_sales_tm")
            # Lag national bunkering by 1 to prevent leakage
            vlsfo_lag1 = vlsfo_monthly.shift(1).rename("nat_vlsfo_sales_tm_lag1")
            df_featured = df_featured.merge(vlsfo_lag1, on="date", how="left")
            
        roro_path = self.silver_dir / "fact_roro.parquet"
        if roro_path.exists():
            df_r = pd.read_parquet(roro_path)
            roro_monthly = df_r.groupby("date")["value"].sum().rename("nat_roro_units")
            roro_lag1 = roro_monthly.shift(1).rename("nat_roro_units_lag1")
            df_featured = df_featured.merge(roro_lag1, on="date", how="left")

        # 6. Save Gold Table
        out_path = self.gold_dir / "container_features.parquet"
        df_featured.to_parquet(out_path, index=False, compression="snappy")
        logger.info(f"Container Feature Store persisted: {df_featured.shape} -> {out_path}")
        
        # Save Feature Catalog Metadata
        feature_metadata = {
            "table_name": "container_features",
            "primary_keys": ["date", "port"],
            "total_records": len(df_featured),
            "total_features": len(df_featured.columns),
            "date_range": [str(df_featured["date"].min()), str(df_featured["date"].max())],
            "feature_columns": df_featured.columns.tolist()
        }
        with open(METADATA_DIR / "container_feature_catalog.json", "w", encoding="utf-8") as f:
            json.dump(feature_metadata, f, indent=2, ensure_ascii=False)
            
        return df_featured

    def build_bunkering_feature_store(self) -> pd.DataFrame:
        """
        Builds feature store for bunkering (marine fuel) sales forecasting.
        """
        logger.info("Building Bunkering Gold Feature Store...")
        bunk_path = self.silver_dir / "fact_bunkering.parquet"
        df_b = pd.read_parquet(bunk_path)
        
        # Aggregate by date, littoral, and product
        piv = df_b.pivot_table(
            index=["date", "year", "month", "littoral"],
            columns="product",
            values="value",
            aggfunc="sum"
        ).fillna(0).reset_index()
        
        # Add temporal features
        df_temp = TemporalFeatureExtractor.add_cyclic_features(piv, date_col="date")
        
        # Add lags for primary fuel products
        lag_extractor = LagAndRollingFeatureExtractor(
            lags=[1, 2, 3, 12],
            rolling_windows=[3, 6],
            ewma_spans=[3]
        )
        fuel_targets = [c for c in ["VLSFO", "MGO", "RMG_380", "NAVES_ATENDIDAS"] if c in df_temp.columns]
        df_featured = lag_extractor.add_lags_and_rolling(
            df_temp,
            target_cols=fuel_targets,
            group_col="littoral",
            date_col="date"
        )
        
        out_path = self.gold_dir / "bunkering_features.parquet"
        df_featured.to_parquet(out_path, index=False, compression="snappy")
        logger.info(f"Bunkering Feature Store persisted: {df_featured.shape} -> {out_path}")
        return df_featured

    def run_all(self):
        self.build_container_feature_store()
        self.build_bunkering_feature_store()

if __name__ == "__main__":
    pipeline = FeatureStorePipeline()
    pipeline.run_all()
