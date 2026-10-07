"""Persistent, deterministic queue for engineering and governance gaps."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


VALID_STATES = {"open", "assigned", "in_progress", "blocked", "resolved", "verified", "accepted_risk"}
VALID_SEVERITIES = {"critical", "high", "medium", "low", "info"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class GapFinding:
    rule_id: str
    title: str
    category: str
    severity: str
    evidence: Dict[str, Any]
    owner_role: str
    remediation: str
    source: str = "automated_audit"
    fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        if self.severity not in VALID_SEVERITIES:
            raise ValueError(f"Invalid severity: {self.severity}")
        stable = json.dumps({"rule_id": self.rule_id, "category": self.category}, sort_keys=True)
        object.__setattr__(self, "fingerprint", hashlib.sha256(stable.encode("utf-8")).hexdigest()[:20])


class GapQueue:
    """Upserts findings without losing status, assignee, history, or evidence."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": "1.0", "updated_at": None, "items": []}
        with self.path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        payload.setdefault("items", [])
        return payload

    def _save(self, payload: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        with temp.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, self.path)

    def upsert(self, findings: Iterable[GapFinding]) -> Dict[str, Any]:
        payload = self.load()
        now = utc_now()
        existing = {item["fingerprint"]: item for item in payload["items"]}
        seen = set()
        for finding in findings:
            seen.add(finding.fingerprint)
            current = existing.get(finding.fingerprint)
            if current:
                current.update({
                    "title": finding.title,
                    "category": finding.category,
                    "severity": finding.severity,
                    "evidence": finding.evidence,
                    "owner_role": finding.owner_role,
                    "remediation": finding.remediation,
                    "source": finding.source,
                    "last_seen_at": now,
                    "occurrences": int(current.get("occurrences", 0)) + 1,
                })
                if current.get("status") in {"resolved", "verified"}:
                    current["status"] = "open"
                    current.setdefault("history", []).append({"at": now, "event": "reopened_by_audit"})
            else:
                item = asdict(finding)
                item.update({
                    "status": "open",
                    "assignee": None,
                    "first_seen_at": now,
                    "last_seen_at": now,
                    "occurrences": 1,
                    "history": [{"at": now, "event": "detected"}],
                })
                payload["items"].append(item)

        for item in payload["items"]:
            if item["fingerprint"] not in seen and item.get("status") in {"open", "assigned", "in_progress"}:
                item["status"] = "resolved"
                item.setdefault("history", []).append({"at": now, "event": "not_reproduced_by_audit"})
        payload["updated_at"] = now
        self._save(payload)
        return payload

    def transition(self, fingerprint: str, status: str, assignee: Optional[str] = None, note: str = "") -> Dict[str, Any]:
        if status not in VALID_STATES:
            raise ValueError(f"Invalid status: {status}")
        payload = self.load()
        for item in payload["items"]:
            if item["fingerprint"] == fingerprint:
                item["status"] = status
                if assignee is not None:
                    item["assignee"] = assignee
                item.setdefault("history", []).append({"at": utc_now(), "event": "transition", "status": status, "note": note})
                payload["updated_at"] = utc_now()
                self._save(payload)
                return item
        raise KeyError(f"Unknown gap fingerprint: {fingerprint}")
