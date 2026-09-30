"""Assemble an allowlisted source archive without publishing it."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
try:
    from scripts.verify_public_release import audit
except ModuleNotFoundError:
    from verify_public_release import audit

def build(root: Path, destination: Path) -> dict:
    root, destination = root.resolve(), destination.resolve()
    if destination.exists():
        raise FileExistsError("Destination exists; choose a new versioned path")
    report = audit(root)
    if report["violations"]:
        raise ValueError(f"Public boundary blocked: {report['violations']}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED) as archive:
            created = True
            for entry in report["files"]:
                data = (root / entry["path"]).read_bytes()
                if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                    raise ValueError(f"File changed during build: {entry['path']}")
                archive.writestr(entry["path"], data)
            archive.writestr("PUBLIC_MANIFEST.json", json.dumps(report, indent=2))
    except Exception:
        if created:
            destination.unlink(missing_ok=True)
        raise
    return report

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = build(args.root, args.output)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Release blocked: {exc}\n")
    print(f"Built {len(result['files'])} approved files: {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
