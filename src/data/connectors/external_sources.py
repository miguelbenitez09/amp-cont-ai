"""Verified adapters for externally acquired maritime observations.

This module never fabricates provider observations. A source file is accepted only
when an adjacent manifest records its origin and SHA-256 digest.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd


@dataclass
class ExternalSignalRecord:
    timestamp: str
    source_name: str
    signal_key: str
    raw_value: float
    unit: str
    port_code: Optional[str]
    quality_score: float
    metadata: Dict[str, Any]


class VerifiedExternalSource:
    filename: str = ""
    required_columns: tuple[str, ...] = ()

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path("data/external")

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def load_verified(self) -> pd.DataFrame:
        source_path = self.cache_dir / self.filename
        manifest_path = source_path.with_suffix(source_path.suffix + ".source.json")
        if not source_path.exists() or not manifest_path.exists():
            raise FileNotFoundError(
                f"Verified source unavailable: {source_path}. Add the file and {manifest_path.name}; synthetic fallback is disabled."
            )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("classification") != "OBSERVED":
            raise ValueError(f"Source classification must be OBSERVED: {manifest_path}")
        if not manifest.get("source_url") or not manifest.get("retrieved_at"):
            raise ValueError(f"Manifest lacks source_url or retrieved_at: {manifest_path}")
        observed_digest = self._sha256(source_path)
        if observed_digest != manifest.get("sha256"):
            raise ValueError(f"SHA-256 mismatch for external source: {source_path}")
        frame = pd.read_csv(source_path)
        missing = sorted(set(self.required_columns) - set(frame.columns))
        if missing:
            raise ValueError(f"External source is missing columns: {missing}")
        frame.attrs["provenance"] = manifest
        return frame


class ACPHydrologyConnector(VerifiedExternalSource):
    filename = "acp_gatun_lake_levels_observed.csv"
    required_columns = ("period", "gatun_lake_level_feet", "max_allowed_draft_feet")

    def fetch_historical_series(self) -> pd.DataFrame:
        return self.load_verified()


class AISTelemetryConnector(VerifiedExternalSource):
    filename = "ais_vessel_telemetry_observed.csv"
    required_columns = ("period", "balboa_anchorage_wait_hours", "colon_anchorage_wait_hours")

    def fetch_anchorage_telemetry(self) -> pd.DataFrame:
        return self.load_verified()


class FreightIndexConnector(VerifiedExternalSource):
    filename = "freight_indices_observed.csv"
    required_columns = ("period", "baltic_freight_fbx_usd", "vlsfo_bunker_panama_usd_mt")

    def fetch_freight_rates(self) -> pd.DataFrame:
        return self.load_verified()


def generate_all_external_datasets() -> Dict[str, Any]:
    """Load all verified observations; the historic function name is retained for compatibility."""
    acp = ACPHydrologyConnector().fetch_historical_series()
    ais = AISTelemetryConnector().fetch_anchorage_telemetry()
    freight = FreightIndexConnector().fetch_freight_rates()
    return {
        "acp_records": len(acp),
        "ais_records": len(ais),
        "freight_records": len(freight),
        "status": "VERIFIED_OBSERVED_SOURCES_LOADED",
    }


if __name__ == "__main__":
    print(json.dumps(generate_all_external_datasets(), ensure_ascii=False))
