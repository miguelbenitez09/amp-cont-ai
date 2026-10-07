"""
=============================================================================
MOTOR DE EXTRACCIÓN Y CONSULTA DEL ARANCEL INTERACTIVO DE ADUANAS DE PANAMÁ
Autor: Desarrollado v1.0.0 Miguel Benítez / Ing. Miguel Antonio Benítez González (UTP)
Licencia: GNU General Public License v3.0 (GPL-3.0) con Atribución Obligatoria
=============================================================================

1. ARQUITECTURA DEL PORTAL Y ANÁLISIS DEL DOM:
   - Portal Web Front-End: https://aranceles.ana.gob.pa (Single Page Application
     construida sobre Angular 10+ e Ionic Framework 5, Bootstrap 3.4.1).
   - Componentes UI / DOM:
     * <app-root>: Contenedor raíz de la aplicación web aduanera.
     * <ion-grid>, <ion-row>, <ion-col>: Maquetación responsiva de resultados.
     * Form Controls Interactivos:
       - 'rbtn_codehs_word': Radio button ("code" para búsqueda numérica por código
         arancelario del Sistema Armonizado; "word" para búsqueda semántica por descripción).
       - 'rbtn_imp_exp': Radio button ("imp" para Arancel de Importación con DAI/ITBMS/ISC;
         "exp" para Régimen Definitivo de Exportación).
       - 'searchbar': Input de texto interactivo con autocompletado y búsqueda por prefijo.
     * Bloques de Presentación del DOM:
       - Árbol Taxonómico (family.codeHS): Sección, Capítulo (2 dígitos), Partida (4 dígitos),
         Subpartida OMA (6 dígitos), Subpartida Regional SAC (8 dígitos) y Fracción Nacional
         de Panamá (10 y 12 dígitos, ej. 2710.19.21.00.00).
       - Tabla de Tributos Aduaneros (detalle.tributos):
         * DAI (Derecho Arancelario a la Importación, ad-valorem %).
         * ITBMS (Impuesto de Transferencia de Bienes Muebles y Servicios, 0% o 7%).
         * ISC (Impuesto Selectivo al Consumo, ej. licores, tabaco, vehículos).
         * ICCDP (Impuesto al Consumo de Combustible y Derivados del Petróleo).
         * Enlaces directos a decretos y pliegos arancelarios oficiales (arancel_url, isc_archivo).
       - Tabla de Órganos Anuentes (OGA - Other Government Agencies):
         * Institución reguladora: MIDA (DNSA/DNSV/DECA), MINSA (DNFD/Saneamiento), APA
           (Agencia Panameña de Alimentos), Secretaría de Energía, MiAmbiente, DIASP, MICI.
         * Requisito / Permiso: Licencia zoosanitaria, registro sanitario, permiso de importación.
         * Modalidad de tramitación: "Manual" (sello físico en oficina) vs "Electrónica"
           (aprobación digital en ventanilla única aduanera SIGA).
       - Tratados de Libre Comercio y Preferencias (tratados):
         * Año fiscal de vigencia (desgravación cronológica).
         * País socio comercial (EE.UU., Centroamérica, Canadá, UE, México, Chile, ALADI, etc.).
         * Tratado / Acuerdo bilateral y porcentaje arancelario preferencial (degravamen %).
       - Notas Legales y Aclaratorias (notas_legales):
         * Rutas y enlaces a PDFs oficiales de las Notas Aclaratorias del Sistema Armonizado.
       - Resoluciones Anticipadas y Criterios Clasificatorios (fallos_resoluciones):
         * Fallos vinculantes emitidos por la Dirección de Gestión Técnica de la ANA.

2. ARQUITECTURA DE LA API REST OFICIAL:
   - Endpoint Base: https://aranceles-api.ana.gob.pa/v1/consulta
   - Método: GET con parámetros Query:
     * rbtn_codehs_word: "code" | "word"
     * rbtn_imp_exp: "imp" | "exp"
     * searchbar: <código arancelario o palabra clave>
   - Retorno: JSON estructurado con lista de 'products', conteniendo la ficha aduanera
     íntegra y trazable con el Sistema Integrado de Gestión Aduanera (SIGA).
=============================================================================
"""

import os
import sys
import json
import time
import ssl
import random
import logging
import hashlib
import argparse
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s"
)
logger = logging.getLogger("ANATariffScraper")

# Rutas estándar del proyecto Medallion
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
BRONZE_ANA_DIR = DATA_DIR / "bronze" / "ana_tariff"
SILVER_DIR = DATA_DIR / "silver"

BRONZE_ANA_DIR.mkdir(parents=True, exist_ok=True)
SILVER_DIR.mkdir(parents=True, exist_ok=True)

# URL oficial de la API de Aranceles de Panamá
ANA_API_BASE_URL = "https://aranceles-api.ana.gob.pa/v1/consulta"
ANA_PORTAL_URL = "https://aranceles.ana.gob.pa"

# Códigos arancelarios estratégicos del comercio marítimo y portuario panameño
STRATEGIC_PANAMA_HS_CODES = [
    # Combustibles y Bunkering (Tránsito Canal y Puertos Balboa/Cristóbal)
    "27101921",  # Diésel para vehículos y barcos
    "27101915",  # Búnker marino fuel oil / IFO
    "27101211",  # Gasolina de aviación / motor
    "27111200",  # Propano licuado (buques gaseros Neopanamax)
    # Alimentos refrigerados y perecederos (Cadena de frío y contenedores reefer)
    "020110",    # Carne bovina fresca o refrigerada
    "020230",    # Carne bovina deshuesada congelada
    "020712",    # Aves sin trocear congeladas
    "030211",    # Truchas / salmones frescos
    "030617",    # Camarones y langostinos congelados
    "040210",    # Leche en polvo
    "040690",    # Quesos madurados
    "080390",    # Bananos y plátanos frescos (Bocas Fruit / Puerto Almirante)
    "080440",    # Aguacates frescos
    "100590",    # Maíz amarillo a granel (Silos y graneleros)
    "100630",    # Arroz semiblanqueado o pulido
    # Medicamentos y productos farmacéuticos (Hub Logístico Tocumen / ZLC)
    "300220",    # Vacunas para medicina humana
    "300490",    # Medicamentos dosificados para venta al por menor
    # Automotriz y Maquinaria Pesada (Ro-Ro y Terminales Manzanillo / Balboa)
    "870323",    # Vehículos de turismo cilindrada 1500-3000cc
    "870421",    # Camiones y vehículos de transporte de carga g.v.w <= 5t
    "842611",    # Grúas pórtico y grúas de muelle STS sobre neumáticos/carriles
    "847130",    # Computadoras y unidades de procesamiento digital
    "851713",    # Teléfonos inteligentes / smartphones
    # Productos Químicos e Industriales
    "390110",    # Polietileno de densidad < 0.94 a granel
    "721420",    # Barras de hierro/acero estriadas para construcción
]


class ANATariffScraper:
    """
    Scraper y extractor industrial de la base de datos arancelaria de la
    Autoridad Nacional de Aduanas (ANA) de la República de Panamá.
    """

    def __init__(self, request_delay: float = 1.2, timeout: int = 15):
        self.request_delay = request_delay
        self.timeout = timeout
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def fetch_tariff_by_hs_code(
        self,
        hs_code: str,
        regime: str = "imp",
        search_type: str = "code"
    ) -> Optional[Dict[str, Any]]:
        """
        Consulta la API de la ANA para un código arancelario específico.
        Implementa reintentos con backoff exponencial.
        """
        clean_code = hs_code.replace(".", "").replace(" ", "").strip()
        params = {
            "rbtn_codehs_word": search_type,
            "rbtn_imp_exp": regime,
            "searchbar": clean_code
        }
        query_string = urllib.parse.urlencode(params)
        url = f"{ANA_API_BASE_URL}?{query_string}"

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Origin": ANA_PORTAL_URL,
                "Referer": f"{ANA_PORTAL_URL}/"
            }
        )

        for attempt in range(1, 4):
            try:
                time.sleep(self.request_delay + random.uniform(0.1, 0.4))
                with urllib.request.urlopen(req, context=self.ssl_context, timeout=self.timeout) as response:
                    if response.status == 200:
                        raw_bytes = response.read()
                        data = json.loads(raw_bytes.decode("utf-8"))
                        return {
                            "query_code": clean_code,
                            "regime": regime,
                            "search_type": search_type,
                            "url": url,
                            "scraped_at": datetime.now(timezone.utc).isoformat(),
                            "status_code": 200,
                            "products": data.get("products", []),
                            "raw_bytes_sha256": hashlib.sha256(raw_bytes).hexdigest()
                        }
            except Exception as e:
                logger.warning(f"Intento {attempt}/3 fallido para HS {clean_code}: {e}")
                time.sleep(2.0 * attempt)

        logger.error(f"Error definitivo al consultar código HS: {clean_code}")
        return None

    def save_raw_response(self, result: Dict[str, Any]) -> Path:
        """Guarda la respuesta cruda en la capa Bronze con formato JSON."""
        code = result["query_code"]
        regime = result["regime"]
        filename = f"ana_{regime}_{code}.json"
        target_path = BRONZE_ANA_DIR / filename
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        return target_path

    def batch_extract(self, hs_codes: List[str], regime: str = "imp") -> List[Dict[str, Any]]:
        """Extrae un lote de códigos arancelarios con checkpointing."""
        results = []
        logger.info(f"Iniciando extracción de {len(hs_codes)} códigos HS para régimen '{regime}'...")

        for idx, code in enumerate(hs_codes, 1):
            clean_code = code.replace(".", "").replace(" ", "").strip()
            target_path = BRONZE_ANA_DIR / f"ana_{regime}_{clean_code}.json"

            # Checkpoint: si ya existe y no está vacío, cargarlo
            if target_path.exists() and target_path.stat().st_size > 100:
                try:
                    with open(target_path, "r", encoding="utf-8") as f:
                        cached = json.load(f)
                    logger.info(f"[{idx}/{len(hs_codes)}] [CACHE HIT] HS {clean_code} cargado de Bronze.")
                    results.append(cached)
                    continue
                except Exception:
                    pass

            logger.info(f"[{idx}/{len(hs_codes)}] Consultando API oficial de la ANA para HS {clean_code}...")
            data = self.fetch_tariff_by_hs_code(clean_code, regime=regime)
            if data:
                self.save_raw_response(data)
                results.append(data)
                num_prods = len(data.get("products", []))
                logger.info(f"  -> Éxito: {num_prods} fracciones/incisos arancelarios recuperados.")
            else:
                logger.warning(f"  -> Sin datos para HS {clean_code}.")

        return results

    def normalize_to_silver_tables(self, extractions: List[Dict[str, Any]]) -> Dict[str, pd.DataFrame]:
        """
        Normaliza las extracciones crudas a tablas relacionales de la capa Silver:
        1. dim_ana_hs_catalog: Jerarquía y descripciones arancelarias.
        2. dim_ana_hs_taxes: DAI, ITBMS, ISC, ICCDP y tasas.
        3. dim_ana_hs_permits_oga: Órganos anuentes y permisos obligatorios.
        4. dim_ana_hs_trade_agreements: Acuerdos comerciales y aranceles preferenciales.
        5. dim_ana_hs_legal_notes: Notas aclaratorias legales del arancel.
        """
        catalog_rows = []
        taxes_rows = []
        oga_rows = []
        agreements_rows = []
        notes_rows = []

        now_iso = datetime.now(timezone.utc).isoformat()

        for ext in extractions:
            query_code = ext.get("query_code")
            regime = ext.get("regime", "imp")
            for prod in ext.get("products", []):
                hs12 = prod.get("hs12", "")
                hs_desc = prod.get("hs12description", "")
                detalle = prod.get("detalle", {})
                family = detalle.get("family", {}).get("codeHS", [])

                # Extraer jerarquía
                seccion = ""
                capitulo = ""
                partida = ""
                subpartida = ""
                sac_8 = ""
                fraccion_12 = hs12

                for level in family:
                    if "seccion" in level:
                        seccion = level.get("seccion", "")
                    if "capitulo" in level:
                        capitulo = level.get("capitulo", "")
                    if "partida" in level:
                        partida = level.get("partida", "")
                    if "subpartida" in level:
                        subpartida = level.get("subpartida", "")
                    if "sac" in level:
                        sac_8 = level.get("sac", "")
                    if "fraccion" in level:
                        fraccion_12 = level.get("fraccion", "")

                catalog_rows.append({
                    "hs_code_query": query_code,
                    "hs12": fraccion_12,
                    "sac_8": sac_8,
                    "subpartida_6": subpartida or (hs12[:6] if len(hs12) >= 6 else ""),
                    "partida_4": partida or (hs12[:4] if len(hs12) >= 4 else ""),
                    "capitulo_2": capitulo or (hs12[:2] if len(hs12) >= 2 else ""),
                    "seccion": seccion,
                    "descripcion_oficial": hs_desc,
                    "regimen": regime,
                    "updated_at": now_iso
                })

                # Extraer tributos
                tributos = detalle.get("tributos", [])
                dai_val = 0.0
                itbms_val = 0.0
                isc_val = 0.0
                iccdp_val = 0.0
                arancel_doc_url = None
                isc_doc_url = None

                for t in tributos:
                    nom = t.get("tributo_nombre", "").upper()
                    raw_val = t.get("valor", "0").replace("%", "").strip()
                    try:
                        val_num = float(raw_val)
                    except ValueError:
                        val_num = 0.0

                    if nom == "DAI":
                        dai_val = val_num
                        arancel_doc_url = t.get("arancel_url")
                    elif nom == "ITBMS":
                        itbms_val = val_num
                    elif nom == "ISC":
                        isc_val = val_num
                        isc_doc_url = t.get("isc_archivo")
                    elif nom == "ICCDP":
                        iccdp_val = val_num

                taxes_rows.append({
                    "hs12": fraccion_12,
                    "regimen": regime,
                    "dai_pct": dai_val,
                    "itbms_pct": itbms_val,
                    "isc_pct": isc_val,
                    "iccdp_usd_gal": iccdp_val,
                    "arancel_legal_url": arancel_doc_url,
                    "isc_legal_url": isc_doc_url,
                    "updated_at": now_iso
                })

                # Extraer Órganos Anuentes (OGA)
                ogas = prod.get("OGA", [])
                for oga in ogas:
                    inst = oga.get("institucion", "").strip()
                    permiso = oga.get("permiso", "").strip()
                    tipo = oga.get("tipo_permiso", "").strip()
                    oga_rows.append({
                        "hs12": fraccion_12,
                        "institucion": inst,
                        "permiso_requisito": permiso,
                        "tipo_tramitacion": tipo,
                        "canal_siga": "Ventanilla Electrónica SIGA" if "Elect" in tipo else "Tramitación Presencial Manual",
                        "updated_at": now_iso
                    })

                # Extraer Tratados Comerciales
                tratados = prod.get("tratados", [])
                for tr in tratados:
                    agreements_rows.append({
                        "hs12": fraccion_12,
                        "pais_socio": tr.get("pais", "").strip(),
                        "acuerdo_tratado": tr.get("tratado", "").strip(),
                        "anio_aplicacion": tr.get("ano", "").strip(),
                        "tasa_degravamen": tr.get("degravamen", "").strip(),
                        "updated_at": now_iso
                    })

                # Extraer Notas Legales
                notas = prod.get("notas_legales", [])
                for nl in notas:
                    notes_rows.append({
                        "hs12": fraccion_12,
                        "documento_nota": nl.get("direccion", "").strip(),
                        "url_completa": f"{ANA_PORTAL_URL}/{nl.get('direccion', '').strip()}",
                        "updated_at": now_iso
                    })

        df_catalog = pd.DataFrame(catalog_rows).drop_duplicates(subset=["hs12", "regimen"])
        df_taxes = pd.DataFrame(taxes_rows).drop_duplicates(subset=["hs12", "regimen"])
        df_oga = pd.DataFrame(oga_rows).drop_duplicates()
        df_agreements = pd.DataFrame(agreements_rows).drop_duplicates()
        df_notes = pd.DataFrame(notes_rows).drop_duplicates()

        return {
            "dim_ana_hs_catalog": df_catalog,
            "dim_ana_hs_taxes": df_taxes,
            "dim_ana_hs_permits_oga": df_oga,
            "dim_ana_hs_trade_agreements": df_agreements,
            "dim_ana_hs_legal_notes": df_notes
        }

    def save_silver_tables(self, tables: Dict[str, pd.DataFrame]) -> Dict[str, Path]:
        """Guarda las tablas normalizadas en formato Parquet en la capa Silver con manifiestos."""
        saved_paths = {}
        for name, df in tables.items():
            parquet_path = SILVER_DIR / f"{name}.parquet"
            df.to_parquet(parquet_path, index=False)
            saved_paths[name] = parquet_path

            # Crear manifiesto criptográfico de procedencia
            manifest_path = SILVER_DIR / f"{name}.parquet.source.json"
            content_bytes = parquet_path.read_bytes()
            manifest = {
                "entity": name,
                "file_path": str(parquet_path),
                "records_count": len(df),
                "columns": list(df.columns),
                "sha256": hashlib.sha256(content_bytes).hexdigest(),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "author": "Desarrollado v1.0.0 Miguel Benítez / Ing. Miguel Antonio Benítez González (UTP) - GNU GPL-3.0",
                "source_origin": ANA_API_BASE_URL,
                "portal_reference": ANA_PORTAL_URL
            }
            with open(manifest_path, "w", encoding="utf-8") as mf:
                json.dump(manifest, mf, indent=2, ensure_ascii=False)

            logger.info(f"Guardado {name}.parquet ({len(df)} registros) -> SHA-256: {manifest['sha256'][:16]}...")

        return saved_paths


def main():
    parser = argparse.ArgumentParser(description="Extractor del Arancel Interactivo de Aduanas de Panamá (ANA)")
    parser.add_argument("--mode", choices=["strategic", "custom", "keyword"], default="strategic",
                        help="Modo de consulta: strategic (códigos clave de logística), custom (códigos manuales), keyword (búsqueda de texto)")
    parser.add_argument("--codes", type=str, default="",
                        help="Lista de códigos HS separados por coma (usar con --mode custom)")
    parser.add_argument("--query", type=str, default="",
                        help="Palabra clave a buscar (usar con --mode keyword)")
    parser.add_argument("--regime", choices=["imp", "exp"], default="imp",
                        help="Régimen aduanero: imp (importación) o exp (exportación)")
    args = parser.parse_args()

    scraper = ANATariffScraper(request_delay=1.0)

    if args.mode == "strategic":
        codes = STRATEGIC_PANAMA_HS_CODES
    elif args.mode == "custom":
        codes = [c.strip() for c in args.codes.split(",") if c.strip()]
    elif args.mode == "keyword":
        logger.info(f"Buscando por palabra clave: '{args.query}'...")
        res = scraper.fetch_tariff_by_hs_code(args.query, regime=args.regime, search_type="word")
        if res:
            scraper.save_raw_response(res)
            print(json.dumps(res, indent=2, ensure_ascii=False)[:2000])
        return

    # Extraer lote
    extractions = scraper.batch_extract(codes, regime=args.regime)
    tables = scraper.normalize_to_silver_tables(extractions)
    saved = scraper.save_silver_tables(tables)

    print("\n" + "=" * 65)
    print("EXTRACCIÓN DE ARANCELES ANA COMPLETADA CON ÉXITO")
    print("=" * 65)
    for name, path in saved.items():
        cnt = len(tables[name])
        print(f"  {name:<30} -> {cnt:>5} registros | {path.name}")
    print("=" * 65)


if __name__ == "__main__":
    main()
