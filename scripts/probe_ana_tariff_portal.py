"""Probe ANA's interactive tariff API without crawling or mutating source data."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import requests


def probe(code: str, timeout: tuple[int, int] = (5, 15)) -> dict:
    params = {"rbtn_codehs_word": "code", "rbtn_imp_exp": "imp", "searchbar": code}
    url = "https://aranceles-api.ana.gob.pa/v1/consulta?" + urlencode(params)
    result = {"checked_at": datetime.now(timezone.utc).isoformat(), "url": url, "query": params}
    try:
        response = requests.get(url, timeout=timeout)
        result.update({"status_code": response.status_code, "content_type": response.headers.get("Content-Type", ""), "bytes": len(response.content), "status": "response"})
        if response.ok:
            try:
                payload = response.json()
                result.update({"json": True, "top_level_type": type(payload).__name__, "record_count": len(payload) if isinstance(payload, list) else None})
                products = payload.get("products", []) if isinstance(payload, dict) else []
                result["products"] = [
                    {
                        "hs12": item.get("hs12"),
                        "description": item.get("hs12description"),
                        "taxes": item.get("tributos", []),
                        "regulatory_entities": item.get("OGA", []),
                        "legal_notes": item.get("notas_legales", []),
                        "rulings": item.get("fallos_resoluciones", []),
                    }
                    for item in products
                ]
            except ValueError:
                result.update({"json": False, "error": "response_not_json"})
    except requests.RequestException as exc:
        result.update({"status": "timeout_or_transport_error", "error": f"{type(exc).__name__}: {exc}"})
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", default="2710")
    parser.add_argument("--output", type=Path, default=Path("data/gold/ana_tariff_portal_probe.json"))
    args = parser.parse_args()
    result = probe(args.code)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
