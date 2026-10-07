"""Atomically publish an ANA staging snapshot only after completeness checks."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def publish(manifest_path: Path, current_path: Path, silver_manifest_path: Path | None = None) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    silver = json.loads(silver_manifest_path.read_text(encoding="utf-8")) if silver_manifest_path else {}
    failures = manifest.get("failures") or []
    if not manifest.get("complete") or failures or (silver_manifest_path and not silver.get("publication_ready")):
        raise RuntimeError(
            f"Refusing publication: complete={manifest.get('complete')!r}, failures={len(failures)}, "
            f"silver_publication_ready={silver.get('publication_ready')!r}"
        )
    payload = {
        "schema_version": 1,
        "published_at": datetime.now(timezone.utc).isoformat(),
        "run_id": manifest.get("run_id"),
        "manifest_path": str(manifest_path),
        "records": manifest.get("record_count", len(manifest.get("records") or [])),
    }
    current_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = current_path.with_suffix(current_path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp_path, current_path)
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--silver-manifest", type=Path, default=Path("data/silver/ana_agreements_catalog.manifest.json"))
    parser.add_argument("--current", type=Path, default=Path("data/bronze/ana_agreements_full/CURRENT"))
    args = parser.parse_args()
    print(json.dumps(publish(args.manifest, args.current, args.silver_manifest), ensure_ascii=False, indent=2))
