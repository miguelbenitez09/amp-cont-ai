"""
Maritime & Legal Knowledge Base for Panamanian Port Operations.
Contains structured articles, regulatory decrees, and technical MLOps references.

Author: Desarrollado v1.0 Miguel Benítez
License: GNU GPL-3.0 with Section 7 Mandatory Attribution
"""

from typing import Dict, List


MARITIME_LEGAL_DOCUMENTS: List[Dict[str, str]] = [
    {
        "id": "LEY-56-ART-01",
        "title": "Ley 56 de 2008 (General de Puertos) - Ámbito de Aplicación y Objeto",
        "category": "legislacion_portuaria",
        "content": (
            "La Ley 56 de 27 de diciembre de 2008 regula todos los puertos, terminales e instalaciones "
            "portuarias de la República de Panamá, marítimas o fluviales, de servicio público o privado. "
            "Establece que la Autoridad Marítima de Panamá (AMP) es el ente rector exclusivo de la actividad "
            "portuaria nacional, encargada de fiscalizar el cumplimiento de normativas de eficiencia, "
            "seguridad marítima y competencia leal."
        ),
        "citation": "Gaceta Oficial Digital No. 26194, Ley 56 de 2008, Art. 1-4."
    },
    {
        "id": "LEY-56-ART-18",
        "title": "Ley 56 de 2008 - Régimen de Concesiones y Contratos Portuarios",
        "category": "concesiones",
        "content": (
            "Las concesiones para la administración, construcción y explotación de terminales de contenedores "
            "en puertos estatales (Balboa, Cristóbal, Manzanillo) se otorgan por periodos determinados sujetos a "
            "inversiones mínimas obligatorias en grúas pórtico (STS), dragado de dársenas a un calado mínimo "
            "de 14.5 a 16 metros, y reporte mensual de estadísticas operativas (TEUs llenos y vacíos) a la AMP."
        ),
        "citation": "Ley 56 de 2008, Capítulo III, De las Concesiones Portuarias, Art. 18-25."
    },
    {
        "id": "LEY-6-TRANSPARENCIA",
        "title": "Ley 6 de 2002 - Normas de Transparencia y Acceso Público a la Información",
        "category": "derecho_administrativo",
        "content": (
            "La Ley 6 de 22 de enero de 2002 consagra el principio de máxima publicidad y libre acceso "
            "a la información gubernamental en Panamá. Toda persona natural o jurídica tiene derecho a "
            "solicitar y recibir información completa, veraz y oportuna sobre el movimiento de carga, estadísticas "
            "y gestión portuaria custodiadas por instituciones públicas como la AMP y el INEC, sin necesidad de "
            "justificar su interés, amparando el desarrollo de herramientas de auditoría cívica y educación abierta."
        ),
        "citation": "Gaceta Oficial No. 24476, Ley 6 de 2002 de Transparencia, Art. 1-8."
    },
    {
        "id": "ACP-REG-CALADO",
        "title": "Reglamento de Navegación del Canal de Panamá y Calado Operativo Neopanamax",
        "category": "operaciones_canal",
        "content": (
            "La Autoridad del Canal de Panamá (ACP) emite avisos a la navegación (Advisories to Shipping) "
            "regulando el calado máximo autorizado para tránsitos neopanamax en función del nivel hidrológico "
            "del Lago Gatún. Un nivel normal superior a 85.0 pies permite el calado máximo de 50.0 pies (15.24 m). "
            "Niveles inferiores a 82.0 pies activan restricciones escalonadas de 44.0 pies, obligando a buques "
            "portacontenedores a desembarcar carga en Balboa o Manzanillo para trasbordo vía ferrocarril transístmico."
        ),
        "citation": "Reglamento ACP para la Navegación en Aguas del Canal de Panamá, OP Notice to Shipping."
    },
    {
        "id": "AMP-MLOPS-ARCH",
        "title": "Panamá PortOps-AI: Arquitectura MLOps y Cuantiles P10-P50-P90",
        "category": "tecnologia_mlops",
        "content": (
            "El sistema Panamá PortOps-AI v1.0 desarrollado por Miguel Benítez implementa un ensamble de "
            "LightGBM Quantile Regressors optimizado con pérdida pinball (quantile loss). P50 representa el "
            "escenario mediano no sesgado, mientras que la banda P10-P90 cuantifica la incertidumbre estocástica "
            "asociada a perturbaciones geopolíticas y estacionales. Con un WAPE global de 9.11% y R² de 0.9594, "
            "el sistema supera significativamente a Random Forest y modelos de regresión lineal regularizada."
        ),
        "citation": "Manual Técnico y de Arquitectura MLOps Panamá PortOps-AI v1.0, 2026."
    },
    {
        "id": "AMP-BUNKER-LOGISTICS",
        "title": "Logística de Despacho de Combustible Marino (Bunkering) en Panamá",
        "category": "bunkering",
        "content": (
            "Panamá es el principal hub de bunkering de América Latina. Las barcazas despachan VLSFO "
            "(Very Low Sulfur Fuel Oil con máximo 0.50% azufre) y MGO tanto en el Pacífico (Balboa/Taboga) "
            "como en el Atlántico (Cristóbal/Bahía Las Minas). La relación de despacho búnker por TEU movilizado "
            "es un indicador líder de estadía y demanda de servicios auxiliares marítimos."
        ),
        "citation": "Estadísticas Oficiales AMP de Venta de Combustible Marino a través de Barcazas (2015-2026)."
    }
]
