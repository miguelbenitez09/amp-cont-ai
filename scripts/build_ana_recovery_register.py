"""Create a provenance register for ANA links that returned 404."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


SOURCES = {
    "pll_ps_2014.pdf": {
        "status": "exact_alternative_source",
        "source_url": "https://mici.gob.pa/wp-content/uploads/2022/06/tpc-pll-ps-105-001-2014.pdf",
        "source_name": "MICI convocatoria TPC-PLL/PS 105-001-2014",
        "basis": "Official MICI PDF is the same TPC-PLL/PS 105-001-2014 contingency call referenced by the ANA record.",
    },
    "pll_ps_2017.pdf": {
        "status": "exact_alternative_source",
        "source_url": "https://mici.gob.pa/wp-content/uploads/2022/06/convocatoria-tpc-pll-ps-105-001-2017.pdf",
        "source_name": "MICI convocatoria TPC-PLL/PS 105-001-2017",
        "basis": "Official MICI PDF is the same TPC-PLL/PS 105-001-2017 contingency call referenced by the ANA record.",
    },
    "pll_ps_2018.pdf": {
        "status": "exact_alternative_source",
        "source_url": "https://mici.gob.pa/wp-content/uploads/2022/06/convocatoria-tpc-pll-ps-105-001-2018.pdf",
        "source_name": "MICI convocatoria TPC-PLL/PS 105-001-2018",
        "basis": "Official MICI PDF is the same TPC-PLL/PS 105-001-2018 contingency call referenced by the ANA record.",
    },
    "pll_ps_2019.pdf": {
        "status": "exact_alternative_source",
        "source_url": "https://mici.gob.pa/wp-content/uploads/2022/06/convocatoria-no-tpc-pll-ps-105-001-2019-del-contigente-arancelario.pdf",
        "source_name": "MICI convocatoria TPC-PLL/PS 105-001-2019",
        "basis": "Official MICI PDF is the same TPC-PLL/PS 105-001-2019 contingency call referenced by the ANA record.",
    },
    "pll_ps_": {
        "status": "related_official_repository",
        "source_url": "https://ustr.gov/trade-agreements/free-trade-agreements/panama-tpa/final-text",
        "source_name": "USTR Panama TPA final text and annexes",
        "basis": "Official USTR page lists the Panama annexes and tariff schedules; exact historical PLL file name was not found.",
    },
    "medidas_disconforme_ii_n_explicativa": {
        "status": "related_official_repository",
        "source_url": "https://mici.gob.pa/onci-acuerdos-comerciales-bilaterales/",
        "source_name": "MICI Panama bilateral agreements index",
        "basis": "Official index confirms the Panama bilateral treaty family; the exact ANA asset path remains unresolved.",
    },
    "CAPITULO_10.pdf": {
        "status": "exact_alternative_source",
        "source_url": "https://www.subrei.gob.cl/docs/default-source/acuerdos/panama/cap%C3%ADtulos-panam%C3%A1/11-cap%C3%ADtulo-10-comercio-transfronterizo-de-servicios.pdf?sfvrsn=c154177f_2",
        "source_name": "SUBREI Chile–Panama Chapter 10 PDF",
        "basis": "Official SUBREI PDF has the same treaty chapter title and Chile–Panama Chapter 10 content.",
    },
    "02b-anexo-2b-kor-es_degravacion.pdf": {
        "status": "exact_alternative_source",
        "source_url": "https://infotrade.minec.gob.sv/corea/wp-content/uploads/sites/17/2018/02/2b-KOR-ES_final-27feb17.pdf",
        "source_name": "MINEC El Salvador Korea–El Salvador tariff schedule",
        "basis": "Official MINEC PDF contains the Section B tariff schedule and HS 2015 codes.",
    },
    "02_Definicionfes_Generales.pdf": {
        "status": "related_official_repository",
        "source_url": "https://infotrade.minec.gob.sv/corea/",
        "source_name": "MINEC El Salvador Korea agreement repository",
        "basis": "Official repository is the alternate starting point; the exact misspelled ANA filename was not found.",
    },
    "ACUERDO.pdf": {
        "status": "exact_alternative_source",
        "source_url": "https://mici.gob.pa/wp-content/uploads/2022/06/TextoNormativo_acuerdo-de-alcance-parcial-entre-la-panama-y-la-republica-de-cuba.pdf",
        "source_name": "MICI Panama–Cuba partial-scope agreement",
        "basis": "Official MICI text normative document for the same agreement.",
    },
    "Anexo_3-10-6_Restricciones-import-y-export.pdf": {
        "status": "candidate_alternative_source",
        "source_url": "https://mici.gob.pa/wp-content/uploads/2022/06/06-Anexo-3.106-Restricciones-a-la-importacion-y-a-la-exportacion.pdf",
        "source_name": "MICI TLC Centroamérica–Panamá, Anexo 3.10(6) Costa Rica",
        "basis": "Official MICI PDF has the same Anexo 3.10(6) title and Panama measures; country pairing must be confirmed because the ANA path omits the bilateral country.",
    },
    "certificado_de_Origen.pdf": {
        "status": "exact_alternative_source",
        "source_url": "https://mici.gob.pa/wp-content/uploads/2022/06/Anexo-III-CertificadoDeOrigen.pdf",
        "source_name": "MICI TLC Centroamérica–Panamá, Anexo III Certificado de Origen",
        "basis": "Official MICI PDF matches the ANA certificate title and the Centroamérica–Panamá treaty family.",
    },
    "29_anexo_xvi_apendice_1.pdf": {
        "status": "exact_alternative_source",
        "source_url": "https://mici.gob.pa/wp-content/uploads/2022/06/03_apendice-1-costa-rica.pdf",
        "source_name": "MICI/EFTA Anexo XVI, Apéndice 1 Costa Rica",
        "basis": "Official MICI PDF has the same Anexo XVI / Apéndice 1 Costa Rica title and MFN-exemptions content.",
    },
}


def build(manifest_path: Path, output: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = []
    for failure in manifest.get("failures", []):
        record = next((r for r in manifest["records"] if r["record_id"] == failure["record_id"]), {})
        match = next((v for k, v in SOURCES.items() if k in failure["url"]), None)
        if match is None:
            match = {"status": "no_public_alternative_located", "source_url": None,
                     "source_name": None, "basis": "No exact public replacement was located during this review."}
        rows.append({"record_id": failure["record_id"], "title": record.get("title"),
                     "category": record.get("category"), "ana_url": failure["url"],
                     "http_status": 404, "checked_at": datetime.now(timezone.utc).isoformat(), **match})
    output.parent.mkdir(parents=True, exist_ok=True)
    result = {"schema_version": 1, "classification": "PROVENANCE_RECOVERY_REGISTER",
              "source_manifest": str(manifest_path), "raw_inputs_modified": False,
              "records": rows}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"records": len(rows), "exact_sources": sum(r["status"] == "exact_alternative_source" for r in rows),
            "related_repositories": sum(r["status"] == "related_official_repository" for r in rows),
            "manual_confirmation": sum(r["status"] == "related_source_needs_manual_confirmation" for r in rows),
            "unlocated": sum(r["status"] == "no_public_alternative_located" for r in rows), "output": str(output)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/gold/ana_agreements_recovery/source_register.json"))
    args = parser.parse_args()
    print(json.dumps(build(args.manifest, args.output), ensure_ascii=False, indent=2))
