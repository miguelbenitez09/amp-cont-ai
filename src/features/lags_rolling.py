"""
Lags, Rolling Window Statistics, and Momentum Feature Engineering.
Adheres strictly to MLOps Masterclass Section 12 & 17:
Zero Data Leakage: All rolling statistics and lags are shifted prior to computation,
ensuring that observations from time t or t+k never contaminate the feature matrix for target y_t.
"""

from typing import List, Optional
import pandas as pd
import numpy as np
from src.utils.logger import logger

class LagAndRollingFeatureExtractor:
    """
    Computes time-series lags, window statistics, and momentum metrics by port.
    """

    def __init__(
        self,
        lags: List[int] = [1, 2, 3, 12],
        rolling_windows: List[int] = [3, 6, 12],
        ewma_spans: List[int] = [3, 6]
    ):
        self.lags = lags
        self.rolling_windows = rolling_windows
        self.ewma_spans = ewma_spans

    def add_lags_and_rolling(
        self,
        df: pd.DataFrame,
        target_cols: List[str] = ["teu_total", "transshipment_ratio", "empty_ratio"],
        group_col: str = "port",
        date_col: str = "date"
    ) -> pd.DataFrame:
        """
        Computes lagged values and rolling aggregations grouped by entity.
        
        Args:
            df: DataFrame containing date, entity group, and target variables.
            target_cols: List of numerical columns to generate features for.
            group_col: Column indicating time-series entity (e.g. 'port' or 'littoral').
            date_col: Column indicating timestamp.
            
        Returns:
            DataFrame enriched with lag, rolling mean, rolling std, and EWMA features.
        """
        logger.info(f"Generating lag and rolling features for {target_cols} grouped by {group_col}...")
        df_out = df.sort_values(by=[group_col, date_col]).copy()
        
        for col in target_cols:
            if col not in df_out.columns:
                continue
                
            grouped = df_out.groupby(group_col)[col]
            
            # 1. Autoregressive Lags (t-k)
            for lag in self.lags:
                col_name = f"{col}_lag_{lag}"
                df_out[col_name] = grouped.shift(lag)
                
            # 2. Rolling Window Statistics with STRICT shift(1) to avoid data leakage
            shifted = grouped.shift(1)
            for window in self.rolling_windows:
                # Rolling Mean
                df_out[f"{col}_rolling_mean_{window}m"] = shifted.rolling(window=window, min_periods=1).mean()
                # Rolling Standard Deviation (Volatility)
                df_out[f"{col}_rolling_std_{window}m"] = shifted.rolling(window=window, min_periods=1).std().fillna(0)
                # Rolling Min and Max
                df_out[f"{col}_rolling_min_{window}m"] = shifted.rolling(window=window, min_periods=1).min()
                df_out[f"{col}_rolling_max_{window}m"] = shifted.rolling(window=window, min_periods=1).max()
                
            # 3. Exponentially Weighted Moving Average (EWMA) with shift(1)
            for span in self.ewma_spans:
                df_out[f"{col}_ewma_span_{span}"] = shifted.ewm(span=span, min_periods=1).mean()
                
            # 4. Momentum / Growth Rate Features (MoM and YoY based on lagged observations)
            # MoM growth: (t-1 - t-2) / (t-2 + eps)
            lag1 = grouped.shift(1)
            lag2 = grouped.shift(2)
            lag12 = grouped.shift(12)
            df_out[f"{col}_growth_mom"] = (lag1 - lag2) / (lag2.abs() + 1e-4)
            df_out[f"{col}_growth_yoy"] = (lag1 - lag12) / (lag12.abs() + 1e-4)

        df_out = df_out.sort_values(by=[date_col, group_col]).reset_index(drop=True)
        return df_out
