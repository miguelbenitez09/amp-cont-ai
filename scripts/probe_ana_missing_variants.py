"""Probe conservative URL variants for ANA failures without touching Bronze inputs."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import requests


def variants(url: str) -> list[str]:
    parts = urlsplit(url)
    candidates = [url]
    path = parts.path
    if not path.lower().endswith(".pdf"):
        candidates.extend([url + ".pdf", url + ".PDF"])
    candidates.append(url.replace("www.ana.gob.pa", "ana.gob.pa"))
    candidates.append(url.replace("www.ana.gob.pa", "www.ana.gob.pa"))
    candidates.append(url.replace("_", "-"))
    candidates.append(url.replace("-", "_"))
    if path.lower().endswith(".pdf"):
        candidates.append(url[:-4] + ".PDF")
    return list(dict.fromkeys(candidates))


def probe(staging_manifest: Path, output: Path) -> dict:
    manifest = json.loads(staging_manifest.read_text(encoding="utf-8"))
    session = requests.Session()
    session.headers["User-Agent"] = "amp-cont-ai/1.0 (read-only provenance probe)"
    rows = []
    for failure in manifest.get("failures", []):
        attempts = []
        for candidate in variants(failure["url"]):
            row = {"url": candidate}
            try:
                response = session.get(candidate, timeout=(10, 30), allow_redirects=True)
                row.update({"status_code": response.status_code, "final_url": response.url,
                            "content_type": response.headers.get("Content-Type", ""),
                            "is_pdf": response.content.startswith(b"%PDF-")})
            except Exception as exc:
                row["error"] = f"{type(exc).__name__}: {exc}"
            attempts.append(row)
        successful_pdf = next((a for a in attempts if a.get("status_code") == 200 and a.get("is_pdf")), None)
        codes = {a.get("status_code") for a in attempts}
        if successful_pdf:
            classification = "recovered_variant"
        elif 401 in codes or 403 in codes:
            classification = "access_restricted"
        elif 429 in codes:
            classification = "rate_limited"
        elif codes and codes.issubset({404, None}):
            classification = "resource_not_found_at_probed_variants"
        else:
            classification = "inconclusive_transport_or_server_error"
        rows.append({"record_id": failure["record_id"], "original_url": failure["url"], "attempts": attempts,
                     "successful_pdf": successful_pdf, "classification": classification})
    classifications = {}
    for row in rows:
        key = row["classification"]
        classifications[key] = classifications.get(key, 0) + 1
    result = {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
              "staging_manifest": str(staging_manifest), "raw_inputs_modified": False,
              "records": rows, "successful_variants": sum(r["successful_pdf"] is not None for r in rows),
              "classification_counts": classifications,
              "interpretation": "404 en todas las variantes probadas indica recurso no encontrado en esas rutas; no constituye evidencia de bloqueo por parte del servidor."}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--staging-manifest", type=Path, default=Path("data/bronze/ana_agreements_full/.staging/20260930T070226Z/manifest.json"))
    parser.add_argument("--output", type=Path, default=Path("data/gold/ana_missing_variant_probe.json"))
    args = parser.parse_args()
    print(json.dumps(probe(args.staging_manifest, args.output), ensure_ascii=False, indent=2))
