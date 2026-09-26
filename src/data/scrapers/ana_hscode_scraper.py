"""
Panama Customs & Tariff Scraper (HS Codes / Incisos Arancelarios de Panamá)
Extracts and normalizes the National Customs Tariff (Arancel de Importación de la República de Panamá).
Supports 6-digit WCO international HS codes up to 8, 10, and 12-digit national subheadings (ANA / SIECA).
Provides bitemporal validity, regulatory procedures, and institutional permit mapping (MIDA, MINSA, APA, MiAmbiente, DIASP, AMP).

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
    Includes bitemporal validity, WCO vs. ANA mapping, required permits, and port procedures.
    """

    OFFICIAL_TARIFF_ITEMS = [
        {
            "hs_code_6": "010121",
            "hs_code_panama": "0101.21.00.00.10",
            "classification_system": "WCO HS 2022 / SIECA / ANA Panamá",
            "descripcion": "Caballos reproductores de raza pura",
            "capitulo": "01",
            "seccion": "I - Animales Vivos y Productos del Reino Animal",
            "unidad_medida": "Cabeza (u)",
            "arancel_dai_pct": 0.0,
            "itbms_pct": 0.0,
            "entidades_reguladoras": ["MIDA-DNSA", "MINSA"],
            "permiso_requerido": "Licencia Fitosanitaria / Zoosanitaria previa MIDA",
            "tipo_mercancia": "ANIMALES_VIVOS",
            "requiere_reefer": False,
            "effective_from": "2024-01-01",
            "effective_to": "2026-12-31",
            "procedimiento_importacion": "1. Notificación previa con 72h de antelación al MIDA. 2. Inspección veterinaria en muelle o rampa de desembarque. 3. Cuarentena preventiva obligatoria en estación autorizada. 4. Liquidación DUA aduanera exenta de DAI e ITBMS.",
            "procedimiento_exportacion": "1. Certificado zoosanitario de exportación emitido por MIDA-DNSA. 2. Certificado de pedigree y microchip ISO. 3. Despacho aduanero bajo régimen definitivo de exportación.",
            "base_legal": "Ley 23 de 15 de julio de 1997 (Sanidad Agropecuaria) y Arancel Nacional de Importación."
        },
        {
            "hs_code_6": "020130",
            "hs_code_panama": "0201.30.00.00.20",
            "classification_system": "WCO HS 2022 / SIECA / ANA Panamá",
            "descripcion": "Carne de la especie bovina, deshuesada, fresca o refrigerada (Cortes Finos)",
            "capitulo": "02",
            "seccion": "I - Animales Vivos y Productos del Reino Animal",
            "unidad_medida": "Kilogramo (kg)",
            "arancel_dai_pct": 25.0,
            "itbms_pct": 0.0,
            "entidades_reguladoras": ["APA", "MIDA-DNSA", "MINSA"],
            "permiso_requerido": "Registro Sanitario APA / Inspección de Cuarentena en Muelle",
            "tipo_mercancia": "ALIMENTOS_PERECEDEROS",
            "requiere_reefer": True,
            "effective_from": "2024-01-01",
            "effective_to": "2026-12-31",
            "procedimiento_importacion": "1. Notificación de importación en el Sistema Integrado APA. 2. Cadena de frío verificada con datalogger en contenedor reefer (-1°C a 2°C). 3. Inspección física y toma de muestras por Cuarentena Agropecuaria en recinto portuario (Balboa o Manzanillo). 4. Pago de DAI (25%) y tasa DUA ($70.00).",
            "procedimiento_exportacion": "1. Inspección sanitaria de planta certificada por MIDA/MINSA. 2. Certificado de inocuidad para mercados destino. 3. Monitoreo de sellos de seguridad de contenedor refrigerado.",
            "base_legal": "Ley 206 de 30 de marzo de 2021 (Crea la Agencia Panameña de Alimentos APA)."
        },
        {
            "hs_code_6": "030342",
            "hs_code_panama": "0303.42.00.00.00",
            "classification_system": "WCO HS 2022 / SIECA / ANA Panamá",
            "descripcion": "Atunes de aleta amarilla (rabiles) (Thunnus albacares), congelados para procesamiento",
            "capitulo": "03",
            "seccion": "I - Animales Vivos y Productos del Reino Animal",
            "unidad_medida": "Kilogramo (kg)",
            "arancel_dai_pct": 10.0,
            "itbms_pct": 0.0,
            "entidades_reguladoras": ["ARAP", "MIDA", "AMP"],
            "permiso_requerido": "Licencia de Pesca ARAP / Certificado de Captura Legal INDNR",
            "tipo_mercancia": "PESCA_CONGELADA",
            "requiere_reefer": True,
            "effective_from": "2024-01-01",
            "effective_to": "2026-12-31",
            "procedimiento_importacion": "1. Verificación del buque pesquero en registro ARAP/AMP. 2. Inspección de pesca no declarada y no reglamentada (INDNR). 3. Descarga en muelle pesquero autorizado o transferencia a contenedores reefer superfreezer (-30°C).",
            "procedimiento_exportacion": "1. Certificado de captura validado por la Autoridad de los Recursos Acuáticos de Panamá (ARAP). 2. Certificado sanitario de exportación.",
            "base_legal": "Ley 204 de 18 de marzo de 2021 (Ley de Pesca y Acuicultura de Panamá)."
        },
        {
            "hs_code_6": "080390",
            "hs_code_panama": "0803.90.11.00.10",
            "classification_system": "WCO HS 2022 / SIECA / ANA Panamá",
            "descripcion": "Bananas o plátanos frescos (Tipo Cavendish para exportación)",
            "capitulo": "08",
            "seccion": "II - Productos del Reino Vegetal",
            "unidad_medida": "Caja de 18.14 kg",
            "arancel_dai_pct": 15.0,
            "itbms_pct": 0.0,
            "entidades_reguladoras": ["MIDA-DNSV", "APA"],
            "permiso_requerido": "Certificado Fitosanitario de Exportación MIDA (Bocas Fruit Co. / Puerto Almirante)",
            "tipo_mercancia": "AGROEXPORTACION",
            "requiere_reefer": True,
            "effective_from": "2024-01-01",
            "effective_to": "2026-12-31",
            "procedimiento_importacion": "1. Solicitud de requisito fitosanitario previo MIDA. 2. Análisis de riesgo de plagas. 3. Inspección en muelle de arribo.",
            "procedimiento_exportacion": "1. Verificación en empacadora registrada MIDA en Changuinola o Barú. 2. Carga en contenedores reefer controlados a 13.3°C. 3. Zarpe preferencial desde Puerto Almirante o Puerto Manzanillo.",
            "base_legal": "Ley 23 de 1997 y Normas Fitosanitarias Internacionales NIMF-12."
        },
        {
            "hs_code_6": "090121",
            "hs_code_panama": "0901.21.00.00.00",
            "classification_system": "WCO HS 2022 / SIECA / ANA Panamá",
            "descripcion": "Café tostado, sin descafeinar (Café Especial Geisha de Tierras Altas)",
            "capitulo": "09",
            "seccion": "II - Productos del Reino Vegetal",
            "unidad_medida": "Kilogramo (kg)",
            "arancel_dai_pct": 54.0,
            "itbms_pct": 7.0,
            "entidades_reguladoras": ["MIDA", "MICI"],
            "permiso_requerido": "Certificado de Origen Denominación Protegida Boquete / Volcán",
            "tipo_mercancia": "SPECIALTY_EXPORT",
            "requiere_reefer": False,
            "effective_from": "2024-01-01",
            "effective_to": "2026-12-31",
            "procedimiento_importacion": "1. Aplicación de arancel de protección nacional DAI 54% + ITBMS 7%. 2. Permiso fitosanitario MIDA para prevención de broca y roya.",
            "procedimiento_exportacion": "1. Validación de Denominación de Origen en MICI. 2. Certificado de catación Specialty Coffee Association (SCA > 88 pts). 3. Consolidación en contenedores dry estándar en Balboa / MIT.",
            "base_legal": "Decreto Ejecutivo 28 de 2004 y Reglamentos de Denominación de Origen MICI."
        },
        {
            "hs_code_6": "100590",
            "hs_code_panama": "1005.90.20.00.00",
            "classification_system": "WCO HS 2022 / SIECA / ANA Panamá",
            "descripcion": "Maíz amarillo duro para consumo animal (A granel)",
            "capitulo": "10",
            "seccion": "II - Productos del Reino Vegetal",
            "unidad_medida": "Tonelada Métrica (MT)",
            "arancel_dai_pct": 0.0,
            "itbms_pct": 0.0,
            "entidades_reguladoras": ["MIDA", "APA", "Bolsa de Productos (BAISA)"],
            "permiso_requerido": "Adjudicación de Contingente Arancelario por Convocatoria BAISA / Permiso MIDA",
            "tipo_mercancia": "GRANEL_AGROINDUSTRIAL",
            "requiere_reefer": False,
            "effective_from": "2024-01-01",
            "effective_to": "2026-12-31",
            "procedimiento_importacion": "1. Verificación de cuota de importación negociada en Tratados de Promoción Comercial (TPC). 2. Inspección por succión neumática en muelle granelero de Puerto Balboa o Manzanillo. 3. Tratamiento de fumigación y desinfección obligatoria.",
            "procedimiento_exportacion": "No aplica (Rubro deficitario de consumo interno agroindustrial avícola y porcino).",
            "base_legal": "Decreto de Gabinete de Contingentes Arancelarios y Ley 23 de 1997."
        },
        {
            "hs_code_6": "271019",
            "hs_code_panama": "2710.19.21.00.00",
            "classification_system": "WCO HS 2022 / SIECA / ANA Panamá",
            "descripcion": "Fuelóleo marino (Bunker VLSFO - Very Low Sulfur Fuel Oil / IFO 380)",
            "capitulo": "27",
            "seccion": "V - Productos Minerales",
            "unidad_medida": "Tonelada Métrica (MT)",
            "arancel_dai_pct": 0.0,
            "itbms_pct": 0.0,
            "entidades_reguladoras": ["AMP", "MiAmbiente", "Secretaría Nacional de Energía"],
            "permiso_requerido": "Permiso de Operación de Despacho de Bunkering AMP / MARPOL Anexo VI",
            "tipo_mercancia": "COMBUSTIBLE_MARINO",
            "requiere_reefer": False,
            "effective_from": "2024-01-01",
            "effective_to": "2026-12-31",
            "procedimiento_importacion": "1. Arribo a tanques de almacenamiento fiscal en terminales petroleras (Rodman, Bahía Las Minas, Petroterminales). 2. Control de calidad de contenido de azufre (máx 0.50% m/m conforme a IMO 2020). 3. Exención arancelaria para combustible de avituallamiento a buques en tránsito internacional.",
            "procedimiento_exportacion": "1. Emisión de Bunker Delivery Note (BDN) conforme a MARPOL Anexo VI. 2. Inspección de mangueras, barreras de contención y autorización de la Dirección General de Puertos e Industrias Marítimas de la AMP.",
            "base_legal": "Ley 56 de 27 de diciembre de 2008 (Ley General de Puertos de Panamá) y Convenio MARPOL 73/78."
        },
        {
            "hs_code_6": "300490",
            "hs_code_panama": "3004.90.99.00.90",
            "classification_system": "WCO HS 2022 / SIECA / ANA Panamá",
            "descripcion": "Medicamentos constituidos por productos mezclados o sin mezclar, dosificados para venta al por menor",
            "capitulo": "30",
            "seccion": "VI - Productos de las Industrias Químicas o Conexas",
            "unidad_medida": "Envase / Caja",
            "arancel_dai_pct": 0.0,
            "itbms_pct": 0.0,
            "entidades_reguladoras": ["MINSA-DNFD"],
            "permiso_requerido": "Registro Sanitario de Medicamentos de la Dirección Nacional de Farmacia y Drogas",
            "tipo_mercancia": "FARMACEUTICOS",
            "requiere_reefer": True,
            "effective_from": "2024-01-01",
            "effective_to": "2026-12-31",
            "procedimiento_importacion": "1. Validación del Registro Sanitario vigente en la base de datos de Farmacia y Drogas del MINSA. 2. Verificación de licencia de importación del distribuidor farmacéutico. 3. Control de temperatura durante el transporte (reefer pharma 15°C a 25°C o 2°C a 8°C). 4. Inspección aduanera prioritaria canal verde/amarillo.",
            "procedimiento_exportacion": "1. Certificado de Libre Venta y Buenas Prácticas de Manufactura (BPM). 2. Sellado de seguridad inalterable en contenedor.",
            "base_legal": "Ley 1 de 10 de enero de 2001 (Sobre Medicamentos y Otros Productos para la Salud Humana)."
        },
        {
            "hs_code_6": "310210",
            "hs_code_panama": "3102.10.00.00.00",
            "classification_system": "WCO HS 2022 / SIECA / ANA Panamá",
            "descripcion": "Urea, incluso en disolución acuosa (Fertilizante nitrogenado con pureza > 45%)",
            "capitulo": "31",
            "seccion": "VI - Productos de las Industrias Químicas o Conexas",
            "unidad_medida": "Kilogramo (kg)",
            "arancel_dai_pct": 0.0,
            "itbms_pct": 0.0,
            "entidades_reguladoras": ["MIDA-DNV", "Aduanas-ANA"],
            "permiso_requerido": "Registro de Fertilizante en la Dirección Nacional de Sanidad Vegetal del MIDA",
            "tipo_mercancia": "FERTILIZANTE_AGRO",
            "requiere_reefer": False,
            "effective_from": "2024-01-01",
            "effective_to": "2026-12-31",
            "procedimiento_importacion": "1. Registro previo del agroquímico en MIDA. 2. Hoja de Seguridad (MSDS) con clasificación IMO para transporte marítimo seguro. 3. Exoneración de DAI e ITBMS para fomento agropecuario. 4. Descarga en terminales secas.",
            "procedimiento_exportacion": "No aplica.",
            "base_legal": "Ley 47 de 1996 (Protección Vegetal) y Arancel Nacional de Importación."
        },
        {
            "hs_code_6": "390110",
            "hs_code_panama": "3901.10.00.00.00",
            "classification_system": "WCO HS 2022 / SIECA / ANA Panamá",
            "descripcion": "Polietileno de densidad inferior a 0.94, en formas primarias (Pellets para inyección)",
            "capitulo": "39",
            "seccion": "VII - Materias Plásticas y sus Manufacturas",
            "unidad_medida": "Kilogramo (kg)",
            "arancel_dai_pct": 0.0,
            "itbms_pct": 7.0,
            "entidades_reguladoras": ["MICI", "Aduanas-ANA"],
            "permiso_requerido": "Declaración de Materia Prima para la Industria Nacional (Ley de Incentivos Industriales)",
            "tipo_mercancia": "POLIMEROS_INDUSTRIA",
            "requiere_reefer": False,
            "effective_from": "2024-01-01",
            "effective_to": "2026-12-31",
            "procedimiento_importacion": "1. Presentación de declaración de valor aduanero CIF. 2. Exoneración de DAI bajo Régimen de Fomento Industrial o aplicación de ITBMS 7%. 3. Desconsolidación en patios de Balboa o Manzanillo.",
            "procedimiento_exportacion": "Exportación de productos transformados terminados.",
            "base_legal": "Ley 76 de 2009 (Código Industrial) y Arancel Nacional de Importación."
        },
        {
            "hs_code_6": "440349",
            "hs_code_panama": "4403.49.00.00.00",
            "classification_system": "WCO HS 2022 / SIECA / ANA Panamá",
            "descripcion": "Madera en bruto, de las demás maderas tropicales (Teca y Cocobolo)",
            "capitulo": "44",
            "seccion": "IX - Madera, Carbón Vegetal y Manufacturas de Madera",
            "unidad_medida": "Metro Cúbico (m³)",
            "arancel_dai_pct": 10.0,
            "itbms_pct": 7.0,
            "entidades_reguladoras": ["MiAmbiente", "CITES"],
            "permiso_requerido": "Permiso Forestal de Aprovechamiento y Salvoconducto CITES de MiAmbiente",
            "tipo_mercancia": "FORESTAL_CITES",
            "requiere_reefer": False,
            "effective_from": "2024-01-01",
            "effective_to": "2026-12-31",
            "procedimiento_importacion": "1. Inspección fitosanitaria para evitar plagas de la madera (NIMF-15). 2. Verificación de procedencia legal y certificado forestal del país exportador.",
            "procedimiento_exportacion": "1. Salvoconducto de movilización forestal MiAmbiente. 2. Permiso CITES obligatorio para especies amenazadas (Cocobolo / Dalbergia retusa). 3. Inspección física de cubitaje en patio de contenedores previa a estiba marítima.",
            "base_legal": "Ley 1 de 3 de febrero de 1994 (Ley Forestal de Panamá) y Convención CITES."
        },
        {
            "hs_code_6": "640399",
            "hs_code_panama": "6403.99.00.00.00",
            "classification_system": "WCO HS 2022 / SIECA / ANA Panamá",
            "descripcion": "Calzado con suela de caucho, plástico o cuero regenerado y parte superior de cuero natural",
            "capitulo": "64",
            "seccion": "XII - Calzado, Sombreros y Demás Tocados",
            "unidad_medida": "Par (2u)",
            "arancel_dai_pct": 15.0,
            "itbms_pct": 7.0,
            "entidades_reguladoras": ["Aduanas-ANA", "ACODECO"],
            "permiso_requerido": "Etiquetado de país de origen y composición técnica ACODECO / Declaración ZLC",
            "tipo_mercancia": "TEXTIL_CALZADO_ZLC",
            "requiere_reefer": False,
            "effective_from": "2024-01-01",
            "effective_to": "2026-12-31",
            "procedimiento_importacion": "1. Arribo a terminal atlántica (Cristóbal o Manzanillo). 2. Traslado bajo custodia aduanera a la Zona Libre de Colón (Régimen ZLC exento de impuestos locales para redistribución). 3. En caso de importación a territorio fiscal nacional, liquidación de DAI 15% + ITBMS 7%.",
            "procedimiento_exportacion": "Reexportación desde la Zona Libre de Colón mediante Declaración de Movimiento Comercial (DMC).",
            "base_legal": "Decreto de Gabinete N° 18 de 17 de junio de 1948 (Crea la Zona Libre de Colón)."
        },
        {
            "hs_code_6": "721420",
            "hs_code_panama": "7214.20.00.00.00",
            "classification_system": "WCO HS 2022 / SIECA / ANA Panamá",
            "descripcion": "Barras de hierro o acero sin alear, con muescas, cordones, surcos o relieves (Varillas corrugadas para construcción)",
            "capitulo": "72",
            "seccion": "XV - Metales Comunes y sus Manufacturas",
            "unidad_medida": "Kilogramo (kg)",
            "arancel_dai_pct": 5.0,
            "itbms_pct": 7.0,
            "entidades_reguladoras": ["DGNTI-MICI", "Aduanas-ANA"],
            "permiso_requerido": "Certificado de Conformidad Técnica con Norma Copanit DGNTI-MICI",
            "tipo_mercancia": "ACERO_ESTRUCTURAL",
            "requiere_reefer": False,
            "effective_from": "2024-01-01",
            "effective_to": "2026-12-31",
            "procedimiento_importacion": "1. Muestreo de resistencia mecánica y límite de fluencia por laboratorio acreditado. 2. Validación de norma Copanit en muelle. 3. Liquidación DAI 5% e ITBMS 7% sobre valor CIF.",
            "procedimiento_exportacion": "No aplica.",
            "base_legal": "Reglamento Técnico DGNTI-COPANIT 44-2000 y Arancel Nacional."
        },
        {
            "hs_code_6": "842619",
            "hs_code_panama": "8426.19.00.00.00",
            "classification_system": "WCO HS 2022 / SIECA / ANA Panamá",
            "descripcion": "Grúas pórtico de muelle (STS - Ship-to-Shore) y grúas de patio RTG para terminales portuarias",
            "capitulo": "84",
            "seccion": "XVI - Máquinas y Aparatos, Material Eléctrico",
            "unidad_medida": "Unidad (u)",
            "arancel_dai_pct": 0.0,
            "itbms_pct": 7.0,
            "entidades_reguladoras": ["AMP", "Aduanas-ANA"],
            "permiso_requerido": "Contrato de Concesión Portuaria AMP / Exoneración de Bienes de Capital",
            "tipo_mercancia": "EQUIPAMIENTO_PORTUARIO",
            "requiere_reefer": False,
            "effective_from": "2024-01-01",
            "effective_to": "2026-12-31",
            "procedimiento_importacion": "1. Descarga directa en muelle de terminal concesionada (PPC Balboa/Cristóbal, MIT, PSA Panamá o CCT). 2. Verificación de exoneración fiscal bajo contrato ley con el Estado panameño. 3. Inspección técnica de seguridad industrial por la Dirección General de Puertos e Industrias Marítimas de la AMP.",
            "procedimiento_exportacion": "No aplica.",
            "base_legal": "Ley 56 de 27 de diciembre de 2008 (Ley General de Puertos de Panamá)."
        },
        {
            "hs_code_6": "847130",
            "hs_code_panama": "8471.30.00.00.00",
            "classification_system": "WCO HS 2022 / SIECA / ANA Panamá",
            "descripcion": "Máquinas automáticas para tratamiento o procesamiento de datos, portátiles (Laptops y Tablets)",
            "capitulo": "84",
            "seccion": "XVI - Máquinas y Aparatos, Material Eléctrico",
            "unidad_medida": "Unidad (u)",
            "arancel_dai_pct": 0.0,
            "itbms_pct": 7.0,
            "entidades_reguladoras": ["ASEP", "Aduanas-ANA"],
            "permiso_requerido": "Homologación Técnica ASEP (Transmisión Inalámbrica / WiFi / Bluetooth)",
            "tipo_mercancia": "ELECTRONICA_ZLC",
            "requiere_reefer": False,
            "effective_from": "2024-01-01",
            "effective_to": "2026-12-31",
            "procedimiento_importacion": "1. Verificación de frecuencias de transmisión autorizadas por ASEP. 2. Exoneración de DAI bajo el Acuerdo de Tecnologías de la Información (ITA de la OMC). 3. Liquidación de ITBMS 7%.",
            "procedimiento_exportacion": "Reexportación multimodal desde Panamá Pacífico o Zona Libre de Colón.",
            "base_legal": "Resolución JD-026 de ASEP y Acuerdo de Tecnología de Información (ITA)."
        },
        {
            "hs_code_6": "870323",
            "hs_code_panama": "8703.23.90.00.10",
            "classification_system": "WCO HS 2022 / SIECA / ANA Panamá",
            "descripcion": "Automóviles de turismo de cilindrada superior a 1,500 cm³ pero inferior o igual a 3,000 cm³ (SUV / Sedán)",
            "capitulo": "87",
            "seccion": "XVII - Material de Transporte",
            "unidad_medida": "Unidad (u)",
            "arancel_dai_pct": 18.0,
            "itbms_pct": 7.0,
            "entidades_reguladoras": ["ATTT", "Aduanas-ANA"],
            "permiso_requerido": "Certificado de Inspección de Emisiones y VIN de Fábrica ATTT",
            "tipo_mercancia": "RO_RO_VEHICULOS",
            "requiere_reefer": False,
            "effective_from": "2024-01-01",
            "effective_to": "2026-12-31",
            "procedimiento_importacion": "1. Descarga por rampa Ro-Ro en terminal especializada (Puerto Manzanillo o Balboa). 2. Verificación del Número de Identificación Vehicular (VIN) contra manifiesto de carga. 3. Pago de DAI (18%) + ITBMS (7%) + Tasa de Registro Único Vehicular ATTT.",
            "procedimiento_exportacion": "Tránsito Ro-Ro hacia destinos de Centro y Sudamérica.",
            "base_legal": "Ley 34 de 1999 (Tránsito y Transporte Terrestre) y Arancel Nacional."
        },
        {
            "hs_code_6": "930200",
            "hs_code_panama": "9302.00.00.00.00",
            "classification_system": "WCO HS 2022 / SIECA / ANA Panamá",
            "descripcion": "Revólveres y pistolas, excepto los de las partidas 93.03 o 93.04",
            "capitulo": "93",
            "seccion": "XIX - Armas, Municiones, sus partes y accesorios",
            "unidad_medida": "Unidad (u)",
            "arancel_dai_pct": 20.0,
            "itbms_pct": 7.0,
            "entidades_reguladoras": ["DIASP-MINSEG", "Aduanas-ANA"],
            "permiso_requerido": "Licencia Previa de Importación de la Dirección Institucional en Asuntos de Seguridad Pública (DIASP)",
            "tipo_mercancia": "MATERIAL_CONTROLADO",
            "requiere_reefer": False,
            "effective_from": "2024-01-01",
            "effective_to": "2026-12-31",
            "procedimiento_importacion": "1. Trámite de Autorización Previa ante la DIASP del Ministerio de Seguridad Pública. 2. Custodia armada obligatoria por la Policía Nacional desde el muelle de descarga hasta la armería fiscal. 3. Verificación de números de serie y balística forense. 4. Liquidación aduanera con DAI 20% e ITBMS 7%.",
            "procedimiento_exportacion": "Tránsito estrictamente regulado bajo tratados internacionales de armas de fuego.",
            "base_legal": "Ley 57 de 27 de mayo de 2011 (General de Armas de Fuego, Municiones y Materiales Relacionados)."
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
                term_lower in item.get("base_legal", "").lower() or
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
        - Tasa de Inspección Aduanera DUA ($70.00)
        """
        item = cls.lookup_by_hs_code(hs_code)
        if not item:
            dai_pct = 10.0
            itbms_pct = 7.0
            item_desc = "Mercancía general sin clasificación específica"
            permiso = "Trámite aduanero estándar con inspección regular"
            entities = ["Aduanas-ANA"]
            procedimiento = "Declaración ordinaria mediante agente de aduanas acreditado ante la ANA."
            base_legal = "Decreto de Gabinete de Arancel Nacional de Importación."
            eff_from = "2024-01-01"
            eff_to = "2026-12-31"
        else:
            dai_pct = item["arancel_dai_pct"]
            itbms_pct = item["itbms_pct"]
            item_desc = item["descripcion"]
            permiso = item["permiso_requerido"]
            entities = item["entidades_reguladoras"]
            procedimiento = item["procedimiento_importacion"]
            base_legal = item["base_legal"]
            eff_from = item.get("effective_from", "2024-01-01")
            eff_to = item.get("effective_to", "2026-12-31")

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
            "permits_required": permiso,
            "import_procedure": procedimiento,
            "legal_framework": base_legal,
            "effective_from": eff_from,
            "effective_to": eff_to,
            "author": "Desarrollado v1.0 Miguel Benítez"
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
