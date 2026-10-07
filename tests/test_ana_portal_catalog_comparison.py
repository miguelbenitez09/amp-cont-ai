import json
from pathlib import Path


def test_ana_portal_catalog_comparison_is_explicit_about_uncertainty() -> None:
    report = json.loads(Path("data/gold/ana_portal_catalog_comparison.json").read_text(encoding="utf-8"))
    assert report["raw_inputs_modified"] is False
    assert report["query_mode"] == "code/import/sequential"
    assert len(report["rows"]) >= 1
    assert set(report["summary"]) == {"exact_code_match", "exact_code_description_mismatch", "prefix_or_description_result", "not_found", "unavailable"}
