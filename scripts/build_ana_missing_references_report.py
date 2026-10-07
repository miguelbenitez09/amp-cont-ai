"""Build a reviewable report for ANA references that could not be downloaded.

The report is derived from Bronze metadata and the non-destructive variant probe.
It never edits or replaces Bronze documents.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bronze-manifest", type=Path, required=True)
    parser.add_argument("--variant-probe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    bronze = json.loads(args.bronze_manifest.read_text(encoding="utf-8"))
    probe = json.loads(args.variant_probe.read_text(encoding="utf-8"))
    failures = {item["record_id"]: item for item in bronze.get("failures", [])}
    records = {item["record_id"]: item for item in bronze.get("records", [])}
    probed = {item["record_id"]: item for item in probe.get("records", [])}

    items = []
    for record_id, failure in failures.items():
        record = records.get(record_id, {})
        evidence = probed.get(record_id, {})
        classification = evidence.get("classification", "inconclusive")
        items.append(
            {
                "record_id": record_id,
                "category": record.get("category"),
                "subcategory": record.get("subcategory"),
                "help_category": record.get("help_category"),
                "title": record.get("title"),
                "portal_status": record.get("portal_status"),
                "source_url": record.get("source_url"),
                "original_error": failure.get("error"),
                "classification": classification,
                "probed_variants": len(evidence.get("attempts", [])),
                "successful_variant": evidence.get("successful_pdf"),
                "manual_review_label": (
                    "recurso no localizado en las variantes oficiales probadas"
                    if classification == "resource_not_found_at_probed_variants"
                    else "requiere revisión manual"
                ),
                "interpretation": (
                    "El portal lo marca como referencia activa, pero el recurso no respondió "
                    "en la URL original ni en sus variantes de dominio/ruta/extensión. Esto "
                    "no prueba derogación ni bloqueo; conservar como referencia histórica no localizada."
                    if classification == "resource_not_found_at_probed_variants"
                    else "La evidencia de transporte no permite concluir disponibilidad; revisar manualmente."
                ),
            }
        )

    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_manifest": str(args.bronze_manifest),
        "variant_probe": str(args.variant_probe),
        "raw_inputs_modified": False,
        "record_count": len(items),
        "classification_counts": {
            key: sum(item["classification"] == key for item in items)
            for key in sorted({item["classification"] for item in items})
        },
        "records": items,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "record_count": len(items), "raw_inputs_modified": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
