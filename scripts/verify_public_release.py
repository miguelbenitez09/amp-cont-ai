"""Audit selected public files only; this does not certify Git history."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

POLICY = "brain/releases/PUBLIC_FILE_ALLOWLIST.yaml"
FORBIDDEN_PARTS = {".git", ".env", "private", "raw", "bronze_original", "sessions", "cookies"}
FORBIDDEN_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".csv", ".parquet", ".xlsx", ".pkl", ".joblib", ".pt", ".pth", ".bin", ".pem", ".key", ".zip"}
SECRET = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16}")

def load_policy(root: Path) -> dict:
    policy = json.loads((root / POLICY).read_text(encoding="utf-8"))
    if policy.get("version") != 2 or not policy.get("include"):
        raise ValueError("Unsupported or empty public file policy")
    for pattern in policy["include"] + policy.get("required", []):
        path = PurePosixPath(pattern)
        if path.is_absolute() or ".." in path.parts or "\\" in pattern or ":" in pattern:
            raise ValueError("Public file policy contains an unsafe path")
    return policy

def selected_files(root: Path) -> list[Path]:
    root = root.resolve()
    policy = load_policy(root)
    found = set()
    for pattern in policy["include"]:
        for candidate in root.glob(pattern):
            relative = candidate.relative_to(root)
            if any(part in {"__pycache__", ".pytest_cache"} for part in relative.parts):
                continue
            for parent in [candidate, *candidate.parents]:
                if parent == root:
                    break
                if parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()):
                    raise ValueError(f"Linked path is not publishable: {relative}")
            if not candidate.resolve().is_relative_to(root):
                raise ValueError(f"Path escapes root: {relative}")
            if candidate.is_file():
                found.add(candidate)
    for required in policy.get("required", []):
        if root / required not in found:
            raise ValueError(f"Required public file missing: {required}")
    return sorted(found)

def inspect_file(path: Path, relative: str, max_bytes: int) -> list[str]:
    errors = []
    if any(part in FORBIDDEN_PARTS for part in PurePosixPath(relative.lower()).parts) or "scraper" in relative.lower():
        errors.append("private path")
    if path.suffix.lower() in FORBIDDEN_SUFFIXES:
        errors.append("data, state or binary artifact")
    if path.name.startswith(".env") and path.name != ".env.example":
        errors.append("environment secrets")
    if path.stat().st_size > max_bytes:
        return errors + ["exceeds public source size limit"]
    data = path.read_bytes()
    if path.name == "logo.png" and relative.startswith("src/serving/static/framework/"):
        return errors
    try:
        content = data.decode("utf-8")
    except UnicodeDecodeError:
        return errors + ["non-text payload"]
    if b"\x00" in data:
        errors.append("binary payload")
    if SECRET.search(content):
        errors.append("credential signature")
    if re.search(r"(?:from|import)\s+src\.(?:data|serving\.api|platform)\b", content):
        errors.append("legacy runtime dependency")
    if path.name == ".env.example":
        for line in content.splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                if re.search(r"PASSWORD|TOKEN|SECRET|API_KEY", key, re.I) and value.strip():
                    errors.append("nonempty example secret")
    return errors

def audit(root: Path) -> dict:
    root = root.resolve()
    policy = load_policy(root)
    violations, manifest = {}, []
    for path in selected_files(root):
        relative = path.relative_to(root).as_posix()
        errors = inspect_file(path, relative, policy.get("max_file_bytes", 2000000))
        if errors:
            violations[relative] = errors
        manifest.append({"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size})
    return {"violations": violations, "files": manifest, "scope": "selected artifact only; Git history not certified"}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        report = audit(args.root)
    except (ValueError, OSError) as exc:
        print(f"PUBLIC_RELEASE=BLOCKED: {exc}")
        return 1
    print(json.dumps(report, indent=2))
    return int(bool(report["violations"]))

if __name__ == "__main__":
    raise SystemExit(main())
