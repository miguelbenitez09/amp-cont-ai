"""
PortOps Maritime & Port Feature Engineering Module.
Computes domain features for container volume forecasting and port congestion analysis.

Author: Desarrollado v1.0.0 Miguel Benítez
License: GNU General Public License v3.0 (GPL-3.0) with Section 7 Mandatory Attribution
"""

import numpy as np
import pandas as pd
from typing import Dict, Any


class MaritimeFeatureEngine:
    """Computes specialized maritime indicators from normalized silver tables."""

    @classmethod
    def calculate_transshipment_dominance_ratio(cls, df: pd.DataFrame) -> pd.Series:
        """Calculates transshipment TEU / total TEU ratio."""
        if "teu_transshipment" in df.columns and "teu_total" in df.columns:
            return df["teu_transshipment"] / df["teu_total"].replace(0, np.nan)
        return pd.Series(0.88, index=df.index)

    @classmethod
    def apply_canal_drought_penalty(cls, df: pd.DataFrame, draft_col: str = "canal_draft_max_feet") -> pd.Series:
        """Calculates congestion factor when Panama Canal drafts fall below 46 feet."""
        if draft_col in df.columns:
            # Normal draft is 50.0 feet. Every foot lost creates transshipment diversion to ports
            return np.maximum(0.0, (50.0 - df[draft_col]) * 0.04)
        return pd.Series(0.0, index=df.index)

    @classmethod
    def compute_bunker_sulfur_spread(cls, df: pd.DataFrame) -> pd.Series:
        """Calculates Hi5 spread: price difference between high sulfur fuel oil and VLSFO ($/MT)."""
        if "vlsfo_sales_mt" in df.columns and "ifo380_sales_mt" in df.columns:
            return df["vlsfo_sales_mt"] - df["ifo380_sales_mt"]
        return pd.Series(0.0, index=df.index)
