"""Normalize an ANA Bronze manifest into a provenance-only Silver catalog.

This stage never copies, rewrites, or publishes documents. It materializes the
catalog relationships and download outcomes so incomplete runs remain useful
for analysis without being mistaken for a complete CURRENT snapshot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def build(staging_dir: Path, recovery_register: Path, output: Path) -> dict:
    manifest = json.loads((staging_dir / "manifest.json").read_text(encoding="utf-8"))
    recovery = json.loads(recovery_register.read_text(encoding="utf-8")) if recovery_register.exists() else {"records": []}
    recovery_by_id = {row["record_id"]: row for row in recovery.get("records", [])}
    failures_by_url = {row["ana_url"]: row for row in recovery.get("records", [])}
    rows = []
    for row in manifest.get("records", []):
        recovery_row = recovery_by_id.get(row["record_id"]) or failures_by_url.get(row.get("source_url"), {})
        rows.append({
            "record_id": row.get("record_id"),
            "title": row.get("title"),
            "category": row.get("category"),
            "subcategory": row.get("subcategory"),
            "source_url": row.get("source_url"),
            "source_link": row.get("source_link"),
            "portal_status": row.get("portal_status"),
            "downloaded": bool(row.get("downloaded")),
            "document_sha256": row.get("document_sha256"),
            "relative_path": row.get("relative_path"),
            "recovery_status": recovery_row.get("status"),
            "recovery_source_url": recovery_row.get("source_url"),
            "recovery_source_name": recovery_row.get("source_name"),
            "observed_at": manifest.get("observed_at"),
        })
    frame = pd.DataFrame(rows)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output, index=False)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    built_at = datetime.now(timezone.utc).isoformat()
    metadata = {
        "schema_version": 1,
        "artifact": str(output),
        "source_manifest": str(staging_dir / "manifest.json"),
        "source_run_id": manifest.get("run_id"),
        "source_manifest_complete": bool(manifest.get("complete")),
        "publication_ready": bool(manifest.get("complete")) and not manifest.get("failures"),
        "records": len(frame),
        "downloaded_records": int(frame["downloaded"].sum()) if not frame.empty else 0,
        "failed_records": int((~frame["downloaded"]).sum()) if not frame.empty else 0,
        "with_recovery_relation": int(frame["recovery_status"].notna().sum()) if not frame.empty else 0,
        "sha256": digest,
        "raw_inputs_modified": False,
        "built_at": built_at,
    }
    output.with_suffix(".manifest.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--staging-dir", type=Path, required=True)
    parser.add_argument("--recovery-register", type=Path, default=Path("data/gold/ana_agreements_recovery/source_register.json"))
    parser.add_argument("--output", type=Path, default=Path("data/silver/ana_agreements_catalog.parquet"))
    args = parser.parse_args()
    print(json.dumps(build(args.staging_dir, args.recovery_register, args.output), ensure_ascii=False, indent=2))
