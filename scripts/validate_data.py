"""
Data Validation CLI for Panama PortOps-AI v2.0
Validates datasets against the 5 Quality Gates and generates audit manifests.
Author: Desarrollado v1.0 Miguel Benítez - GNU GPL-3.0
"""

import sys
import argparse
from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.data.quality.quality_gates import DataQualityPipeline
from src.data.temporal_window import TemporalWindowManager
from src.data.catalog.manifest import DatasetManifest


def validate_file(file_path: Path) -> bool:
    """Validates a parquet or csv file against the 5 Quality Gates."""
    if not file_path.exists():
        print(f"Error: File '{file_path}' does not exist.")
        return False

    print(f"Validating dataset '{file_path.name}'...")
    if file_path.suffix == ".parquet":
        df = pd.read_parquet(file_path)
    elif file_path.suffix == ".csv":
        df = pd.read_csv(file_path)
    else:
        print(f"Unsupported file format: {file_path.suffix}")
        return False

    # Check temporal continuity
    date_col = "date" if "date" in df.columns else ("event_date" if "event_date" in df.columns else None)
    if date_col:
        tw = TemporalWindowManager.calculate_window_coverage(df, date_col=date_col)
        print(f"  Temporal Continuity: {tw.get('dynamic_summary')}")

    # Run Quality Gates
    req_cols = [c for c in ["date", "port", "value", "category"] if c in df.columns]
    passed, score, gate_results = DataQualityPipeline.run_all_gates(
        df=df,
        dataset_name=file_path.stem,
        required_cols=req_cols,
        target_cols=["value"] if "value" in df.columns else []
    )

    print(f"  Overall Quality Score: {score:.2f} ({'PASSED' if passed else 'FAILED'})")
    for gr in gate_results:
        status_sym = "[OK]" if gr["passed"] else "[VIOLATION]"
        print(f"    {status_sym} {gr['gate_name']} (Score: {gr['score']:.2f})")
        for v in gr["violations"][:3]:
            print(f"      - {v}")

    # Generate Manifest
    manifest = DatasetManifest.from_dataframe(
        df=df,
        dataset_id=file_path.stem,
        source_id="amp_port_traffic",
        layer="silver" if "silver" in str(file_path) else "gold",
        date_col=date_col or "date"
    )
    print(f"  Generated Manifest Content Hash: {manifest.content_hash[:16]}... (Rows: {manifest.row_count})")
    return passed


def main():
    parser = argparse.ArgumentParser(description="Panama PortOps-AI Data Quality Validator")
    parser.add_argument("--file", type=str, default="data/silver/fact_containers.parquet", help="Path to dataset to validate")
    args = parser.parse_args()

    target = ROOT_DIR / args.file
    success = validate_file(target)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
