import hashlib
import json
from pathlib import Path


def test_live_ana_source_manifest_matches_bronze_provenance():
    live_path = Path("data/gold/ana_source_manifest_live.json")
    bronze_path = Path("data/bronze/ana_agreements_full/.staging/20260930T070226Z/manifest.json")
    live = live_path.read_bytes()
    bronze = json.loads(bronze_path.read_text(encoding="utf-8"))
    assert hashlib.sha256(live).hexdigest() == bronze["source_manifest_sha256"]
    assert live_path.exists()
    assert len(bronze["records"]) == 700
