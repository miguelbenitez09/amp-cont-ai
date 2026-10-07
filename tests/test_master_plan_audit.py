import json
from pathlib import Path


def test_master_plan_audit_has_evidence_for_all_nine_phases() -> None:
    report = json.loads(Path("data/gold/master_plan_audit.json").read_text(encoding="utf-8"))
    assert len(report["phases"]) == 9
    assert report["artifact_coverage_complete"] is True
    assert report["plan_phase_closure_requires_runtime_and_quality_evidence"] is True
    assert report["runtime_evidence"]["status"] == "passed"
    assert report["quality_evidence"]["status"] == "passed"
    assert report["bronze_complete"] is False
    assert report["silver_publishable"] is False
    assert report["plan_phase_closure_ready"] is False
