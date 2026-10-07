"""Build a searchable historical HS catalog from INEC import report 05.

The source is intentionally passed as an argument.  This keeps private/raw
acquisitions outside the repository while producing a small, versioned Silver
artifact used by the serving API.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def _find_report(raw_root: Path) -> Path:
    raw_root = raw_root / "data" / "raw" if (raw_root / "data" / "raw").exists() else raw_root
    matches = sorted((raw_root / "05_valor_importacion_por_descripcion_arancelaria_anual").glob("*.csv"))
    if not matches:
        raise FileNotFoundError("No se encontró el reporte 05 de INEC")
    return matches[0]


def build(raw_root: Path, output: Path) -> dict:
    source = _find_report(raw_root)
    rows: list[pd.DataFrame] = []
    for frame in pd.read_csv(source, dtype=str, chunksize=100_000, encoding="utf-8-sig"):
        frame = frame.rename(columns={"codigo": "hs_code", "textbox6": "description", "CAPITULO": "chapter", "ANNO": "observed_year"})
        required = ["hs_code", "description", "chapter", "observed_year"]
        missing = [column for column in required if column not in frame]
        if missing:
            raise ValueError(f"El reporte 05 no contiene columnas requeridas: {missing}")
        frame = frame[required].dropna(subset=["hs_code", "description"])
        frame["hs_code"] = frame["hs_code"].str.replace(r"\D", "", regex=True)
        frame["description"] = frame["description"].str.replace(r"\s+", " ", regex=True).str.strip()
        frame["observed_year"] = pd.to_numeric(frame["observed_year"], errors="coerce").astype("Int64")
        frame = frame[(frame.hs_code.str.len() >= 6) & frame.description.ne("")]
        rows.append(frame)
    data = pd.concat(rows, ignore_index=True).drop_duplicates(["hs_code", "description", "observed_year"])
    data["hs_code_6"] = data.hs_code.str[:6]
    data["hs_code_panama"] = data.hs_code
    data["classification_system"] = "INEC comercio exterior; descripción histórica observada"
    data["source_type"] = "historical_trade_observation"
    data["source_file"] = "INEC Comercio Exterior, reporte 05"
    # ANNO is an observation year from the trade report, not legal validity.
    data["observation_type"] = "historical_trade_observation"
    data["effective_from"] = None
    data["effective_to"] = None
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    output.parent.mkdir(parents=True, exist_ok=True)
    data.to_parquet(output, index=False)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    manifest = {
        "artifact": str(output), "source": str(source), "rows": int(len(data)),
        "distinct_codes": int(data.hs_code.nunique()), "sha256": digest,
        "classification": "FACT_OBSERVED_DESCRIPTION_ONLY", "built_at": data.updated_at.iloc[0],
        "observed_year_min": int(data.observed_year.min()) if data.observed_year.notna().any() else None,
        "observed_year_max": int(data.observed_year.max()) if data.observed_year.notna().any() else None,
    }
    output.with_suffix(".manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--imports-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/silver/dim_tariff_historical.parquet"))
    args = parser.parse_args()
    print(json.dumps(build(args.imports_root, args.output), ensure_ascii=False, indent=2))
