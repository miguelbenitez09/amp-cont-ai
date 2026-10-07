"""
Panama PortOps Lakehouse Sanitizer & Anonymizer Pipeline (Silver Layer)
Transforms raw foreign trade, customs declarations (ANA), and port data into decontaminated,
anonymized Parquet tables compliant with Ley 81 de 2019 de la República de Panamá.

Author: Ing. Miguel Antonio Benítez González (UTP)
License: GNU General Public License v3.0 (GPL-3.0) with Section 7 Mandatory Attribution
Version: v2.0.0
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.privacy.anonymizer import PanamaDataAnonymizerEngine

RAW_DIR = PROJECT_ROOT / "data" / "raw"
SILVER_DIR = PROJECT_ROOT / "data" / "silver"
SILVER_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_customs_declarations(
    raw_csv_path: Path,
    output_parquet: Path,
    sample_limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Sanitizes raw Customs declarations (ANA):
    - Strips/Hashes corporate consignee (CONSIGNATARIO) with HMAC-SHA256
    - Cleans numeric columns (VALOR_CIF, VALOR_FOB, IMPUESTO_IMPORTACION, ITBMS)
    - Normalizes HS codes (INCISO_ARANCELARIO)
    - Writes to Parquet Snappy
    """
    print(f"[INFO] Processing customs declarations from: {raw_csv_path}")
    if not raw_csv_path.exists():
        print(f"[WARN] File not found: {raw_csv_path}")
        return {"status": "skipped", "reason": "not_found"}

    # Read CSV with separator detection (semicolon or comma)
    try:
        df = pd.read_csv(raw_csv_path, sep=";", encoding="utf-8-sig", nrows=sample_limit, low_memory=False)
    except Exception:
        try:
            df = pd.read_csv(raw_csv_path, sep=";", encoding="latin-1", nrows=sample_limit, low_memory=False)
        except Exception:
            df = pd.read_csv(raw_csv_path, sep=",", encoding="utf-8-sig", nrows=sample_limit, low_memory=False)

    # Normalize column names: strip whitespace, BOM, accents and lowercase
    import re
    import unicodedata
    def clean_col(name: str) -> str:
        s = unicodedata.normalize('NFKD', str(name)).encode('ASCII', 'ignore').decode('utf-8')
        s = re.sub(r'[^a-zA-Z0-9_]+', '_', s.lower()).strip('_')
        return s

    df.columns = [clean_col(c) for c in df.columns]

    total_rows = len(df)
    print(f"[INFO] Loaded {total_rows} raw records.")

    # Apply Anonymization Engine on sample
    records = df.head(100).to_dict(orient="records")
    cert = PanamaDataAnonymizerEngine.execute_ordered_pipeline(
        dataset_name=raw_csv_path.name,
        sample_records=records
    )

    # 1. Anonymize CONSIGNATARIO
    if "consignatario" in df.columns:
        df["consignatario_hash"] = df["consignatario"].apply(PanamaDataAnonymizerEngine.hash_token)
        df.drop(columns=["consignatario"], inplace=True)

    # 2. Clean numeric strings
    for col in ["valor_cif", "valor_fob", "valor_flete", "valor_seguro", "total_a_pagar", "total_impuestos", "peso_bruto", "peso_neto", "cantidad"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "").str.strip(), errors="coerce").fillna(0.0)

    # 3. Clean HS codes
    if "inciso_arancelario" in df.columns:
        df["inciso_arancelario"] = df["inciso_arancelario"].astype(str).str.replace('="', '').str.replace('"', '').str.strip()

    # 4. Save to Silver Parquet
    df.to_parquet(output_parquet, engine="pyarrow", compression="snappy", index=False)
    print(f"[SUCCESS] Saved {len(df)} sanitized records to: {output_parquet}")

    # Generate Manifest
    file_bytes = output_parquet.read_bytes()
    sha256 = hashlib.sha256(file_bytes).hexdigest()
    manifest = {
        "dataset_name": output_parquet.name,
        "source": str(raw_csv_path),
        "records_count": len(df),
        "columns": list(df.columns),
        "sha256": sha256,
        "format": "parquet",
        "compression": "snappy",
        "compliance": "Ley 81 de 2019 de la Republica de Panama",
        "anonymization": "HMAC-SHA256 salted hashes on corporate identifiers",
        "author": "Ing. Miguel Antonio Benitez Gonzalez (UTP)",
    }

    manifest_path = output_parquet.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"status": "success", "manifest": manifest, "cert": cert["audit_certificate"]}


def main():
    print("=" * 80)
    print(" Panama PortOps-AI Lakehouse Silver Sanitizer (v2.0)")
    print(" Author: Ing. Miguel Antonio Benítez González (UTP)")
    print("=" * 80)

    # Example: Check for aduanas in downloads folder or data/raw
    aduanas_path = Path(r"C:\Users\mbeni\Downloads\datasets_aduanas\2020\IMP_20260927_003408.csv")
    if aduanas_path.exists():
        output = SILVER_DIR / "customs_imports_2020_silver.parquet"
        # Process a representative sample if file is massive
        res = sanitize_customs_declarations(aduanas_path, output, sample_limit=50000)
        print("[RESULT]", res["status"])
    else:
        print("[INFO] Aduanas raw file not found at expected location, checking data/raw...")


if __name__ == "__main__":
    main()
