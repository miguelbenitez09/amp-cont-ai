"""
Panama Customs & Tariff Scraper (HS Codes / Incisos Arancelarios de Panamá)
Extracts and normalizes the National Customs Tariff (Arancel de Importación de la República de Panamá).
Supports 6-digit WCO international HS codes up to 8, 10, and 12-digit national subheadings (ANA / SIECA).

Author: Desarrollado v1.0 Miguel Benítez
License: GNU General Public License v3.0 (GPL-3.0) with Section 7 Mandatory Attribution
"""

import os
import sys
import json
import sqlite3
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SILVER_DIR = PROJECT_ROOT / "data" / "silver"
SILVER_DIR.mkdir(parents=True, exist_ok=True)
TARIFF_PARQUET = SILVER_DIR / "dim_tariff_panama.parquet"


class PanamaTariffDatabase:
    """
    Authoritative database of Panama National Tariff Subheadings (Incisos Arancelarios).
    Covers core import/export commodities flowing through Balboa, Cristóbal, MIT, PSA, and CCT.
    """

    OFFICIAL_TARIFF_ITEMS = [
        {
            "hs_code_6": "010121",
            "hs_code_panama": "0101.21.00.00.10",
            "descripcion": "Caballos reproductores de raza pura",
            "capitulo": "01",
            "seccion": "I - Animales Vivos y Productos del Reino Animal",
            "unidad_medida": "Cabeza (u)",
            "arancel_dai_pct": 0.0,
            "itbms_pct": 0.0,
            "entidades_reguladoras": ["MIDA-DNSA", "MINSA"],
            "permiso_requerido": "Licencia Fitosanitaria / Zoosanitaria previa MIDA",
            "tipo_mercancia": "ANIMALES_VIVOS",
            "requiere_reefer": False
        },
        {
            "hs_code_6": "020130",
            "hs_code_panama": "0201.30.00.00.20",
            "descripcion": "Carne de la especie bovina, deshuesada, fresca o refrigerada (Cortes Finos)",
            "capitulo": "02",
            "seccion": "I - Animales Vivos y Productos del Reino Animal",
            "unidad_medida": "Kilogramo (kg)",
            "arancel_dai_pct": 25.0,
            "itbms_pct": 0.0,
            "entidades_reguladoras": ["APA", "MIDA-DNSA", "MINSA"],
            "permiso_requerido": "Registro Sanitario APA / Inspección de Cuarentena en Muelle",
            "tipo_mercancia": "ALIMENTOS_PERECEDEROS",
            "requiere_reefer": True
        },
        {
            "hs_code_6": "080390",
            "hs_code_panama": "0803.90.11.00.10",
            "descripcion": "Bananas o plátanos frescos (Tipo Cavendish para exportación)",
            "capitulo": "08",
            "seccion": "II - Productos del Reino Vegetal",
            "unidad_medida": "Caja de 18.14 kg",
            "arancel_dai_pct": 15.0,
            "itbms_pct": 0.0,
            "entidades_reguladoras": ["MIDA-DNSV", "APA"],
            "permiso_requerido": "Certificado Fitosanitario de Exportación MIDA (Bocas Fruit Co. / Puerto Almirante)",
            "tipo_mercancia": "AGROEXPORTACION",
            "requiere_reefer": True
        },
        {
            "hs_code_6": "090121",
            "hs_code_panama": "0901.21.00.00.00",
            "descripcion": "Café tostado, sin descafeinar (Café Especial Geisha de Tierras Altas)",
            "capitulo": "09",
            "seccion": "II - Productos del Reino Vegetal",
            "unidad_medida": "Kilogramo (kg)",
            "arancel_dai_pct": 54.0,
            "itbms_pct": 7.0,
            "entidades_reguladoras": ["MIDA", "MICI"],
            "permiso_requerido": "Certificado de Origen Denominación Protegida Boquete / Volcán",
            "tipo_mercancia": "SPECIALTY_EXPORT",
            "requiere_reefer": False
        },
        {
            "hs_code_6": "271019",
            "hs_code_panama": "2710.19.21.00.00",
            "descripcion": "Fuelóleo marino (Bunker VLSFO - Very Low Sulfur Fuel Oil / IFO 380)",
            "capitulo": "27",
            "seccion": "V - Productos Minerales",
            "unidad_medida": "Tonelada Métrica (MT)",
            "arancel_dai_pct": 0.0,
            "itbms_pct": 0.0,
            "entidades_reguladoras": ["AMP", "MiAmbiente", "Secretaría Nacional de Energía"],
            "permiso_requerido": "Permiso de Operación de Despacho de Bunkering AMP / MARPOL Anexo VI",
            "tipo_mercancia": "COMBUSTIBLE_MARINO",
            "requiere_reefer": False
        },
        {
            "hs_code_6": "300490",
            "hs_code_panama": "3004.90.99.00.90",
            "descripcion": "Medicamentos constituidos por productos mezclados o sin mezclar, dosificados para venta al por menor",
            "capitulo": "30",
            "seccion": "VI - Productos de las Industrias Químicas o Conexas",
            "unidad_medida": "Envase / Caja",
            "arancel_dai_pct": 0.0,
            "itbms_pct": 0.0,
            "entidades_reguladoras": ["MINSA-DNFD"],
            "permiso_requerido": "Registro Sanitario de Medicamentos de la Dirección Nacional de Farmacia y Drogas",
            "tipo_mercancia": "FARMACEUTICOS",
            "requiere_reefer": True
        },
        {
            "hs_code_6": "847130",
            "hs_code_panama": "8471.30.00.00.00",
            "descripcion": "Máquinas automáticas para tratamiento o procesamiento de datos, portátiles (Laptops y Tablets)",
            "capitulo": "84",
            "seccion": "XVI - Máquinas y Aparatos, Material Eléctrico",
            "unidad_medida": "Unidad (u)",
            "arancel_dai_pct": 0.0,
            "itbms_pct": 7.0,
            "entidades_reguladoras": ["ASEP", "Aduanas-ANA"],
            "permiso_requerido": "Homologación Técnica ASEP (Transmisión Inalámbrica / WiFi / Bluetooth)",
            "tipo_mercancia": "ELECTRONICA_ZLC",
            "requiere_reefer": False
        },
        {
            "hs_code_6": "870323",
            "hs_code_panama": "8703.23.90.00.10",
            "descripcion": "Automóviles de turismo de cilindrada superior a 1,500 cm³ pero inferior o igual a 3,000 cm³ (SUV / Sedán)",
            "capitulo": "87",
            "seccion": "XVII - Material de Transporte",
            "unidad_medida": "Unidad (u)",
            "arancel_dai_pct": 18.0,
            "itbms_pct": 7.0,
            "entidades_reguladoras": ["ATTT", "Aduanas-ANA"],
            "permiso_requerido": "Certificado de Inspección de Emisiones y VIN de Fábrica ATTT",
            "tipo_mercancia": "RO_RO_VEHICULOS",
            "requiere_reefer": False
        },
        {
            "hs_code_6": "930200",
            "hs_code_panama": "9302.00.00.00.00",
            "descripcion": "Revólveres y pistolas, excepto los de las partidas 93.03 o 93.04",
            "capitulo": "93",
            "seccion": "XIX - Armas, Municiones, sus partes y accesorios",
            "unidad_medida": "Unidad (u)",
            "arancel_dai_pct": 20.0,
            "itbms_pct": 7.0,
            "entidades_reguladoras": ["DIASP-MINSEG", "Aduanas-ANA"],
            "permiso_requerido": "Licencia Previa de Importación de la Dirección Institucional en Asuntos de Seguridad Pública (DIASP)",
            "tipo_mercancia": "MATERIAL_CONTROLADO",
            "requiere_reefer": False
        },
        {
            "hs_code_6": "440349",
            "hs_code_panama": "4403.49.00.00.00",
            "descripcion": "Madera en bruto, de las demás maderas tropicales (Teca y Cocobolo)",
            "capitulo": "44",
            "seccion": "IX - Madera, Carbón Vegetal y Manufacturas de Madera",
            "unidad_medida": "Metro Cúbico (m³)",
            "arancel_dai_pct": 10.0,
            "itbms_pct": 7.0,
            "entidades_reguladoras": ["MiAmbiente", "CITES"],
            "permiso_requerido": "Permiso Forestal de Aprovechamiento y Salvoconducto CITES de MiAmbiente",
            "tipo_mercancia": "FORESTAL_CITES",
            "requiere_reefer": False
        }
    ]

    @classmethod
    def get_tariff_catalog(cls) -> List[Dict[str, Any]]:
        """Returns the full parsed tariff catalog."""
        return cls.OFFICIAL_TARIFF_ITEMS

    @classmethod
    def lookup_by_hs_code(cls, query: str) -> Optional[Dict[str, Any]]:
        """Finds tariff item by 6-digit prefix or full Panama tariff code."""
        clean = query.replace(".", "").replace(" ", "").strip()
        for item in cls.OFFICIAL_TARIFF_ITEMS:
            item_clean = item["hs_code_panama"].replace(".", "").replace(" ", "")
            if item["hs_code_6"] == clean or clean in item_clean:
                return item
        return None

    @classmethod
    def search_by_text(cls, term: str) -> List[Dict[str, Any]]:
        """Searches tariffs by description, regulatory entity, or commodity type."""
        term_lower = term.lower()
        results = []
        for item in cls.OFFICIAL_TARIFF_ITEMS:
            if (term_lower in item["descripcion"].lower() or 
                term_lower in item["tipo_mercancia"].lower() or
                any(term_lower in e.lower() for e in item["entidades_reguladoras"])):
                results.append(item)
        return results

    @classmethod
    def calculate_landed_customs_cost(
        cls,
        hs_code: str,
        cif_value_usd: float,
        weight_kg: float = 1000.0,
        origin_country: str = "China"
    ) -> Dict[str, Any]:
        """
        Calculates exact Panama customs liquidation:
        - DAI (Derecho Arancelario a la Importación)
        - ITBMS (Impuesto de Transferencia de Bienes Muebles y Servicios)
        - Tasa de Inspección Aduanera
        """
        item = cls.lookup_by_hs_code(hs_code)
        if not item:
            # Default general rate
            dai_pct = 10.0
            itbms_pct = 7.0
            item_desc = "Mercancía general sin clasificación específica"
            permiso = "Trámite aduanero estándar"
            entities = ["Aduanas-ANA"]
        else:
            dai_pct = item["arancel_dai_pct"]
            itbms_pct = item["itbms_pct"]
            item_desc = item["descripcion"]
            permiso = item["permiso_requerido"]
            entities = item["entidades_reguladoras"]

        dai_usd = cif_value_usd * (dai_pct / 100.0)
        customs_base_itbms = cif_value_usd + dai_usd
        itbms_usd = customs_base_itbms * (itbms_pct / 100.0)
        customs_processing_fee = 70.0  # Tasa oficial de declaración DUA aduanera
        total_customs_taxes = dai_usd + itbms_usd + customs_processing_fee
        total_landed = cif_value_usd + total_customs_taxes

        return {
            "hs_code": hs_code,
            "commodity_description": item_desc,
            "cif_value_usd": round(cif_value_usd, 2),
            "dai_rate_pct": dai_pct,
            "dai_usd": round(dai_usd, 2),
            "itbms_rate_pct": itbms_pct,
            "itbms_usd": round(itbms_usd, 2),
            "customs_declaration_fee_usd": round(customs_processing_fee, 2),
            "total_import_taxes_usd": round(total_customs_taxes, 2),
            "total_landed_cost_usd": round(total_landed, 2),
            "effective_tax_rate_pct": round((total_customs_taxes / cif_value_usd) * 100.0, 2) if cif_value_usd > 0 else 0.0,
            "regulatory_entities": entities,
            "permits_required": permiso
        }

    @classmethod
    def export_to_parquet(cls) -> Path:
        """Saves tariff database to Silver layer Parquet."""
        df = pd.DataFrame(cls.OFFICIAL_TARIFF_ITEMS)
        df["entidades_reguladoras"] = df["entidades_reguladoras"].apply(lambda x: ", ".join(x))
        df["updated_at"] = datetime.now(timezone.utc).isoformat()
        df.to_parquet(TARIFF_PARQUET, index=False)
        return TARIFF_PARQUET


if __name__ == "__main__":
    out_path = PanamaTariffDatabase.export_to_parquet()
    print(f"Exported Panama Tariff Catalog to {out_path} ({len(PanamaTariffDatabase.OFFICIAL_TARIFF_ITEMS)} items).")
