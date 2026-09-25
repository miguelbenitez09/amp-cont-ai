"""
Temporal and Calendar Feature Engineering Module.
Adheres to MLOps Masterclass Section 17:
- Cyclic sine/cosine transformations for periodic calendar units.
- Maritime seasonal flags (Chinese New Year, Peak Shipping Season).
"""

import numpy as np
import pandas as pd
from typing import List

class TemporalFeatureExtractor:
    """
    Extracts cyclic, seasonal, and calendar features from date timestamps.
    """

    @staticmethod
    def add_cyclic_features(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
        """
        Computes sin/cos encodings for month and quarter.
        Preserves continuity across year boundaries (e.g. Dec -> Jan).
        """
        df = df.copy()
        month = df[date_col].dt.month
        quarter = df[date_col].dt.quarter
        
        # Monthly cyclic encoding (period = 12)
        df["month_sin"] = np.sin(2 * np.pi * month / 12)
        df["month_cos"] = np.cos(2 * np.pi * month / 12)
        
        # Quarterly cyclic encoding (period = 4)
        df["quarter_sin"] = np.sin(2 * np.pi * quarter / 4)
        df["quarter_cos"] = np.cos(2 * np.pi * quarter / 4)
        
        # Domain-specific maritime flags
        # February is heavily impacted by Chinese New Year shutdown in Asia
        df["is_cny_impact_month"] = (month == 2).astype(int)
        
        # July - October is global peak shipping season (pre-Christmas retail logistics)
        df["is_peak_shipping_season"] = month.isin([7, 8, 9, 10]).astype(int)
        
        # Linear trend proxy: months elapsed since baseline (2015-01)
        min_date = pd.Timestamp("2015-01-01")
        df["time_step"] = ((df[date_col].dt.year - 2015) * 12 + (df[date_col].dt.month - 1)).astype(int)
        
        return df
