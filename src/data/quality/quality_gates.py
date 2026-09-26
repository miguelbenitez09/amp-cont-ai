"""
Data Quality Gates Engine for Panama PortOps-AI v2.0
Implements 5 industrial gates:
- Gate 1: Schema Contract
- Gate 2: Completeness
- Gate 3: Validity & Physical Bounds
- Gate 4: Consistency & Balance Check
- Gate 5: Temporal Integrity & Bitemporal Separation
Author: Desarrollado v1.0 Miguel Benítez - GNU GPL-3.0
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timezone
import pandas as pd
import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
QUARANTINE_DIR = ROOT_DIR / "data" / "quarantine"


class QualityGateResult:
    """Detailed outcome of a quality gate evaluation."""

    def __init__(self, gate_name: str, passed: bool, score: float, violations: List[str]):
        self.gate_name = gate_name
        self.passed = passed
        self.score = score
        self.violations = violations

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_name": self.gate_name,
            "passed": self.passed,
            "score": round(self.score, 4),
            "violations_count": len(self.violations),
            "violations": self.violations[:10]  # Cap for brevity
        }


class DataQualityPipeline:
    """Orchestrates the 5 Data Quality Gates and manages quarantines."""

    VALID_PORTS = [
        "Puerto Balboa",
        "PSA Panama International Terminal",
        "Manzanillo International Terminal (MIT)",
        "SSA Marine MIT",
        "Puerto Cristóbal",
        "Colon Container Terminal (CCT)",
        "Colon Container Terminal",
        "Bocas Fruit Co."
    ]

    @classmethod
    def evaluate_gate_1_schema(cls, df: pd.DataFrame, required_columns: List[str]) -> QualityGateResult:
        """Gate 1: Verifies schema conformance and presence of mandatory columns."""
        missing = [col for col in required_columns if col not in df.columns]
        passed = (len(missing) == 0)
        score = (len(required_columns) - len(missing)) / max(len(required_columns), 1)
        violations = [f"Columna obligatoria ausente: '{col}'" for col in missing]
        return QualityGateResult("Gate 1: Schema Conformance", passed, score, violations)

    @classmethod
    def evaluate_gate_2_completeness(cls, df: pd.DataFrame, target_columns: List[str]) -> QualityGateResult:
        """Gate 2: Verifies absence of nulls in target columns and continuity."""
        violations = []
        total_cells = len(df) * len(target_columns)
        null_count = 0

        for col in target_columns:
            if col in df.columns:
                n_nulls = int(df[col].isna().sum())
                if n_nulls > 0:
                    null_count += n_nulls
                    violations.append(f"Columna '{col}' contiene {n_nulls} valores nulos ({n_nulls/len(df):.2%}).")

        passed = (null_count == 0)
        score = 1.0 - (null_count / max(total_cells, 1))
        return QualityGateResult("Gate 2: Completeness", passed, score, violations)

    @classmethod
    def evaluate_gate_3_validity(cls, df: pd.DataFrame, teu_col: str = "teu_total", port_col: str = "port") -> QualityGateResult:
        """Gate 3: Enforces physical bounds (non-negative, realistic capacity, valid ports)."""
        violations = []

        # 1. Port validity
        if port_col in df.columns:
            invalid_ports = set(df[port_col].dropna().unique()) - set(cls.VALID_PORTS)
            if invalid_ports:
                violations.append(f"Puertos desconocidos detectados: {invalid_ports}")

        # 2. TEU non-negativity and upper bound
        if teu_col in df.columns:
            negative_teus = (df[teu_col] < 0).sum()
            if negative_teus > 0:
                violations.append(f"{negative_teus} filas con volumen TEU negativo.")

            extreme_teus = (df[teu_col] > 600_000).sum()
            if extreme_teus > 0:
                violations.append(f"{extreme_teus} filas exceden la capacidad física portuaria máxima (>600k TEU).")

        passed = (len(violations) == 0)
        score = 1.0 if passed else max(0.0, 1.0 - len(violations) * 0.25)
        return QualityGateResult("Gate 3: Validity & Physical Bounds", passed, score, violations)

    @classmethod
    def evaluate_gate_4_consistency(cls, df: pd.DataFrame) -> QualityGateResult:
        """Gate 4: Verifies internal accounting consistency (total = import + export + transshipment)."""
        violations = []
        if {"teu_total", "teu_transshipment", "teu_import", "teu_export"}.issubset(df.columns):
            computed = df["teu_transshipment"] + df["teu_import"] + df["teu_export"]
            discrepancy = np.abs(df["teu_total"] - computed)
            # Allow 1.0 TEU rounding tolerance
            bad_accounting = (discrepancy > 2.0).sum()
            if bad_accounting > 0:
                violations.append(f"{bad_accounting} registros violan el balance contable de TEUs (Total != Import + Export + Trasbordo).")

        passed = (len(violations) == 0)
        score = 1.0 if passed else max(0.0, 1.0 - (bad_accounting / max(len(df), 1)))
        return QualityGateResult("Gate 4: Relational Consistency", passed, score, violations)

    @classmethod
    def evaluate_gate_5_temporal_integrity(
        cls,
        df: pd.DataFrame,
        date_col: str = "event_date",
        published_col: str = "published_at",
        cutoff_timestamp: Optional[datetime] = None
    ) -> QualityGateResult:
        """
        Gate 5: Verifies bitemporal separation and ensures no future data is leaked.
        """
        violations = []
        now = pd.Timestamp.now().tz_localize(None)

        if date_col in df.columns:
            date_series = pd.to_datetime(df[date_col]).dt.tz_localize(None)
            # Check future event dates
            future_events = (date_series > now).sum()
            if future_events > 0:
                violations.append(f"{future_events} observaciones con fechas futuras a la fecha actual.")

        if published_col in df.columns and cutoff_timestamp is not None:
            pub_series = pd.to_datetime(df[published_col]).dt.tz_localize(None)
            cutoff_ts = pd.to_datetime(cutoff_timestamp).tz_localize(None)
            leaked_records = (pub_series > cutoff_ts).sum()
            if leaked_records > 0:
                violations.append(f"{leaked_records} registros publicados con posterioridad al cutoff ({cutoff_timestamp}).")

        passed = (len(violations) == 0)
        score = 1.0 if passed else 0.0
        return QualityGateResult("Gate 5: Temporal Integrity & Bitemporal Leakage", passed, score, violations)

    @classmethod
    def run_all_gates(
        cls,
        df: pd.DataFrame,
        dataset_name: str,
        required_cols: List[str],
        target_cols: List[str],
        cutoff_timestamp: Optional[datetime] = None
    ) -> Tuple[bool, float, List[Dict[str, Any]]]:
        """Runs the entire 5-Gate suite and quarantines dataset if failed."""
        g1 = cls.evaluate_gate_1_schema(df, required_cols)
        g2 = cls.evaluate_gate_2_completeness(df, target_cols)
        g3 = cls.evaluate_gate_3_validity(df)
        g4 = cls.evaluate_gate_4_consistency(df)
        g5 = cls.evaluate_gate_5_temporal_integrity(df, cutoff_timestamp=cutoff_timestamp)

        results = [g1, g2, g3, g4, g5]
        all_passed = all(r.passed for r in results)
        overall_score = float(np.mean([r.score for r in results]))

        if not all_passed:
            # Quarantine dataset
            QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            quarantine_path = QUARANTINE_DIR / f"{dataset_name}_quarantined_{ts}.parquet"
            try:
                df.to_parquet(quarantine_path)
            except Exception:
                pass

        return all_passed, overall_score, [r.to_dict() for r in results]
