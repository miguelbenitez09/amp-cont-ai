"""CLI for the ANA agreements Lakehouse ingestion."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.data.scrapers.ana_agreements_scraper import DEFAULT_MANIFEST_URL, sync


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/bronze/ana_agreements"))
    parser.add_argument("--manifest-url", default=DEFAULT_MANIFEST_URL)
    parser.add_argument("--discover-only", action="store_true")
    parser.add_argument("--min-delay", type=float, default=1.5)
    parser.add_argument("--max-delay", type=float, default=5.0)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--resume-run-id", help="resume an existing .staging/<run_id> checkpoint")
    args = parser.parse_args()
    result = sync(args.output, manifest_url=args.manifest_url, download=not args.discover_only,
                  min_delay=args.min_delay, max_delay=args.max_delay, max_attempts=args.max_attempts,
                  workers=args.workers, resume_run_id=args.resume_run_id)
    print(json.dumps({k: result[k] for k in ("run_id", "record_count", "unique_documents", "complete", "failures")}, ensure_ascii=False, indent=2))
    return 0 if result["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
