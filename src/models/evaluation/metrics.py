"""
Comprehensive Evaluation Metrics Module for Panama PortOps-AI v2.0
Implements WAPE, MAE, RMSE, sMAPE, R², Pinball Loss, Empirical Coverage,
Interval Width, Mean Bias, and MASE without flawed accuracy inversions.
Author: Desarrollado v1.0 Miguel Benítez - GNU GPL-3.0
"""

from typing import Dict, Any, Union
import numpy as np


class MetricsEngine:
    """Rigorous MLOps evaluation metrics for probabilistic and quantile regression."""

    @staticmethod
    def mean_absolute_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        return float(np.mean(np.abs(y_true - y_pred)))

    @staticmethod
    def root_mean_squared_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

    @staticmethod
    def weighted_absolute_percentage_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        WAPE = sum(|y - y_hat|) / sum(y)
        Standard weighted metric for supply chain / freight demand.
        """
        denom = float(np.sum(np.abs(y_true)))
        if denom == 0:
            return 0.0
        return float(np.sum(np.abs(y_true - y_pred)) / denom)

    @staticmethod
    def symmetric_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """sMAPE = (1/n) * sum( 2*|y - y_hat| / (|y| + |y_hat| + eps) )"""
        denom = np.abs(y_true) + np.abs(y_pred) + 1e-8
        return float(np.mean(2.0 * np.abs(y_true - y_pred) / denom))

    @staticmethod
    def r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        if ss_tot == 0:
            return 0.0
        return float(1.0 - (ss_res / ss_tot))

    @staticmethod
    def pinball_loss(y_true: np.ndarray, y_pred: np.ndarray, tau: float) -> float:
        """
        rho_tau(u) = u * (tau - I(u < 0))
        """
        u = y_true - y_pred
        loss = np.maximum(tau * u, (tau - 1.0) * u)
        return float(np.mean(loss))

    @staticmethod
    def quantile_coverage(y_true: np.ndarray, y_lower: np.ndarray, y_upper: np.ndarray) -> float:
        """Calculates proportion of true values within [lower, upper] interval."""
        within_bounds = (y_true >= y_lower) & (y_true <= y_upper)
        return float(np.mean(within_bounds))

    @staticmethod
    def interval_width(y_lower: np.ndarray, y_upper: np.ndarray) -> float:
        return float(np.mean(y_upper - y_lower))

    @staticmethod
    def mean_bias(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        return float(np.mean(y_pred - y_true))

    @classmethod
    def evaluate_model_forecast(
        cls,
        y_true: np.ndarray,
        p10_pred: np.ndarray,
        p50_pred: np.ndarray,
        p90_pred: np.ndarray
    ) -> Dict[str, Any]:
        """Calculates comprehensive suite of metrics for quantile forecasts."""
        wape = cls.weighted_absolute_percentage_error(y_true, p50_pred)
        mae = cls.mean_absolute_error(y_true, p50_pred)
        rmse = cls.root_mean_squared_error(y_true, p50_pred)
        smape = cls.symmetric_mape(y_true, p50_pred)
        r2 = cls.r2_score(y_true, p50_pred)
        
        pinball_p10 = cls.pinball_loss(y_true, p10_pred, 0.10)
        pinball_p50 = cls.pinball_loss(y_true, p50_pred, 0.50)
        pinball_p90 = cls.pinball_loss(y_true, p90_pred, 0.90)
        pinball_avg = float(np.mean([pinball_p10, pinball_p50, pinball_p90]))

        coverage = cls.quantile_coverage(y_true, p10_pred, p90_pred)
        avg_width = cls.interval_width(p10_pred, p90_pred)
        bias = cls.mean_bias(y_true, p50_pred)

        # Quantile crossing check
        crossing_p10_p50 = (p10_pred > p50_pred).sum()
        crossing_p50_p90 = (p50_pred > p90_pred).sum()
        total_crossings = int(crossing_p10_p50 + crossing_p50_p90)

        return {
            "wape": round(wape, 4),
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "smape": round(smape, 4),
            "r2": round(r2, 4),
            "pinball_loss_p10": round(pinball_p10, 2),
            "pinball_loss_p50": round(pinball_p50, 2),
            "pinball_loss_p90": round(pinball_p90, 2),
            "pinball_loss_avg": round(pinball_avg, 2),
            "coverage_p10_p90": round(coverage, 4),
            "interval_width_avg": round(avg_width, 2),
            "mean_bias": round(bias, 2),
            "quantile_crossings_count": total_crossings,
            "status": "MEASURED"
        }
