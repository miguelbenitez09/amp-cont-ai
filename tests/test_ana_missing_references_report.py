import json
from pathlib import Path


def test_ana_missing_references_report_is_reviewable_and_non_destructive():
    report = json.loads(Path("data/gold/ana_missing_references_report.json").read_text(encoding="utf-8"))
    assert report["record_count"] == 17
    assert report["raw_inputs_modified"] is False
    assert report["classification_counts"] == {"resource_not_found_at_probed_variants": 17}
    assert all(item["source_url"] and item["manual_review_label"] for item in report["records"])
