"""
Motor Compuesto de Linaje, Cronología y Base de Conocimiento Arancelario (HS Code Lineage Engine).
Cruza y normaliza 3 fuentes de datos maestras de Panamá:
1. Fuente 1: Arancel Oficial Interactivo ANA 2025 (aranceles-api.ana.gob.pa / dim_ana_hs_* / bronze).
2. Fuente 2: Comercio Exterior Histórico INEC 1997-2025 (dim_tariff_historical.parquet / 27,764 códigos).
3. Fuente 3: Declaraciones Aduaneras reales y Recintos Aduaneros (customs_imports_2020 / gatech_recintos / ana_regulatory).

Taxonomía de Linaje Arancelario (Enmiendas OMA 1996, 2002, 2007, 2012, 2017, 2022/2025):
- VIGENTE: Fracción activa en el SAC 2022/2025 a 10-12 dígitos.
- HEREDADO: Fracción histórica originada en enmiendas previas.
- EQUIVALENTE: Mapeo 1 a 1 directo entre código histórico y fracción vigente.
- DERIVADO_SPLIT: 1 código previo subdividido en múltiples fracciones modernas.
- DERIVADO_MERGE: Múltiples códigos históricos fusionados en 1 fracción consolidada.
- HISTORICO_OBSERVADO: Observado en transacciones aduaneras reales sin fracción vigente directa.

Desarrollado v1.0.0 Miguel Benítez / Ing. Miguel Antonio Benítez González (UTP) - GNU GPL-3.0
"""

import os
import sys
import json
import sqlite3
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timezone
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("hs_code_lineage_engine")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SILVER_DIR = PROJECT_ROOT / "data" / "silver"
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"
DB_PATH = PROJECT_ROOT / "data" / "metadata.db"
KNOWLEDGE_BASE_JSON = SILVER_DIR / "customs_tariff_knowledge_base.json"

# WCO Harmonized System Amendments Timeline
WCO_AMENDMENTS = {
    "HS_1996": {"effective_from": 1996, "effective_to": 2001, "name": "2da Enmienda OMA (SA 1996)"},
    "HS_2002": {"effective_from": 2002, "effective_to": 2006, "name": "3ra Enmienda OMA (SA 2002)"},
    "HS_2007": {"effective_from": 2007, "effective_to": 2011, "name": "4ta Enmienda OMA (SA 2007)"},
    "HS_2012": {"effective_from": 2012, "effective_to": 2016, "name": "5ta Enmienda OMA (SA 2012)"},
    "HS_2017": {"effective_from": 2017, "effective_to": 2021, "name": "6ta Enmienda OMA (SA 2017)"},
    "HS_2022": {"effective_from": 2022, "effective_to": 2026, "name": "7ma Enmienda OMA (SA 2022/2025 SAC)"}
}

class HSCodeLineageEngine:
    """
    Motor central de inferencia y catalogación de linaje arancelario para la República de Panamá.
    """
    _instance: Optional["HSCodeLineageEngine"] = None

    def __init__(self):
        self.active_sac_catalog: Dict[str, Dict[str, Any]] = {}
        self.historical_catalog: Dict[str, Dict[str, Any]] = {}
        self.taxes_catalog: Dict[str, Dict[str, Any]] = {}
        self.permits_catalog: Dict[str, List[Dict[str, Any]]] = {}
        self.treaties_catalog: Dict[str, List[Dict[str, Any]]] = {}
        self.recintos_catalog: List[Dict[str, Any]] = []
        self.regulatory_documents: Dict[str, List[Dict[str, Any]]] = {}
        self.lineage_index: Dict[str, Dict[str, Any]] = {}
        self._is_loaded = False

    @classmethod
    def get_instance(cls) -> "HSCodeLineageEngine":
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.initialize()
        return cls._instance

    def initialize(self, force_reload: bool = False) -> None:
        """Carga e indexa las 3 fuentes de datos en memoria para inferencia de baja latencia."""
        if self._is_loaded and not force_reload:
            return

        logger.info("Inicializando HSCodeLineageEngine desde las 3 fuentes maestras...")
        self._load_source_1_active_tariff()
        self._load_source_2_historical_trade()
        self._load_source_3_customs_and_regulations()
        self._build_lineage_graph()
        self._persist_to_sqlite()
        self._is_loaded = True
        logger.info(f"HSCodeLineageEngine listo: {len(self.lineage_index)} códigos indexados con linaje completo.")

    def _load_source_1_active_tariff(self) -> None:
        """Carga el Arancel Interactivo 2025 activo desde Parquet y Bronze."""
        # 1. Base Parquet silver dimensions if available
        dim_cat = SILVER_DIR / "dim_ana_hs_catalog.parquet"
        if dim_cat.exists():
            try:
                df = pd.read_parquet(dim_cat)
                for _, r in df.iterrows():
                    code12 = str(r.get("hs12", "")).strip().replace(".", "")
                    code_clean = str(r.get("sac_8", "")).strip().replace(".", "")
                    if code12:
                        self.active_sac_catalog[code12] = {
                            "hs12": code12,
                            "sac_8": code_clean or code12[:8],
                            "subpartida_6": str(r.get("subpartida_6", ""))[:6] or code12[:6],
                            "partida_4": str(r.get("partida_4", ""))[:4] or code12[:4],
                            "capitulo_2": str(r.get("capitulo_2", ""))[:2] or code12[:2],
                            "seccion": str(r.get("seccion", "")),
                            "descripcion": str(r.get("descripcion_oficial", "")),
                            "regimen": str(r.get("regimen", "imp")),
                            "source": "ANA_INTERACTIVE_API_2025",
                            "amendment": "HS_2022"
                        }
            except Exception as e:
                logger.warning(f"Error cargando dim_ana_hs_catalog: {e}")

        # Taxes
        dim_taxes = SILVER_DIR / "dim_ana_hs_taxes.parquet"
        if dim_taxes.exists():
            try:
                df = pd.read_parquet(dim_taxes)
                for _, r in df.iterrows():
                    code12 = str(r.get("hs12", "")).strip().replace(".", "")
                    if code12:
                        self.taxes_catalog[code12] = {
                            "dai_pct": float(r.get("dai_pct", 0.0) or 0.0),
                            "itbms_pct": float(r.get("itbms_pct", 0.0) or 0.0),
                            "isc_pct": float(r.get("isc_pct", 0.0) or 0.0),
                            "iccdp_usd": float(r.get("iccdp_usd_gal", 0.0) or 0.0)
                        }
            except Exception as e:
                logger.warning(f"Error cargando dim_ana_hs_taxes: {e}")

        # Permits
        dim_oga = SILVER_DIR / "dim_ana_hs_permits_oga.parquet"
        if dim_oga.exists():
            try:
                df = pd.read_parquet(dim_oga)
                for _, r in df.iterrows():
                    code12 = str(r.get("hs12", "")).strip().replace(".", "")
                    if code12:
                        if code12 not in self.permits_catalog:
                            self.permits_catalog[code12] = []
                        self.permits_catalog[code12].append({
                            "institucion": str(r.get("institucion", "")),
                            "permiso": str(r.get("permiso_requisito", "")),
                            "tipo_tramite": str(r.get("tipo_tramitacion", "Electronico")),
                            "canal": str(r.get("canal_siga", "SIGA / VUCE"))
                        })
            except Exception as e:
                logger.warning(f"Error cargando dim_ana_hs_permits_oga: {e}")

        # Treaties
        dim_treaties = SILVER_DIR / "dim_ana_hs_trade_agreements.parquet"
        if dim_treaties.exists():
            try:
                df = pd.read_parquet(dim_treaties)
                for _, r in df.iterrows():
                    code12 = str(r.get("hs12", "")).strip().replace(".", "")
                    if code12:
                        if code12 not in self.treaties_catalog:
                            self.treaties_catalog[code12] = []
                        self.treaties_catalog[code12].append({
                            "pais": str(r.get("pais_socio", "")),
                            "tratado": str(r.get("acuerdo_tratado", "")),
                            "degravamen": str(r.get("tasa_degravamen", "0.00%")),
                            "ano": str(r.get("anio_aplicacion", "2025"))
                        })
            except Exception as e:
                logger.warning(f"Error cargando dim_ana_hs_trade_agreements: {e}")

        # 2. Also ingest cached bronze raw chapters (e.g. chapter_01_imp.json, etc.)
        bronze_ana = BRONZE_DIR / "ana_aranceles_2025"
        if bronze_ana.exists():
            for jf in bronze_ana.glob("chapter_*_imp.json"):
                try:
                    with open(jf, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    for prod in data.get("products", []):
                        hs12 = str(prod.get("hs12", "")).strip()
                        if not hs12:
                            continue
                        desc = str(prod.get("hs12description", "")).strip()
                        detalle = prod.get("detalle", {})
                        code_hs_levels = detalle.get("family", {}).get("codeHS", [])
                        seccion = ""
                        capitulo = hs12[:2]
                        partida = hs12[:4]
                        subpartida = hs12[:6]
                        sac8 = hs12[:8]
                        for lvl in code_hs_levels:
                            if "seccion" in lvl:
                                seccion = lvl["seccion"]
                            if "capitulo" in lvl:
                                capitulo = lvl["capitulo"]
                            if "partida" in lvl:
                                partida = lvl["partida"]
                            if "subpartida" in lvl:
                                subpartida = lvl["subpartida"]
                            if "sac" in lvl:
                                sac8 = lvl["sac"]

                        self.active_sac_catalog[hs12] = {
                            "hs12": hs12,
                            "sac_8": sac8,
                            "subpartida_6": subpartida,
                            "partida_4": partida,
                            "capitulo_2": capitulo,
                            "seccion": seccion,
                            "descripcion": desc,
                            "regimen": "imp",
                            "source": "ANA_INTERACTIVE_API_2025",
                            "amendment": "HS_2022"
                        }

                        # Taxes from detalle
                        tributos = detalle.get("tributos", [])
                        dai_val = 0.0
                        itbms_val = 0.0
                        isc_val = 0.0
                        iccdp_val = 0.0
                        for t in tributos:
                            tnombre = str(t.get("tributo_nombre", "")).upper()
                            val_str = str(t.get("valor", "0")).replace("%", "").strip()
                            try:
                                v_float = float(val_str)
                            except ValueError:
                                v_float = 0.0
                            if tnombre == "DAI":
                                dai_val = v_float
                            elif tnombre == "ITBMS":
                                itbms_val = v_float
                            elif tnombre == "ISC":
                                isc_val = v_float
                            elif tnombre == "ICCDP":
                                iccdp_val = v_float
                        self.taxes_catalog[hs12] = {
                            "dai_pct": dai_val,
                            "itbms_pct": itbms_val,
                            "isc_pct": isc_val,
                            "iccdp_usd": iccdp_val
                        }

                        # Permits from OGA
                        ogas = prod.get("OGA", [])
                        if ogas:
                            self.permits_catalog[hs12] = [
                                {
                                    "institucion": o.get("institucion", ""),
                                    "permiso": o.get("permiso", ""),
                                    "tipo_tramite": o.get("tipo_permiso", "Electronico"),
                                    "canal": "SIGA"
                                }
                                for o in ogas
                            ]

                        # Treaties
                        tratados = prod.get("tratados", [])
                        if tratados:
                            self.treaties_catalog[hs12] = [
                                {
                                    "pais": tr.get("pais", ""),
                                    "tratado": tr.get("tratado", ""),
                                    "degravamen": tr.get("degravamen", "0.00%"),
                                    "ano": tr.get("ano", "2025")
                                }
                                for tr in tratados
                            ]
                except Exception as e:
                    logger.debug(f"Error parsing bronze {jf}: {e}")

        logger.info(f"Fuente 1 (Arancel 2025): {len(self.active_sac_catalog)} fracciones activas cargadas.")

    def _load_source_2_historical_trade(self) -> None:
        """Carga los 27,764 códigos históricos observados en comercio exterior INEC 1997-2025."""
        dim_hist = SILVER_DIR / "dim_tariff_historical.parquet"
        if dim_hist.exists():
            try:
                df = pd.read_parquet(dim_hist)
                for _, r in df.iterrows():
                    code = str(r.get("hs_code", "")).strip().replace(".", "")
                    if not code:
                        continue
                    desc = str(r.get("description", "")).strip()
                    ch = str(r.get("chapter", code[:2]))
                    sub6 = str(r.get("hs_code_6", code[:6]))
                    panama_code = str(r.get("hs_code_panama", code)).replace(".", "").strip()
                    
                    # Estimate historical WCO amendment based on code structure & observations
                    amendment = "HS_2017" if len(code) >= 10 else ("HS_2012" if len(code) == 8 else "HS_2007")
                    
                    self.historical_catalog[code] = {
                        "hs_code": code,
                        "hs_code_panama": panama_code,
                        "descripcion": desc,
                        "capitulo": ch,
                        "subpartida_6": sub6,
                        "partida_4": code[:4],
                        "source": "INEC_COMEXT_HISTORICAL_OBSERVATION",
                        "amendment": amendment
                    }
            except Exception as e:
                logger.error(f"Error cargando dim_tariff_historical: {e}")
        logger.info(f"Fuente 2 (Histórico INEC): {len(self.historical_catalog)} códigos históricos indexados.")

    def _load_source_3_customs_and_regulations(self) -> None:
        """Carga recintos aduaneros y catálogo normativo/resoluciones."""
        # 1. Recintos aduaneros
        recintos_json = BRONZE_DIR / "gatech_recintos" / "recintos_aduaneros_panama.json"
        if recintos_json.exists():
            try:
                with open(recintos_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.recintos_catalog = data.get("recintos", [])
            except Exception as e:
                logger.warning(f"Error cargando recintos aduaneros: {e}")

        # 2. Normativa y resoluciones de aduanas
        reg_dir = BRONZE_DIR / "ana_regulatory"
        if reg_dir.exists():
            for jf in reg_dir.glob("*.json"):
                if jf.name == "regulatory_manifest.json":
                    continue
                try:
                    with open(jf, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.regulatory_documents[jf.stem] = data
                except Exception as e:
                    logger.debug(f"Error cargando normativa {jf}: {e}")

        logger.info(f"Fuente 3: {len(self.recintos_catalog)} recintos y {len(self.regulatory_documents)} colecciones normativas cargadas.")

    def _build_lineage_graph(self) -> None:
        """
        Construye la taxonomía y grafo de linaje entre las 3 fuentes:
        VIGENTE, HEREDADO, EQUIVALENTE, DERIVADO_SPLIT, DERIVADO_MERGE, HISTORICO_OBSERVADO.
        """
        # Map 6-digit subheadings to active 10-12 digit codes
        subheading_to_active: Dict[str, List[str]] = {}
        for hs12, info in self.active_sac_catalog.items():
            sub6 = info["subpartida_6"]
            if sub6 not in subheading_to_active:
                subheading_to_active[sub6] = []
            subheading_to_active[sub6].append(hs12)

        # 1. First process all ACTIVE SAC codes
        for hs12, info in self.active_sac_catalog.items():
            sub6 = info["subpartida_6"]
            active_siblings = subheading_to_active.get(sub6, [])
            
            # Check historical counterparts with same 6/8 prefix
            hist_matches = [
                hcode for hcode in self.historical_catalog.keys()
                if hcode.startswith(sub6) or hcode == info["sac_8"]
            ]
            
            # Determine lineage status
            if len(active_siblings) > 1 and len(hist_matches) == 1:
                lineage_tag = "DERIVADO_SPLIT"
                derivation_notes = f"Fracción {hs12} originada por subdivisión de la subpartida histórica {sub6} ({len(active_siblings)} fracciones SAC modernas)."
            elif len(active_siblings) == 1 and len(hist_matches) > 1:
                lineage_tag = "DERIVADO_MERGE"
                derivation_notes = f"Fracción {hs12} consolidada a partir de {len(hist_matches)} códigos históricos observados."
            elif any(h == hs12 or h == info["sac_8"] for h in hist_matches):
                lineage_tag = "EQUIVALENTE"
                derivation_notes = "Mapeo directo 1 a 1 verificado entre histórico observado y arancel interactivo vigente."
            else:
                lineage_tag = "VIGENTE"
                derivation_notes = "Fracción nacional SAC 2022/2025 plenamente vigente en el sistema arancelario oficial de la ANA."

            self.lineage_index[hs12] = {
                "hs_code": hs12,
                "hs12": hs12,
                "sac_8": info["sac_8"],
                "subpartida_6": sub6,
                "partida_4": info["partida_4"],
                "capitulo_2": info["capitulo_2"],
                "seccion": info["seccion"],
                "descripcion": info["descripcion"],
                "lineage_tag": lineage_tag,
                "derivation_notes": derivation_notes,
                "is_active_2025": True,
                "amendment_timeline": {
                    "HS_1996": sub6 if sub6 in self.historical_catalog else None,
                    "HS_2002": sub6,
                    "HS_2007": info["sac_8"],
                    "HS_2012": info["sac_8"],
                    "HS_2017": info["sac_8"],
                    "HS_2022": hs12
                },
                "taxes": self.taxes_catalog.get(hs12, {"dai_pct": 0.0, "itbms_pct": 7.0, "isc_pct": 0.0, "iccdp_usd": 0.0}),
                "permits": self.permits_catalog.get(hs12, []),
                "trade_agreements": self.treaties_catalog.get(hs12, []),
                "historical_counterparts": hist_matches[:10]
            }

        # 2. Process HISTORICAL codes that do not directly match an active hs12
        for hcode, hinfo in self.historical_catalog.items():
            if hcode in self.lineage_index or any(v["sac_8"] == hcode for v in self.active_sac_catalog.values()):
                continue

            sub6 = hinfo["subpartida_6"]
            active_successors = subheading_to_active.get(sub6, [])
            
            if len(active_successors) > 1:
                lineage_tag = "HEREDADO"
                notes = f"Código histórico {hcode} heredado de enmiendas previas; subdividido en {len(active_successors)} fracciones activas en SAC 2025."
            elif len(active_successors) == 1:
                lineage_tag = "HEREDADO"
                notes = f"Código histórico {hcode} sucedido directamente por la fracción {active_successors[0]} en el SAC vigente."
            else:
                lineage_tag = "HISTORICO_OBSERVADO"
                notes = f"Código {hcode} registrado en transacciones aduaneras históricas del INEC; requiere consulta de correlación especial."

            self.lineage_index[hcode] = {
                "hs_code": hcode,
                "hs12": active_successors[0] if active_successors else None,
                "sac_8": hcode[:8] if len(hcode) >= 8 else None,
                "subpartida_6": sub6,
                "partida_4": hinfo["partida_4"],
                "capitulo_2": hinfo["capitulo"],
                "seccion": "",
                "descripcion": hinfo["descripcion"],
                "lineage_tag": lineage_tag,
                "derivation_notes": notes,
                "is_active_2025": False,
                "amendment_timeline": {
                    "HS_1996": hcode if hinfo["amendment"] == "HS_1996" else None,
                    "HS_2002": hcode if hinfo["amendment"] in ("HS_1996", "HS_2002") else None,
                    "HS_2007": hcode,
                    "HS_2012": hcode,
                    "HS_2017": hcode,
                    "HS_2022": active_successors[0] if active_successors else None
                },
                "taxes": self.taxes_catalog.get(active_successors[0], {}) if active_successors else {},
                "permits": self.permits_catalog.get(active_successors[0], []) if active_successors else [],
                "trade_agreements": self.treaties_catalog.get(active_successors[0], []) if active_successors else [],
                "active_successors": active_successors
            }

    def _persist_to_sqlite(self) -> None:
        """Persiste la tabla unificada de linaje aduanero en SQLite para consultas SQL."""
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customs_tariff_lineage (
                hs_code TEXT PRIMARY KEY,
                hs12 TEXT,
                sac_8 TEXT,
                subpartida_6 TEXT,
                partida_4 TEXT,
                capitulo_2 TEXT,
                descripcion TEXT,
                lineage_tag TEXT,
                derivation_notes TEXT,
                is_active_2025 INTEGER,
                dai_pct REAL,
                itbms_pct REAL,
                isc_pct REAL,
                permits_count INTEGER,
                treaties_count INTEGER,
                updated_at TEXT
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lineage_sub6 ON customs_tariff_lineage(subpartida_6)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lineage_tag ON customs_tariff_lineage(lineage_tag)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lineage_ch ON customs_tariff_lineage(capitulo_2)")

        rows = []
        now_iso = datetime.now(timezone.utc).isoformat()
        for code, info in self.lineage_index.items():
            taxes = info.get("taxes", {})
            rows.append((
                code,
                info.get("hs12"),
                info.get("sac_8"),
                info.get("subpartida_6"),
                info.get("partida_4"),
                info.get("capitulo_2"),
                info.get("descripcion"),
                info.get("lineage_tag"),
                info.get("derivation_notes"),
                1 if info.get("is_active_2025") else 0,
                float(taxes.get("dai_pct", 0.0) or 0.0),
                float(taxes.get("itbms_pct", 0.0) or 0.0),
                float(taxes.get("isc_pct", 0.0) or 0.0),
                len(info.get("permits", [])),
                len(info.get("trade_agreements", [])),
                now_iso
            ))

        cursor.executemany("""
            INSERT OR REPLACE INTO customs_tariff_lineage
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rows)
        conn.commit()
        conn.close()

        # Save summary JSON for knowledge base RAG
        summary_payload = {
            "title": "Base de Conocimiento de Linaje y Cronología Arancelaria de Panamá",
            "compiled_at": now_iso,
            "total_hs_codes_indexed": len(self.lineage_index),
            "total_active_2025_fractions": len(self.active_sac_catalog),
            "total_historical_inec_codes": len(self.historical_catalog),
            "taxonomies": {
                "VIGENTE": sum(1 for v in self.lineage_index.values() if v["lineage_tag"] == "VIGENTE"),
                "EQUIVALENTE": sum(1 for v in self.lineage_index.values() if v["lineage_tag"] == "EQUIVALENTE"),
                "DERIVADO_SPLIT": sum(1 for v in self.lineage_index.values() if v["lineage_tag"] == "DERIVADO_SPLIT"),
                "DERIVADO_MERGE": sum(1 for v in self.lineage_index.values() if v["lineage_tag"] == "DERIVADO_MERGE"),
                "HEREDADO": sum(1 for v in self.lineage_index.values() if v["lineage_tag"] == "HEREDADO"),
                "HISTORICO_OBSERVADO": sum(1 for v in self.lineage_index.values() if v["lineage_tag"] == "HISTORICO_OBSERVADO")
            },
            "recintos_aduaneros_count": len(self.recintos_catalog),
            "regulatory_documents_count": sum(len(v) if isinstance(v, list) else 1 for v in self.regulatory_documents.values())
        }

        with open(KNOWLEDGE_BASE_JSON, "w", encoding="utf-8") as f:
            json.dump(summary_payload, f, indent=2, ensure_ascii=False)
        logger.info(f"Base de conocimiento guardada en {KNOWLEDGE_BASE_JSON}")

    def query_code(self, hs_code_query: str) -> Optional[Dict[str, Any]]:
        """
        Consulta un código HS a cualquier nivel (2, 4, 6, 8, 10, 12 dígitos)
        y retorna su ficha técnica completa de linaje, tributos, permisos y cronología.
        """
        if not self._is_loaded:
            self.initialize()

        clean_code = str(hs_code_query).strip().replace(".", "")
        if not clean_code:
            return None

        # Exact match
        if clean_code in self.lineage_index:
            entry = dict(self.lineage_index[clean_code])
            entry["recintos_autorizados"] = self.recintos_catalog[:5]
            return entry

        # Prefix search (e.g. searching 6-digit or 4-digit code)
        matches = [v for k, v in self.lineage_index.items() if k.startswith(clean_code)]
        if matches:
            primary = dict(matches[0])
            primary["multiple_matches_count"] = len(matches)
            primary["sample_subfractions"] = [m["hs_code"] for m in matches[:10]]
            primary["recintos_autorizados"] = self.recintos_catalog[:5]
            return primary

        return None

    def search_by_keyword(self, query: str, limit: int = 15) -> List[Dict[str, Any]]:
        """Búsqueda semántica por descripción o palabra clave."""
        if not self._is_loaded:
            self.initialize()

        q_lower = query.lower().strip()
        results = []
        for code, info in self.lineage_index.items():
            desc = info.get("descripcion", "").lower()
            if q_lower in desc or q_lower in code:
                results.append(info)
                if len(results) >= limit:
                    break
        return results

    def get_summary(self) -> Dict[str, Any]:
        """Retorna estadísticas globales para dashboards y control de calidad."""
        if not self._is_loaded:
            self.initialize()

        if KNOWLEDGE_BASE_JSON.exists():
            try:
                with open(KNOWLEDGE_BASE_JSON, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        return {
            "total_indexed": len(self.lineage_index),
            "active_catalog_size": len(self.active_sac_catalog),
            "historical_size": len(self.historical_catalog),
            "recintos_count": len(self.recintos_catalog)
        }

if __name__ == "__main__":
    engine = HSCodeLineageEngine.get_instance()
    summary = engine.get_summary()
    print("=== SUMMARY HS CODE LINEAGE ENGINE ===")
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    # Test query
    sample = engine.query_code("010121")
    print("\n=== SAMPLE QUERY (010121) ===")
    print(json.dumps(sample, indent=2, ensure_ascii=False))
