"""Synchronise non-live INEC MAPL port and vessel reference data.

The ships-in-panama endpoint is intentionally excluded. This job uses the
static/reference endpoints only and writes versioned Parquet snapshots.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests


BASE = "https://www.inec.gob.pa/mapl/api"


def fetch(url: str, params: dict | None = None):
    response = requests.get(url, params=params, timeout=(10, 60))
    response.raise_for_status()
    return response.json()


def sync(output_dir: Path) -> dict:
    retrieved_at = datetime.now(timezone.utc).isoformat()
    ports = fetch(f"{BASE}/ports")
    ships_payload = fetch(f"{BASE}/ship", {"page": 0, "pageSize": 10_000, "sortField": "nombre", "sortDirection": "asc"})
    ships = ships_payload.get("ships", ships_payload) if isinstance(ships_payload, dict) else ships_payload
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {}
    for name, records in (("mapl_ports", ports), ("mapl_ships", ships)):
        frame = pd.DataFrame(records)
        frame["source_id"] = "inec_mapl_ports" if name.endswith("ports") else "inec_mapl_ships"
        frame["retrieved_at"] = retrieved_at
        path = output_dir / f"{name}.parquet"
        frame.to_parquet(path, index=False)
        outputs[name] = {"path": str(path), "rows": len(frame), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    manifest = {"source": "https://www.inec.gob.pa/mapl", "live_endpoint_used": False, "retrieved_at": retrieved_at, "outputs": outputs}
    (output_dir / "mapl_reference_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("data/silver/mapl_reference"))
    args = parser.parse_args()
    print(json.dumps(sync(args.output_dir), ensure_ascii=False, indent=2))
