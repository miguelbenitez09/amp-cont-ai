"""
Dataset Manifest and Provenance Engine for Panama PortOps-AI v2.0
Implements formal dataset cataloging, cryptographic content hashing,
and classification states (FACT, MEASURED, DERIVED, ESTIMATED, SIMULATED, DEMO).
Author: Desarrollado v1.0 Miguel Benítez - GNU GPL-3.0
"""

import json
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import pandas as pd


class DatasetManifest(BaseModel):
    """Immutable manifest accompanying every registered dataset."""

    dataset_id: str
    source_id: str
    layer: str  # 'raw', 'bronze', 'silver', 'gold'
    version: str = "1.0.0"
    coverage_start: str
    coverage_end: str
    months_count: int
    row_count: int
    schema_hash: str
    content_hash: str
    quality_score: float = 1.0
    classification: str = "FACT"  # 'FACT', 'MEASURED', 'DERIVED', 'ESTIMATED', 'SIMULATED', 'DEMO'
    pipeline_version: str = "2.0.0"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def from_dataframe(
        cls,
        df: pd.DataFrame,
        dataset_id: str,
        source_id: str,
        layer: str,
        date_col: str = "event_date",
        classification: str = "FACT",
        version: str = "1.0.0"
    ) -> "DatasetManifest":
        """Generates a complete cryptographic manifest from a pandas DataFrame."""
        # 1. Schema Hash
        schema_repr = str(list(df.dtypes.items())).encode("utf-8")
        schema_hash = hashlib.sha256(schema_repr).hexdigest()

        # 2. Content Hash
        content_repr = hashlib.sha256(pd.util.hash_pandas_object(df).values).hexdigest()

        # 3. Dynamic temporal calculation
        if date_col in df.columns:
            date_series = pd.to_datetime(df[date_col])
            min_date = date_series.min().strftime("%Y-%m-%d")
            max_date = date_series.max().strftime("%Y-%m-%d")
            months_count = int(date_series.dt.to_period("M").nunique())
        else:
            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            min_date = now_str
            max_date = now_str
            months_count = 0

        return cls(
            dataset_id=dataset_id,
            source_id=source_id,
            layer=layer,
            version=version,
            coverage_start=min_date,
            coverage_end=max_date,
            months_count=months_count,
            row_count=len(df),
            schema_hash=schema_hash,
            content_hash=content_repr,
            classification=classification
        )
