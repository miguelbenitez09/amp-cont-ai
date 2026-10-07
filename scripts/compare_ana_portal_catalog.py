"""Compare curated HS candidates with the official ANA interactive API."""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.scrapers.ana_hscode_scraper import PanamaTariffDatabase


def _tokens(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()
    return {token for token in re.findall(r"[a-z0-9]+", normalized) if len(token) > 2}


def query(session: requests.Session, code: str) -> dict:
    normalized = re.sub(r"\D", "", code)
    params = {"rbtn_codehs_word": "code", "rbtn_imp_exp": "imp", "searchbar": normalized}
    url = "https://aranceles-api.ana.gob.pa/v1/consulta"
    row = {"curated_code": code, "query_code": normalized, "query": params, "checked_at": datetime.now(timezone.utc).isoformat()}
    try:
        response = session.get(url, params=params, timeout=(5, 20))
        row.update({"status_code": response.status_code, "status": "response", "content_type": response.headers.get("Content-Type", "")})
        payload = response.json() if response.ok else {}
        products = payload.get("products", []) if isinstance(payload, dict) else []
        row["products"] = [{
            "hs12": product.get("hs12"),
            "description": product.get("hs12description"),
            "taxes": product.get("tributos", []),
            "regulatory_entities": product.get("OGA", []),
            "legal_notes": product.get("notas_legales", []),
        } for product in products]
        if not products:
            row["comparison"] = "not_found"
        elif any(product.get("hs12") == normalized for product in products):
            exact = next(product for product in products if product.get("hs12") == normalized)
            curated = next(item for item in PanamaTariffDatabase.OFFICIAL_TARIFF_ITEMS if item["hs_code_panama"] == code)
            portal_tokens = _tokens(exact.get("hs12description", ""))
            curated_tokens = _tokens(curated.get("descripcion", ""))
            similarity = len(portal_tokens & curated_tokens) / max(1, len(portal_tokens | curated_tokens))
            row["description_similarity"] = round(similarity, 4)
            row["comparison"] = "exact_code_description_mismatch" if similarity < 0.25 else "exact_code_match"
        else:
            row["comparison"] = "prefix_or_description_result"
    except (requests.RequestException, ValueError) as exc:
        row.update({"status": "transport_or_parse_error", "error": f"{type(exc).__name__}: {exc}", "comparison": "unavailable"})
    return row


def build(output: Path) -> dict:
    session = requests.Session()
    session.headers["User-Agent"] = "amp-cont-ai/1.0 (controlled provenance comparison)"
    rows = [query(session, item["hs_code_panama"]) for item in PanamaTariffDatabase.OFFICIAL_TARIFF_ITEMS]
    result = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "https://aranceles-api.ana.gob.pa/v1/consulta",
        "query_mode": "code/import/sequential",
        "raw_inputs_modified": False,
        "rows": rows,
        "summary": {status: sum(row.get("comparison") == status for row in rows) for status in {"exact_code_match", "exact_code_description_mismatch", "prefix_or_description_result", "not_found", "unavailable"}},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/gold/ana_portal_catalog_comparison.json"))
    args = parser.parse_args()
    print(json.dumps(build(args.output), ensure_ascii=False, indent=2))
