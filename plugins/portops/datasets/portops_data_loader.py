"""
PortOps Domain Pack Data Loader.
Provides high-level dataset loading and inspection for Panamanian maritime analytics.

Author: Desarrollado v1.0.0 Miguel Benítez
License: GNU General Public License v3.0 (GPL-3.0) with Section 7 Mandatory Attribution
"""

from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SILVER_DIR = PROJECT_ROOT / "data" / "silver"


class PortOpsDataLoader:
    """Loads standardized Silver and Gold layer datasets for the PortOps domain plugin."""

    @classmethod
    def load_container_movements(cls) -> pd.DataFrame:
        p = SILVER_DIR / "container_movements_silver.parquet"
        if not p.exists():
            p = SILVER_DIR / "fact_containers.parquet"
        return pd.read_parquet(p)

    @classmethod
    def load_bunkering_statistics(cls) -> pd.DataFrame:
        p = SILVER_DIR / "fact_bunkering.parquet"
        return pd.read_parquet(p)

    @classmethod
    def load_customs_tariffs(cls) -> pd.DataFrame:
        p = SILVER_DIR / "dim_tariff_panama.parquet"
        return pd.read_parquet(p)

    @classmethod
    def load_macro_energy_multimodal(cls) -> pd.DataFrame:
        p = SILVER_DIR / "fact_macro_energy_multimodal.parquet"
        return pd.read_parquet(p)

    @classmethod
    def get_dataset_inventory(cls) -> Dict[str, Any]:
        tables = [
            "container_movements_silver.parquet",
            "fact_bunkering.parquet",
            "dim_tariff_panama.parquet",
            "fact_macro_energy_multimodal.parquet"
        ]
        res = {}
        for tbl in tables:
            path = SILVER_DIR / tbl
            res[tbl] = {
                "exists": path.exists(),
                "file_size_bytes": path.stat().st_size if path.exists() else 0,
                "records": len(pd.read_parquet(path)) if path.exists() else 0
            }
        return res
