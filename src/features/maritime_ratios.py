"""
Maritime Domain Ratios and Operational Indicators Module.
Adheres to MLOps Masterclass Section 17:
Domain-engineered features representing physical port mechanics:
- Transshipment Ratio (Hub Intensity)
- Empty Container Imbalance Ratio (Repositioning Pressure)
- TEU-to-Unit Multiplier (40ft vs 20ft container factor)
"""

import pandas as pd
import numpy as np
from typing import Dict, List

class MaritimeRatioExtractor:
    """
    Computes operational domain ratios from normalized Silver container tables.
    """

    @staticmethod
    def compute_ratios_by_port_and_date(df_containers: pd.DataFrame) -> pd.DataFrame:
        """
        Pivots container movements and computes domain ratios.
        
        Args:
            df_containers: fact_containers DataFrame from Silver layer.
            
        Returns:
            DataFrame indexed by [date, port, littoral] with computed ratios.
        """
        # Pivot TEU and Unidades
        df_piv = df_containers.pivot_table(
            index=["date", "year", "month", "port", "littoral"],
            columns=["metric_unit", "category", "sub_category"],
            values="value",
            aggfunc="sum"
        ).fillna(0)
        
        records = []
        for idx, row in df_piv.iterrows():
            date_val, yr, mo, port, littoral = idx
            
            # Extract volumes
            teu_tot = row.get(("TEU", "TOTAL", "TOTAL"), 0.0)
            unit_tot = row.get(("UNIDADES", "TOTAL", "TOTAL"), 0.0)
            
            teu_tras = row.get(("TEU", "DESTINO", "TRASBORDO"), 0.0)
            teu_local = row.get(("TEU", "DESTINO", "LOCAL"), 0.0)
            teu_zl = row.get(("TEU", "DESTINO", "ZONA_LIBRE"), 0.0)
            
            teu_llenos = row.get(("TEU", "TIPO", "LLENOS"), 0.0)
            teu_vacios = row.get(("TEU", "TIPO", "VACIOS"), 0.0)
            
            # If Total is 0 but destination sum is available, estimate Total
            if teu_tot == 0 and (teu_tras + teu_local + teu_zl) > 0:
                teu_tot = teu_tras + teu_local + teu_zl
                
            # If Total is 0 but type sum is available, estimate Total
            if teu_tot == 0 and (teu_llenos + teu_vacios) > 0:
                teu_tot = teu_llenos + teu_vacios
                
            # 1. Transshipment Ratio (Share of transshipment in total throughput)
            transshipment_ratio = float(np.clip((teu_tras / (teu_tot + 1e-5)) if teu_tot > 0 else 0.0, 0.0, 1.0))
            
            # 2. Local Market Ratio
            local_ratio = float(np.clip((teu_local / (teu_tot + 1e-5)) if teu_tot > 0 else 0.0, 0.0, 1.0))
            
            # 3. Empty Container Imbalance Ratio (Empty / Full)
            empty_ratio = (teu_vacios / (teu_llenos + 1e-5)) if teu_llenos > 0 else 0.0
            
            # 4. TEU per Unit Factor (Approximates 40ft vs 20ft container share: 1.0 = all 20ft, 2.0 = all 40ft)
            teu_unit_factor = (teu_tot / (unit_tot + 1e-5)) if unit_tot > 0 else 1.5
            teu_unit_factor = float(np.clip(teu_unit_factor, 1.0, 2.2))
            
            records.append({
                "date": date_val,
                "year": yr,
                "month": mo,
                "port": port,
                "littoral": littoral,
                "teu_total": teu_tot,
                "unit_total": unit_tot,
                "teu_transshipment": teu_tras,
                "teu_local": teu_local,
                "teu_freezone": teu_zl,
                "teu_full": teu_llenos,
                "teu_empty": teu_vacios,
                "transshipment_ratio": round(float(transshipment_ratio), 4),
                "local_ratio": round(float(local_ratio), 4),
                "empty_ratio": round(float(empty_ratio), 4),
                "teu_unit_factor": round(float(teu_unit_factor), 4)
            })
            
        df_ratios = pd.DataFrame(records).sort_values(by=["date", "port"]).reset_index(drop=True)
        return df_ratios
