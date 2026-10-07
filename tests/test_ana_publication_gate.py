import pytest

from scripts.publish_ana_snapshot import publish


def test_publication_gate_refuses_incomplete_snapshot(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"run_id":"run-1","complete":false,"failures":[{"url":"x"}]}', encoding="utf-8")
    silver = tmp_path / "silver.json"
    silver.write_text('{"publication_ready":false}', encoding="utf-8")
    with pytest.raises(RuntimeError, match="Refusing publication"):
        publish(manifest, tmp_path / "CURRENT", silver)
    assert not (tmp_path / "CURRENT").exists()
