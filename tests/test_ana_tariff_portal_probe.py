import json
from pathlib import Path


def test_ana_tariff_portal_probe_is_read_only_and_traceable() -> None:
    report = json.loads(Path("data/gold/ana_tariff_portal_probe.json").read_text(encoding="utf-8"))
    assert report["query"]["rbtn_codehs_word"] == "code"
    assert report["query"]["rbtn_imp_exp"] == "imp"
    assert report["status"] in {"response", "timeout_or_transport_error"}
    if report["status"] == "response":
        assert report["products"]
        assert report["products"][0]["hs12"] == "271019210000"
        assert "diésel" in report["products"][0]["description"]
