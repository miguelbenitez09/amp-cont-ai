"""Run the reproducible local validation profile for AMP-CONT-AI.

This runner intentionally reports unavailable external services instead of
pretending that Wazuh, Redis, MinIO, PostgreSQL or an LLM runtime passed.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def check_health(url: str) -> dict:
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/health", timeout=5) as response:
            payload = json.load(response)
        return {"name": "api_health", "status": "passed", "details": payload}
    except Exception as exc:  # validation must preserve the exact failure
        return {"name": "api_health", "status": "failed", "details": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8001")
    parser.add_argument("--pytest", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("data/gold/validation/latest.json"))
    args = parser.parse_args()
    checks = [check_health(args.base_url)]
    if args.pytest:
        result = subprocess.run([sys.executable, "-m", "pytest", "-q"], text=True, capture_output=True)
        checks.append({"name": "pytest", "status": "passed" if result.returncode == 0 else "failed", "details": result.stdout[-4000:] + result.stderr[-1000:]})
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "checks": checks}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if all(check["status"] == "passed" for check in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
