import json
from pathlib import Path


def test_ana_silver_catalog_preserves_incomplete_publication_boundary() -> None:
    metadata = json.loads(Path("data/silver/ana_agreements_catalog.manifest.json").read_text(encoding="utf-8"))
    assert metadata["records"] == 700
    assert metadata["downloaded_records"] == 683
    assert metadata["failed_records"] == 17
    assert metadata["source_manifest_complete"] is False
    assert metadata["publication_ready"] is False
    assert metadata["raw_inputs_modified"] is False
