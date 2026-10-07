"""Compare codes extracted from verified recovery PDFs with import observations."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from pypdf import PdfReader


CODE_RE = re.compile(r"(?<!\d)(\d{4})[.\s-]?(\d{2})[.\s-]?(\d{2})(?:[.\s-]?(\d{2}))?(?:[.\s-]?(\d{2}))?(?!\d)")


def normalize(value: object) -> str | None:
    digits = re.sub(r"\D", "", str(value or ""))
    return digits if len(digits) >= 4 else None


def extract_codes(text: str) -> set[str]:
    return {"".join(part for part in match.groups() if part) for match in CODE_RE.finditer(text)}


def extract_code_evidence(text: str) -> list[tuple[str, str]]:
    """Return normalized codes with excerpts anchored to the raw PDF text."""
    evidence = []
    for match in CODE_RE.finditer(text):
        code = "".join(part for part in match.groups() if part)
        excerpt = " ".join(text[max(0, match.start() - 80):match.end() + 160].split())
        evidence.append((code, excerpt))
    return evidence


def import_codes(raw_root: Path) -> tuple[pd.DataFrame, set[str]]:
    root = raw_root / "data" / "raw" if (raw_root / "data" / "raw").exists() else raw_root
    source = next((root / "05_valor_importacion_por_descripcion_arancelaria_anual").glob("*.csv"), None)
    if source is None:
        raise FileNotFoundError("No se encontró el reporte 05 de importaciones")
    frames = []
    for frame in pd.read_csv(source, dtype=str, encoding="utf-8-sig", chunksize=100_000):
        frame = frame.rename(columns={"codigo": "hs_code", "ANNO": "observed_year", "textbox6": "description"})
        frame["hs_code"] = frame["hs_code"].map(normalize)
        frame["observed_year"] = pd.to_numeric(frame["observed_year"], errors="coerce").astype("Int64")
        frames.append(frame[["hs_code", "observed_year", "description"]].dropna(subset=["hs_code"]))
    data = pd.concat(frames, ignore_index=True).drop_duplicates()
    return data, set(data["hs_code"])


def build(recovery_root: Path, imports_root: Path, output: Path) -> dict:
    manifest_path = recovery_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    imports, observed = import_codes(imports_root)
    rows = []
    parse_errors = []
    for source in manifest["records"]:
        if source.get("status") != "downloaded" or not source.get("path", "").lower().endswith(".pdf"):
            continue
        pdf_path = Path(source["path"])
        try:
            for page_number, page in enumerate(PdfReader(str(pdf_path)).pages, start=1):
                text = page.extract_text() or ""
                for code, excerpt in extract_code_evidence(text):
                    rows.append({"hs_code": code, "chapter": code[:2], "source_id": source["source_id"],
                                 "source_url": source["url"], "source_sha256": source["sha256"],
                                 "source_file": str(pdf_path), "page_number": page_number,
                                 "evidence_excerpt": excerpt, "import_observed": code in observed,
                                 "evidence_type": "pdf_text", "observed_at": source["checked_at"]})
        except Exception as exc:
            parse_errors.append({"source_id": source["source_id"], "error": f"{type(exc).__name__}: {exc}"})
    result = pd.DataFrame(rows)
    output.mkdir(parents=True, exist_ok=True)
    parquet = output / "recovery_import_hs_comparison.parquet"
    result.to_parquet(parquet, index=False)
    digest = hashlib.sha256(parquet.read_bytes()).hexdigest()
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "source_manifest": str(manifest_path),
              "pdf_sources": sum(r.get("status") == "downloaded" and r.get("path", "").lower().endswith(".pdf") for r in manifest["records"]),
              "import_rows": len(imports), "import_distinct_codes": len(observed),
              "extracted_code_rows": len(result), "extracted_distinct_codes": int(result["hs_code"].nunique()) if not result.empty else 0,
              "codes_observed_in_imports": int(result.loc[result["import_observed"], "hs_code"].nunique()) if not result.empty else 0,
              "evidence_rows_with_page": int(result["page_number"].notna().sum()) if not result.empty else 0,
              "evidence_rows_with_excerpt": int(result["evidence_excerpt"].fillna("").str.len().gt(0).sum()) if not result.empty else 0,
              "evidence_coverage_complete": bool(not result.empty and result["page_number"].notna().all() and result["evidence_excerpt"].fillna("").str.len().gt(0).all()),
              "parse_errors": parse_errors, "sha256": digest, "raw_inputs_modified": False,
              "classification": "DERIVED_RECOVERY_SOURCE_COMPARISON"}
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--recovery-root", type=Path, default=Path("data/bronze/ana_recovery_sources"))
    parser.add_argument("--imports-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/gold/recovery_import_comparison"))
    args = parser.parse_args()
    print(json.dumps(build(args.recovery_root, args.imports_root, args.output), ensure_ascii=False, indent=2))
