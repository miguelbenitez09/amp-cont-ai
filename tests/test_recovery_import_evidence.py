"""Regression checks for document/page-level evidence in derived comparisons."""
from __future__ import annotations

import json
from pathlib import Path


def test_recovery_comparison_has_complete_page_evidence() -> None:
    report_path = Path("data/gold/recovery_import_comparison/report.json")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["raw_inputs_modified"] is False
    assert report["pdf_sources"] >= 1
    assert report["extracted_code_rows"] > 0
    assert report["evidence_coverage_complete"] is True
    assert report["evidence_rows_with_page"] == report["extracted_code_rows"]
    assert report["evidence_rows_with_excerpt"] == report["extracted_code_rows"]


def test_ana_recovery_register_keeps_uncertainty_and_agreement_type() -> None:
    register = json.loads(Path("data/gold/ana_agreements_recovery/source_register.json").read_text(encoding="utf-8"))
    assert len(register["records"]) == 17
    assert all(row.get("category") for row in register["records"])
    statuses = {row["status"] for row in register["records"]}
    assert "candidate_alternative_source" in statuses
    assert "exact_alternative_source" in statuses
    assert sum(row["status"] == "exact_alternative_source" for row in register["records"]) == 9
    assert "related_source_needs_manual_confirmation" not in statuses
    assert "no_public_alternative_located" not in statuses
    assert register["raw_inputs_modified"] is False


def test_ana_missing_variant_probe_found_no_original_file() -> None:
    probe = json.loads(Path("data/gold/ana_missing_variant_probe.json").read_text(encoding="utf-8"))
    assert len(probe["records"]) == 17
    assert probe["successful_variants"] == 0
    assert probe["classification_counts"]["resource_not_found_at_probed_variants"] >= 1
    assert "no encontrado" in probe["interpretation"]
    assert probe["raw_inputs_modified"] is False


def test_agreement_chronology_is_literal_page_evidence() -> None:
    report = json.loads(Path("data/gold/ana_agreements_recovery/chronology/report.json").read_text(encoding="utf-8"))
    assert report["evidence_rows"] > 0
    assert report["rows_with_page"] == report["evidence_rows"]
    assert report["rows_with_excerpt"] == report["evidence_rows"]
    assert report["legal_validity_inferred"] is False
    assert report["raw_inputs_modified"] is False
