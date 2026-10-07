"""Download official replacement/reference sources into a separate Bronze area."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests


SOURCES = [
    ("ana_official_tariff_current", "https://www.ana.gob.pa/w_ana/images/ANA_pdf/arancel/arancel_nacional_aplicado.pdf", "official_tariff_reference"),
    ("ana_interactive_tariff_portal", "https://aranceles.ana.gob.pa/", "official_tariff_repository"),
    ("mici_bilateral_index", "https://mici.gob.pa/onci-acuerdos-comerciales-bilaterales/", "related_repository"),
    ("mici_panama_chile", "https://mici.gob.pa/onci-acuerdos-bilaterales-panama-chile/", "related_repository"),
    ("mici_panama_cuba", "https://mici.gob.pa/onci-acuerdos-bilaterales-panama-cuba/", "related_repository"),
    ("mici_panama_cuba_text", "https://mici.gob.pa/wp-content/uploads/2022/06/TextoNormativo_acuerdo-de-alcance-parcial-entre-la-panama-y-la-republica-de-cuba.pdf", "exact_alternative"),
    ("mici_panama_chile_explanatory", "https://mici.gob.pa/wp-content/uploads/2022/06/documento-explicativo-chile.pdf", "related_document"),
    ("mici_panama_chile_summary", "https://mici.gob.pa/wp-content/uploads/2022/06/resumen-del-tlc-de-chile1944913.pdf", "related_document"),
    ("mici_ca_tlc_restrictions_costa_rica", "https://mici.gob.pa/wp-content/uploads/2022/06/06-Anexo-3.106-Restricciones-a-la-importacion-y-a-la-exportacion.pdf", "candidate_exact_alternative"),
    ("mici_ca_tlc_certificate_of_origin", "https://mici.gob.pa/wp-content/uploads/2022/06/Anexo-III-CertificadoDeOrigen.pdf", "exact_alternative"),
    ("mici_usa_pll_ps_2014", "https://mici.gob.pa/wp-content/uploads/2022/06/tpc-pll-ps-105-001-2014.pdf", "exact_alternative"),
    ("mici_usa_pll_ps_2017", "https://mici.gob.pa/wp-content/uploads/2022/06/convocatoria-tpc-pll-ps-105-001-2017.pdf", "exact_alternative"),
    ("mici_usa_pll_ps_2018", "https://mici.gob.pa/wp-content/uploads/2022/06/convocatoria-tpc-pll-ps-105-001-2018.pdf", "exact_alternative"),
    ("mici_usa_pll_ps_2019", "https://mici.gob.pa/wp-content/uploads/2022/06/convocatoria-no-tpc-pll-ps-105-001-2019-del-contigente-arancelario.pdf", "exact_alternative"),
    ("subrei_panama_chile", "https://www.subrei.gob.cl/acuerdos-comerciales/acuerdos-comerciales-vigentes/panam%C3%A1", "related_repository"),
    ("subrei_panama_chile_chapter_10", "https://www.subrei.gob.cl/docs/default-source/acuerdos/panama/cap%C3%ADtulos-panam%C3%A1/11-cap%C3%ADtulo-10-comercio-transfronterizo-de-servicios.pdf?sfvrsn=c154177f_2", "exact_alternative"),
    ("subrei_panama_chile_full_text", "https://www.subrei.gob.cl/docs/default-source/acuerdos/panama/texto-completo-acuerdo-%281%29.pdf?sfvrsn=d5bf5d11_2", "related_document"),
    ("ustr_panama_tpa", "https://ustr.gov/trade-agreements/free-trade-agreements/panama-tpa", "related_repository"),
    ("ustr_panama_final_text", "https://ustr.gov/trade-agreements/free-trade-agreements/panama-tpa/final-text", "related_repository"),
    ("minec_korea_el_salvador_schedule", "https://infotrade.minec.gob.sv/corea/wp-content/uploads/sites/17/2018/02/2b-KOR-ES_final-27feb17.pdf", "exact_alternative"),
    ("minec_korea_repository", "https://infotrade.minec.gob.sv/corea/", "related_repository"),
    ("subrei_efta", "https://www.subrei.gob.cl/acuerdos-comerciales/acuerdos-comerciales-vigentes/efta", "manual_confirmation"),
    ("mici_efta_annex_xvi_appendix_1_costa_rica", "https://mici.gob.pa/wp-content/uploads/2022/06/03_apendice-1-costa-rica.pdf", "exact_alternative"),
]


def safe_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value).strip("_")


def download(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "amp-cont-ai/1.0 (provenance archive)"
    records = []
    for key, url, relation in SOURCES:
        row = {"source_id": key, "url": url, "relation": relation,
               "checked_at": datetime.now(timezone.utc).isoformat()}
        try:
            response = session.get(url, timeout=(15, 90), allow_redirects=True)
            row["status_code"] = response.status_code
            row["final_url"] = response.url
            row["content_type"] = response.headers.get("Content-Type", "")
            response.raise_for_status()
            body = response.content
            digest = hashlib.sha256(body).hexdigest()
            suffix = ".pdf" if body.startswith(b"%PDF-") else ".html"
            path = output / f"{safe_name(key)}-{digest[:12]}{suffix}"
            path.write_bytes(body)
            row.update({"status": "downloaded", "sha256": digest, "bytes": len(body), "path": str(path)})
        except Exception as exc:
            row.update({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
        records.append(row)
    manifest = {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
                "classification": "ANA_RECOVERY_AND_RELATED_OFFICIAL_SOURCES",
                "raw_inputs_modified": False, "records": records}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"total": len(records), "downloaded": sum(r["status"] == "downloaded" for r in records),
            "errors": sum(r["status"] == "error" for r in records), "manifest": str(output / "manifest.json")}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/bronze/ana_recovery_sources"))
    args = parser.parse_args()
    print(json.dumps(download(args.output), ensure_ascii=False, indent=2))
