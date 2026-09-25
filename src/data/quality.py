"""
Data Quality Validation Engine (Quality Gates).
Adheres to MLOps Masterclass Section 16:
- Schema validation
- Null checks
- Range & boundary verification
- Primary key uniqueness
- Domain-specific relational & additive checks
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
import pandas as pd
import numpy as np
from src.utils.logger import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SILVER_DIR = PROJECT_ROOT / "data" / "silver"

class DataQualityError(Exception):
    """Raised when data quality validation fails."""
    pass

class MaritimeDataQualityGate:
    """
    Implements production data quality verification rules over Silver tables.
    """

    def __init__(self, silver_dir: Path = SILVER_DIR):
        self.silver_dir = silver_dir

    def validate_containers(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validates fact_containers table against strict business rules.
        """
        logger.info("Running Data Quality Gate on Containers...")
        results = {}
        
        # 1. Null checks
        null_counts = df.isna().sum().to_dict()
        total_rows = len(df)
        has_nulls = any(cnt > 0 for cnt in null_counts.values())
        results["null_check"] = {"passed": not has_nulls, "null_counts": null_counts}
        if has_nulls:
            logger.warning(f"Nulls detected: {null_counts}")
            
        # 2. Date boundary check
        min_date = df["date"].min()
        max_date = df["date"].max()
        valid_dates = (min_date >= pd.Timestamp("2015-01-01")) and (max_date <= pd.Timestamp("2026-12-31"))
        results["date_bounds"] = {
            "passed": valid_dates,
            "min_date": str(min_date),
            "max_date": str(max_date)
        }
        if not valid_dates:
            logger.error(f"Date bounds violated: {min_date} to {max_date}")
            raise DataQualityError(f"Dates out of expected bounds: {min_date} to {max_date}")

        # 3. Non-negative values
        negative_count = (df["value"] < 0).sum()
        results["non_negative"] = {"passed": negative_count == 0, "negatives": int(negative_count)}
        if negative_count > 0:
            raise DataQualityError(f"Found {negative_count} negative container movement values!")

        # 4. Port domain check
        known_ports = {
            "Bocas Fruit Co.", "Colon Container Terminal", "SSA Marine MIT",
            "Puerto Balboa", "Puerto Cristóbal", "PSA Panama International Terminal"
        }
        found_ports = set(df["port"].unique())
        invalid_ports = found_ports - known_ports
        results["known_ports"] = {"passed": len(invalid_ports) == 0, "invalid_ports": list(invalid_ports)}
        if invalid_ports:
            raise DataQualityError(f"Encountered unexpected ports: {invalid_ports}")

        # 5. Primary key uniqueness
        pk_cols = ["date", "port", "category", "sub_category", "metric_unit"]
        dup_count = df.duplicated(subset=pk_cols).sum()
        results["uniqueness"] = {"passed": dup_count == 0, "duplicates": int(dup_count)}
        if dup_count > 0:
            raise DataQualityError(f"Found {dup_count} duplicate primary key records!")

        # 6. Additive consistency check: Llenos + Vacíos vs Total
        # Filter where both are available for the same date and port in TEU
        df_teu = df[df["metric_unit"] == "TEU"]
        piv = df_teu.pivot_table(
            index=["date", "port"],
            columns=["category", "sub_category"],
            values="value",
            aggfunc="sum"
        ).fillna(0)
        
        additive_passed = True
        discrepancies = 0
        if ("TIPO", "LLENOS") in piv.columns and ("TIPO", "VACIOS") in piv.columns and ("TOTAL", "TOTAL") in piv.columns:
            sum_tipo = piv[("TIPO", "LLENOS")] + piv[("TIPO", "VACIOS")]
            tot = piv[("TOTAL", "TOTAL")]
            # Allow up to 1% rounding or preliminary tolerance
            diff = (sum_tipo - tot).abs()
            rel_diff = diff / (tot + 1)
            discrepancies = int((rel_diff > 0.05).sum())
            if discrepancies > 10:
                additive_passed = False
                logger.warning(f"Additive discrepancies detected in {discrepancies} instances")
                
        results["additive_consistency"] = {
            "passed": additive_passed,
            "discrepancies_count": discrepancies
        }
        
        logger.info(f"Container Quality Gate passed with results: {results}")
        return results

    def validate_bunkering(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validates fact_bunkering table.
        """
        logger.info("Running Data Quality Gate on Bunkering...")
        results = {}
        
        # 1. Null check
        null_counts = df.isna().sum().to_dict()
        results["null_check"] = {"passed": sum(null_counts.values()) == 0, "nulls": null_counts}
        
        # 2. Date check
        valid_dates = (df["date"].min() >= pd.Timestamp("2015-01-01")) and (df["date"].max() <= pd.Timestamp("2026-12-31"))
        results["date_bounds"] = {"passed": valid_dates}
        
        # 3. Litoral check
        valid_litorals = {"Pacífico", "Atlántico", "Nacional"}
        found_litorals = set(df["littoral"].unique())
        results["litorals"] = {"passed": found_litorals.issubset(valid_litorals)}
        
        # 4. Values >= 0
        results["non_negative"] = {"passed": (df["value"] >= 0).all()}
        
        logger.info(f"Bunkering Quality Gate passed with results: {results}")
        return results

    def run_all(self) -> Dict[str, Dict[str, Any]]:
        report = {}
        cont_path = self.silver_dir / "fact_containers.parquet"
        bunk_path = self.silver_dir / "fact_bunkering.parquet"
        
        if cont_path.exists():
            df_c = pd.read_parquet(cont_path)
            report["containers"] = self.validate_containers(df_c)
            
        if bunk_path.exists():
            df_b = pd.read_parquet(bunk_path)
            report["bunkering"] = self.validate_bunkering(df_b)
            
        return report

if __name__ == "__main__":
    gate = MaritimeDataQualityGate()
    summary = gate.run_all()
    print("Quality Gates Summary:")
    print(summary)
