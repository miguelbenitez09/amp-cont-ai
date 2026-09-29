"""
PortOps Domain Forecasting Wrapper.
Encapsulates Panama port-specific container throughput projections and terminal physical capacity gates.

Author: Desarrollado v1.0.0 Miguel Benítez
License: GNU General Public License v3.0 (GPL-3.0) with Section 7 Mandatory Attribution
"""

from typing import Dict, Any, Optional
import numpy as np


class PortOpsForecastModel:
    """Wraps inference for the PortOps domain pack."""

    PORT_CAPACITIES = {
        "Puerto Balboa": 5000000,
        "Puerto Cristóbal": 2000000,
        "SSA Marine MIT": 3000000,
        "PSA Panama International Terminal": 2000000,
        "Colon Container Terminal": 2500000,
        "Bocas Fruit Co.": 350000
    }

    @classmethod
    def evaluate_capacity_utilization(cls, port_name: str, monthly_teu: float) -> Dict[str, Any]:
        """Calculates port capacity utilization percentage based on physical annual design capacity."""
        annual_capacity = cls.PORT_CAPACITIES.get(port_name, 2500000)
        monthly_capacity = annual_capacity / 12.0
        utilization_pct = round((monthly_teu / monthly_capacity) * 100.0, 2)
        
        status = "NORMAL"
        if utilization_pct >= 90.0:
            status = "CRITICAL_CONGESTION"
        elif utilization_pct >= 75.0:
            status = "HIGH_UTILIZATION"
        elif utilization_pct < 40.0:
            status = "UNDER_UTILIZED"

        return {
            "port_name": port_name,
            "monthly_teu": monthly_teu,
            "monthly_design_capacity_teu": round(monthly_capacity, 0),
            "utilization_pct": utilization_pct,
            "congestion_status": status
        }
