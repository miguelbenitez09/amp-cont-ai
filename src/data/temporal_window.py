"""
Temporal Window Validation and Dynamic Month Counter for Panama PortOps-AI v2.0
Calculates actual observed calendar periods using pd.period_range.
Prevents hardcoded assumptions and verifies strict time continuity.
Author: Desarrollado v1.0 Miguel Benítez - GNU GPL-3.0
"""

from typing import Dict, Any, Tuple
import pandas as pd


class TemporalWindowManager:
    """Verifies empirical timeline coverage against continuous calendar periods."""

    @classmethod
    def calculate_window_coverage(
        cls,
        df: pd.DataFrame,
        date_col: str = "date"
    ) -> Dict[str, Any]:
        """
        Dynamically computes expected continuous monthly periods vs actual observed periods.
        """
        if date_col not in df.columns or df.empty:
            return {
                "valid": False,
                "error": f"Columna temporal '{date_col}' no encontrada en el DataFrame."
            }

        dates = pd.to_datetime(df[date_col]).dropna()
        min_date = dates.min()
        max_date = dates.max()

        expected_periods = pd.period_range(start=min_date, end=max_date, freq="M")
        expected_months_count = len(expected_periods)

        actual_periods = dates.dt.to_period("M").unique()
        actual_months_count = len(actual_periods)

        missing_periods = [str(p) for p in expected_periods if p not in actual_periods]
        coverage_pct = (actual_months_count / max(expected_months_count, 1)) * 100.0

        return {
            "valid": len(missing_periods) == 0,
            "min_date": min_date.strftime("%Y-%m-%d"),
            "max_date": max_date.strftime("%Y-%m-%d"),
            "expected_months_count": expected_months_count,
            "actual_months_count": actual_months_count,
            "coverage_pct": round(coverage_pct, 2),
            "missing_periods_count": len(missing_periods),
            "missing_periods": missing_periods[:12],  # Cap output
            "dynamic_summary": f"Cobertura real: {actual_months_count} meses observados de {expected_months_count} meses calendario esperados ({coverage_pct:.1f}%)."
        }
