"""
Crawler y Extractor Oficial del Arancel Interactivo de Panamá (ANA 2025/2026).
URL Fuente: https://aranceles.ana.gob.pa/#/home
API Base: https://aranceles-api.ana.gob.pa/v1/consulta

Extrae:
- Estructura Arancelaria SAC (Sección, Capítulo, Partida, Subpartida, Fracción 10-12 dígitos)
- Tributos Arancelarios (DAI %, ITBMS %, ISC %, ICCDP %)
- Permisos y Licencias OGAs (APA, AUPSA, MINSA, MIDA, Normas Técnicas, trámite electrónico/manual)
- Tratados Comerciales Internacionales vigentes al 2025 con degravamen preferencial
- Resoluciones y Fallos Arancelarios
- Notas Legales y Productos Sensitivos

Desarrollado v1.0.0 Miguel Benítez / Ing. Miguel Antonio Benítez González (UTP) - GNU GPL-3.0
"""

import os
import sys
import json
import time
import hashlib
import logging
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ana_interactive_tariff_crawler")

BASE_API_URL = "https://aranceles-api.ana.gob.pa/v1/consulta"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
TARGET_DIR = Path("data/bronze/ana_aranceles_2025")
MANIFEST_PATH = TARGET_DIR / "manifest.json"

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

import subprocess

def fetch_query_raw(searchbar: str, flow: str = "imp", timeout_sec: int = 12) -> Optional[Dict[str, Any]]:
    """
    Realiza la consulta al endpoint de aranceles de ANA usando curl.exe
    para mantener consistencia de headers TLS con el WAF gubernamental.
    """
    params = {
        "rbtn_codehs_word": "code",
        "rbtn_imp_exp": flow,
        "searchbar": searchbar
    }
    url = f"{BASE_API_URL}?{urllib.parse.urlencode(params)}"
    
    # Try with curl.exe first (bypasses TLS handshake disconnects on Windows)
    try:
        cmd = [
            "curl.exe", "-s", "--max-time", str(timeout_sec),
            "-H", f"User-Agent: {USER_AGENT}",
            "-H", "Accept: application/json, text/plain, */*",
            "-H", "Referer: https://aranceles.ana.gob.pa/",
            "-H", "Origin: https://aranceles.ana.gob.pa",
            url
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec + 3)
        if proc.returncode == 0 and proc.stdout:
            data = json.loads(proc.stdout)
            if isinstance(data, dict):
                return data
    except Exception as e:
        logger.debug(f"curl.exe fallo para {searchbar} [{flow}]: {e}")

    # Fallback to urllib
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://aranceles.ana.gob.pa/",
                "Origin": "https://aranceles.ana.gob.pa"
            }
        )
        with urllib.request.urlopen(req, timeout=timeout_sec) as response:
            if response.status == 200:
                return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        logger.debug(f"urllib fallo para {searchbar} [{flow}]: {e}")

    return None


def fetch_tariff_chapter(chapter_num: int, flow: str = "imp", retries: int = 2, delay: float = 0.8) -> Optional[Dict[str, Any]]:
    """
    Consulta un capítulo arancelario (01 a 98) en el endpoint oficial de la ANA.
    Si la consulta de 2 dígitos genera timeout por tamaño de tabla en la BD de ANA,
    descompone automáticamente la búsqueda en partidas de 4 dígitos (ej. 0201, 0202, ...).
    """
    ch_str = f"{chapter_num:02d}"
    
    # Intento 1: Búsqueda directa del capítulo a 2 dígitos
    for attempt in range(1, retries + 1):
        payload = fetch_query_raw(ch_str, flow=flow, timeout_sec=12)
        if payload and isinstance(payload, dict):
            products = payload.get("products", [])
            if len(products) > 0:
                raw_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                logger.info(f"Capítulo {ch_str} [{flow.upper()}]: {len(products)} fracciones extraídas directamente a 2 dígitos.")
                return {
                    "chapter": ch_str,
                    "flow": flow,
                    "sha256": sha256_bytes(raw_bytes),
                    "status": 200,
                    "product_count": len(products),
                    "data": payload
                }
        time.sleep(delay)

    # Intento 2: Descomposición inteligente a 4 dígitos para capítulos grandes
    logger.info(f"Capítulo {ch_str} [{flow.upper()}]: Descomponiendo en partidas de 4 dígitos ({ch_str}01..{ch_str}30)...")
    combined_products = []
    combined_notes = []
    consecutive_empty = 0

    for heading_idx in range(1, 35):
        heading_code = f"{ch_str}{heading_idx:02d}"
        hd_payload = fetch_query_raw(heading_code, flow=flow, timeout_sec=10)
        time.sleep(0.4) # cortesía anti-WAF
        
        if hd_payload and isinstance(hd_payload, dict):
            hd_prods = hd_payload.get("products", [])
            if hd_prods:
                consecutive_empty = 0
                for p in hd_prods:
                    # Deduplicate by codehs or code
                    p_code = p.get("codehs") or p.get("code")
                    if not any((x.get("codehs") or x.get("code")) == p_code for x in combined_products):
                        combined_products.append(p)
                if hd_payload.get("notes"):
                    combined_notes.extend(hd_payload.get("notes"))
                logger.debug(f"Partida {heading_code} [{flow.upper()}]: {len(hd_prods)} fracciones agregadas.")
            else:
                consecutive_empty += 1
        else:
            consecutive_empty += 1

        # Si encontramos al menos productos y 3 partidas consecutivas están vacías, terminamos el capítulo
        if len(combined_products) > 0 and consecutive_empty >= 3:
            break
        # Si no encontramos ningún producto y 5 partidas consecutivas están vacías, capítulo no tiene más partidas
        if len(combined_products) == 0 and consecutive_empty >= 5:
            break

    if combined_products:
        consolidated = {
            "products": combined_products,
            "notes": combined_notes,
            "chapter": ch_str,
            "flow": flow,
            "extraction_method": "decomposed_4digit_headings"
        }
        raw_bytes = json.dumps(consolidated, ensure_ascii=False).encode("utf-8")
        logger.info(f"Capítulo {ch_str} [{flow.upper()}]: {len(combined_products)} fracciones consolidadas vía partidas de 4 dígitos.")
        return {
            "chapter": ch_str,
            "flow": flow,
            "sha256": sha256_bytes(raw_bytes),
            "status": 200,
            "product_count": len(combined_products),
            "data": consolidated
        }

    logger.warning(f"No se obtuvieron fracciones para el capítulo {ch_str} [{flow.upper()}] tras descomposición.")
    return None

def run_crawler(start_ch: int = 1, end_ch: int = 98, flows: Optional[List[str]] = None, max_workers: int = 1) -> Dict[str, Any]:
    """
    Ejecuta el rastreo sistemático de todos los capítulos arancelarios para importación y exportación.
    """
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    if flows is None:
        flows = ["imp", "exp"]

    manifest = {}
    if MANIFEST_PATH.exists():
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception:
            manifest = {}

    total_chapters = end_ch - start_ch + 1
    total_queries = total_chapters * len(flows)
    completed_queries = 0
    total_products_collected = 0

    logger.info(f"Iniciando crawling de Aranceles ANA: capítulos {start_ch:02d} a {end_ch:02d}, flujos={flows}")

    for ch in range(start_ch, end_ch + 1):
        ch_str = f"{ch:02d}"
        for flow in flows:
            out_file = TARGET_DIR / f"chapter_{ch_str}_{flow}.json"
            
            # Check if already cached and valid
            if out_file.exists() and f"{ch_str}_{flow}" in manifest.get("entries", {}):
                cached_entry = manifest["entries"][f"{ch_str}_{flow}"]
                total_products_collected += cached_entry.get("product_count", 0)
                completed_queries += 1
                logger.debug(f"Capítulo {ch_str}_{flow} ya descargado previamente ({cached_entry.get('product_count', 0)} fracciones).")
                continue

            result = fetch_tariff_chapter(ch, flow=flow, delay=1.0)
            if result:
                # Save raw JSON
                with open(out_file, "w", encoding="utf-8") as f:
                    json.dump(result["data"], f, ensure_ascii=False, indent=2)

                # Update manifest
                if "entries" not in manifest:
                    manifest["entries"] = {}
                manifest["entries"][f"{ch_str}_{flow}"] = {
                    "chapter": ch_str,
                    "flow": flow,
                    "sha256": result["sha256"],
                    "product_count": result["product_count"],
                    "timestamp": time.time(),
                    "file": str(out_file.name)
                }
                total_products_collected += result["product_count"]
                completed_queries += 1

                # Periodic save of manifest
                with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
                    json.dump(manifest, f, indent=2, ensure_ascii=False)
            else:
                logger.warning(f"No se pudo obtener información para capítulo {ch_str}_{flow}")

            # Courtesy delay anti-WAF
            time.sleep(0.5)

    manifest["total_entries"] = len(manifest.get("entries", {}))
    manifest["total_products"] = total_products_collected
    manifest["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    logger.info(f"Crawling completado: {completed_queries}/{total_queries} consultas. Total fracciones recolectadas: {total_products_collected}")
    return manifest

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ANA Interactive Tariff Scraper")
    parser.add_argument("--start", type=int, default=1, help="Capítulo inicial (1-98)")
    parser.add_argument("--end", type=int, default=98, help="Capítulo final (1-98)")
    parser.add_argument("--flows", nargs="+", default=["imp", "exp"], help="Flujos a consultar ('imp', 'exp')")
    args = parser.parse_args()

    run_crawler(start_ch=args.start, end_ch=args.end, flows=args.flows)
