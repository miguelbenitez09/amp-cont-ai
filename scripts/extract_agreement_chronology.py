"""Extract date evidence from downloaded agreement PDFs into a derived Gold artifact.

The extractor records literal date/year occurrences and page excerpts. It does
not infer legal validity, amendment status, or current applicability.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from pypdf import PdfReader


DATE_RE = re.compile(
    r"(?i)\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+de\s+[a-záéíóúñ]+\s+de\s+\d{4}|\d{4}-\d{2}-\d{2})\b"
)
YEAR_RE = re.compile(r"(?<!\d)(?:19|20)\d{2}(?!\d)")


def _excerpt(text: str, start: int, end: int) -> str:
    return " ".join(text[max(0, start - 90):end + 180].split())


def extract(manifest_path: Path, register_path: Path, output: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    register = json.loads(register_path.read_text(encoding="utf-8")) if register_path.exists() else {"records": []}
    by_url = {row.get("source_url"): row for row in register.get("records", []) if row.get("source_url")}
    rows: list[dict] = []
    errors: list[dict] = []
    for source in manifest.get("records", []):
        if source.get("status") != "downloaded" or not str(source.get("path", "")).lower().endswith(".pdf"):
            continue
        path = Path(source["path"])
        context = by_url.get(source.get("url"), {})
        try:
            for page_number, page in enumerate(PdfReader(str(path)).pages, start=1):
                text = page.extract_text() or ""
                matches = list(DATE_RE.finditer(text))
                if not matches:
                    matches = list(YEAR_RE.finditer(text))
                for match in matches:
                    token = match.group(0)
                    rows.append({
                        "source_id": source["source_id"], "source_url": source["url"],
                        "source_sha256": source.get("sha256"), "source_file": str(path),
                        "agreement_title": context.get("title"), "agreement_category": context.get("category"),
                        "page_number": page_number, "date_token": token,
                        "evidence_excerpt": _excerpt(text, match.start(), match.end()),
                        "extraction_type": "date_literal" if DATE_RE.fullmatch(token) else "year_literal",
                    })
        except Exception as exc:
            errors.append({"source_id": source.get("source_id"), "error": f"{type(exc).__name__}: {exc}"})
    frame = pd.DataFrame(rows)
    output.mkdir(parents=True, exist_ok=True)
    parquet = output / "agreement_chronology.parquet"
    frame.to_parquet(parquet, index=False)
    digest = hashlib.sha256(parquet.read_bytes()).hexdigest()
    report = {
        "schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": "DERIVED_AGREEMENT_CHRONOLOGY_LITERAL_EVIDENCE",
        "source_manifest": str(manifest_path), "register": str(register_path),
        "pdf_sources": sum(r.get("status") == "downloaded" and str(r.get("path", "")).lower().endswith(".pdf") for r in manifest.get("records", [])),
        "evidence_rows": len(frame), "distinct_sources": int(frame["source_id"].nunique()) if not frame.empty else 0,
        "rows_with_page": int(frame["page_number"].notna().sum()) if not frame.empty else 0,
        "rows_with_excerpt": int(frame["evidence_excerpt"].fillna("").str.len().gt(0).sum()) if not frame.empty else 0,
        "parse_errors": errors, "sha256": digest, "raw_inputs_modified": False,
        "legal_validity_inferred": False,
    }
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("data/bronze/ana_recovery_sources/manifest.json"))
    parser.add_argument("--register", type=Path, default=Path("data/gold/ana_agreements_recovery/source_register.json"))
    parser.add_argument("--output", type=Path, default=Path("data/gold/ana_agreements_recovery/chronology"))
    args = parser.parse_args()
    print(json.dumps(extract(args.manifest, args.register, args.output), ensure_ascii=False, indent=2))
