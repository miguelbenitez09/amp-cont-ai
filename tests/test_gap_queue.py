import json

import scripts.audit_gap_queue as audit_gap_queue
from src.governance.gap_queue import GapFinding, GapQueue


def finding(evidence=None):
    return GapFinding("RULE-1", "Gap", "runtime", "high", evidence or {"count": 0}, "MlopsAdmin", "Fix it")


def test_gap_queue_deduplicates_and_preserves_assignment(tmp_path):
    queue = GapQueue(tmp_path / "queue.json")
    first = queue.upsert([finding()])
    fingerprint = first["items"][0]["fingerprint"]
    queue.transition(fingerprint, "assigned", assignee="operator")
    second = queue.upsert([finding({"count": 1})])
    assert len(second["items"]) == 1
    assert second["items"][0]["assignee"] == "operator"
    assert second["items"][0]["occurrences"] == 2


def test_gap_queue_resolves_when_rule_no_longer_reproduces(tmp_path):
    queue = GapQueue(tmp_path / "queue.json")
    queue.upsert([finding()])
    payload = queue.upsert([])
    assert payload["items"][0]["status"] == "resolved"
    json.loads((tmp_path / "queue.json").read_text(encoding="utf-8"))


def test_optional_local_llm_runtimes_do_not_open_gaps_when_disabled(monkeypatch, tmp_path):
    monkeypatch.delenv("VLLM_ENABLED", raising=False)
    monkeypatch.delenv("VLLM_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_ENABLED", raising=False)
    monkeypatch.setattr(audit_gap_queue, "command_lines", lambda command: [])

    def offline_get(*args, **kwargs):
        raise audit_gap_queue.requests.RequestException("offline")

    monkeypatch.setattr(audit_gap_queue.requests, "get", offline_get)

    findings = audit_gap_queue.detect()
    rule_ids = {finding.rule_id for finding in findings}

    assert "RUNTIME-VLLM-NO-MODEL" not in rule_ids
    assert "RUNTIME-OLLAMA-NO-MODEL" not in rule_ids
