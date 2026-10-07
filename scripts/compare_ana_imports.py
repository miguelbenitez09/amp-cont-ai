"""Build a derived comparison between ANA documents and import observations.

RAW inputs are read-only. Outputs are written under a separate Gold directory.
The comparison is deliberately evidence-limited: a code is marked as official
only when it is extracted from a validated downloaded document and linked to a
manifest record.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


CODE_RE = re.compile(r"(?<!\d)(\d{4})[.\s-]?(\d{2})[.\s-]?(\d{2})(?:[.\s-]?(\d{2}))?(?:[.\s-]?(\d{2}))?(?!\d)")


def normalize_code(value: object) -> str | None:
    digits = re.sub(r"\D", "", str(value or ""))
    return digits if len(digits) >= 4 else None


def extract_codes(text: str) -> set[str]:
    result: set[str] = set()
    for match in CODE_RE.finditer(text):
        groups = [g for g in match.groups() if g]
        result.add("".join(groups))
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_import_codes(raw_root: Path) -> pd.DataFrame:
    root = raw_root / "data" / "raw" if (raw_root / "data" / "raw").exists() else raw_root
    files = sorted((root / "05_valor_importacion_por_descripcion_arancelaria_anual").glob("*.csv"))
    if not files:
        raise FileNotFoundError("No se encontró el reporte 05 de importaciones")
    rows: list[pd.DataFrame] = []
    for frame in pd.read_csv(files[0], dtype=str, encoding="utf-8-sig", chunksize=100_000):
        frame = frame.rename(columns={"codigo": "hs_code", "CAPITULO": "chapter", "ANNO": "observed_year", "textbox6": "description"})
        required = {"hs_code", "chapter", "observed_year", "description"}
        if not required.issubset(frame.columns):
            raise ValueError(f"Faltan columnas en importaciones: {sorted(required - set(frame.columns))}")
        frame = frame[list(required)].copy()
        frame["hs_code"] = frame["hs_code"].map(normalize_code)
        frame["chapter"] = frame["chapter"].map(normalize_code)
        frame["observed_year"] = pd.to_numeric(frame["observed_year"], errors="coerce").astype("Int64")
        rows.append(frame.dropna(subset=["hs_code"]))
    return pd.concat(rows, ignore_index=True).drop_duplicates(["hs_code", "observed_year", "description"])


def build(ana_root: Path, imports_root: Path, output_root: Path) -> dict:
    current = ana_root / "CURRENT"
    if not current.exists():
        raise RuntimeError("No hay snapshot ANA completo publicado; no se genera comparación")
    run_id = current.read_text(encoding="utf-8").strip()
    snapshot = ana_root / run_id
    manifest_path = snapshot / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not manifest.get("complete"):
        raise RuntimeError("El manifiesto ANA no está completo")
    imports = _load_import_codes(imports_root)
    import_codes = set(imports["hs_code"].dropna())
    rows: list[dict] = []
    from pypdf import PdfReader
    for record in manifest["records"]:
        relative = record.get("relative_path")
        pdf = snapshot / relative if relative else None
        if not pdf or not pdf.exists():
            continue
        try:
            text = "\n".join(page.extract_text() or "" for page in PdfReader(str(pdf)).pages)
            codes = extract_codes(text)
            for code in sorted(codes):
                rows.append({"hs_code": code, "chapter": code[:2], "ana_record_id": record["record_id"],
                             "ana_title": record["title"], "ana_source_url": record["source_url"],
                             "document_sha256": record["document_sha256"], "evidence_file": str(relative),
                             "import_observed": code in import_codes, "evidence_type": "pdf_text"})
        except Exception as exc:
            rows.append({"hs_code": None, "ana_record_id": record["record_id"], "ana_title": record["title"],
                         "ana_source_url": record["source_url"], "document_sha256": record["document_sha256"],
                         "evidence_file": str(relative), "import_observed": False, "evidence_type": f"parse_error:{type(exc).__name__}"})
    output_root.mkdir(parents=True, exist_ok=True)
    result = pd.DataFrame(rows)
    parquet = output_root / "ana_imports_hs_comparison.parquet"
    result.to_parquet(parquet, index=False)
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "ana_run_id": run_id,
              "ana_records": len(manifest["records"]), "import_rows": len(imports),
              "import_distinct_codes": len(import_codes), "extracted_code_rows": len(result),
              "extracted_distinct_codes": int(result["hs_code"].dropna().nunique()) if not result.empty else 0,
              "codes_observed_in_imports": int(result.loc[result.get("import_observed", False) == True, "hs_code"].nunique()) if not result.empty else 0,
              "source_manifest_sha256": manifest.get("source_manifest_sha256"),
              "classification": "DERIVED_EVIDENCE_COMPARISON", "raw_inputs_modified": False,
              "sha256": _sha256(parquet)}
    (output_root / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ana-root", type=Path, default=Path("data/bronze/ana_agreements_full"))
    parser.add_argument("--imports-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/gold/ana_imports_comparison"))
    args = parser.parse_args()
    print(json.dumps(build(args.ana_root, args.imports_root, args.output), ensure_ascii=False, indent=2))
