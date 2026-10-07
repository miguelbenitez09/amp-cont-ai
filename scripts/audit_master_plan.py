"""Audit evidence for the nine MLOps phases described in PLAN_MAESTRO."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def audit(root: Path) -> dict:
    checks = [
        ("data_acquisition", "ANA Bronze manifest", root / "data/bronze/ana_agreements_full/.staging/20260930T070226Z/manifest.json"),
        ("data_engineering", "ANA Silver catalog", root / "data/silver/ana_agreements_catalog.manifest.json"),
        ("data_quality", "quality test suite", root / "tests/test_quality.py"),
        ("feature_engineering", "feature catalog implementation", root / "src/data"),
        ("training", "training scripts", root / "scripts/train.py"),
        ("evaluation", "benchmark endpoint", root / "src/serving/api.py"),
        ("registry", "model registry implementation", root / "src/models/registry"),
        ("deployment", "CI workflow", root / ".github/workflows/ci.yml"),
        ("monitoring_governance", "telemetry endpoint", root / "src/serving/v1_router.py"),
    ]
    phases = []
    for phase, evidence, path in checks:
        exists = path.exists()
        phases.append({"phase": phase, "evidence": evidence, "path": str(path), "artifact_present": exists})
    validation_path = root / "data/gold/validation/latest.json"
    validation = None
    if validation_path.exists():
        try:
            validation = json.loads(validation_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            validation = None
    checks_by_name = {item.get("name"): item for item in (validation or {}).get("checks", [])}
    runtime_evidence = {
        "path": str(validation_path),
        "available": validation is not None,
        "status": checks_by_name.get("api_health", {}).get("status", "missing"),
    }
    quality_evidence = {
        "path": str(validation_path),
        "available": validation is not None,
        "status": checks_by_name.get("pytest", {}).get("status", "missing"),
    }
    bronze_manifest = root / "data/bronze/ana_agreements_full/.staging/20260930T070226Z/manifest.json"
    silver_manifest = root / "data/silver/ana_agreements_catalog.manifest.json"
    missing_report_path = root / "data/gold/ana_missing_references_report.json"
    bronze_complete = False
    silver_publishable = False
    if bronze_manifest.exists():
        try:
            bronze_complete = bool(json.loads(bronze_manifest.read_text(encoding="utf-8")).get("complete"))
        except (OSError, json.JSONDecodeError):
            bronze_complete = False
    if silver_manifest.exists():
        try:
            silver_publishable = bool(json.loads(silver_manifest.read_text(encoding="utf-8")).get("publication_ready"))
        except (OSError, json.JSONDecodeError):
            silver_publishable = False
    missing_references = {"path": str(missing_report_path), "available": False, "records": 0, "classification_counts": {}}
    if missing_report_path.exists():
        try:
            report = json.loads(missing_report_path.read_text(encoding="utf-8"))
            missing_references = {
                "path": str(missing_report_path),
                "available": True,
                "records": int(report.get("record_count") or 0),
                "classification_counts": report.get("classification_counts") or {},
                "raw_inputs_modified": bool(report.get("raw_inputs_modified", False)),
            }
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
    closure_ready = (
        all(row["artifact_present"] for row in phases)
        and runtime_evidence["status"] == "passed"
        and quality_evidence["status"] == "passed"
        and bronze_complete
        and silver_publishable
    )
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "phases": phases,
        "artifact_coverage_complete": all(row["artifact_present"] for row in phases),
        "runtime_evidence": runtime_evidence,
        "quality_evidence": quality_evidence,
        "bronze_complete": bronze_complete,
        "silver_publishable": silver_publishable,
        "missing_references": missing_references,
        "plan_phase_closure_requires_runtime_and_quality_evidence": True,
        "plan_phase_closure_ready": closure_ready,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("data/gold/master_plan_audit.json"))
    args = parser.parse_args()
    result = audit(args.root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
