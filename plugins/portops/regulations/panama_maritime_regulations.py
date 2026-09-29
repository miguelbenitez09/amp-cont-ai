"""
Panama Maritime & Port Operations Legal and Regulatory Framework.
Authoritative registry of maritime legislation, port regulations, and trade compliance in the Republic of Panama.

Author: Desarrollado v1.0.0 Miguel Benítez
License: GNU General Public License v3.0 (GPL-3.0) with Section 7 Mandatory Attribution
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class PanamaMaritimeRegulation:
    regulation_id: str
    official_title: str
    law_number: str
    promulgation_date: str
    enforcing_authority: str
    scope_and_applicability: str
    key_articles: List[Dict[str, str]]
    source_url: str


PANAMA_MARITIME_REGULATIONS: List[PanamaMaritimeRegulation] = [
    PanamaMaritimeRegulation(
        regulation_id="LEY_56_2008_PUERTOS",
        official_title="Ley General de Puertos de la República de Panamá",
        law_number="Ley 56 de 27 de diciembre de 2008",
        promulgation_date="2008-12-27",
        enforcing_authority="Autoridad Marítima de Panamá (AMP) - Dirección General de Puertos e Industrias Marítimas",
        scope_and_applicability="Regula la construcción, explotación, operación y administración de las instalaciones portuarias marítimas, fluviales y lacustres, así como los servicios marítimos auxiliares y el régimen de concesiones portuarias.",
        key_articles=[
            {"article": "Artículo 3", "content": "Declara de orden público e interés social todas las actividades relativas a los puertos e industrias marítimas en el territorio nacional."},
            {"article": "Artículo 12", "content": "Atribuciones exclusivas de la AMP para otorgar concesiones y licencias de operación a terminales de contenedores y servicios auxiliares."},
            {"article": "Artículo 45", "content": "Obligatoriedad de inspecciones de seguridad, protección portuaria PBIP/ISPS y cumplimiento de estándares ambientales MARPOL."}
        ],
        source_url="https://amp.gob.pa/marco-legal-puertos/"
    ),
    PanamaMaritimeRegulation(
        regulation_id="LEY_206_2021_APA",
        official_title="Ley que Crea la Agencia Panameña de Alimentos (APA)",
        law_number="Ley 206 de 30 de marzo de 2021",
        promulgation_date="2021-03-30",
        enforcing_authority="Agencia Panameña de Alimentos (APA) en coordinación con MINSA y MIDA",
        scope_and_applicability="Regula los trámites para la emisión de requisitos sanitarios, fitosanitarios, zoosanitarios y de inocuidad para la importación y tránsito de alimentos a través de recintos portuarios.",
        key_articles=[
            {"article": "Artículo 5", "content": "Establece el Sistema Integrado de Trámites de la APA como ventanilla única digital para la autorización de importación de alimentos perecederos."},
            {"article": "Artículo 18", "content": "Verificación estricta de la cadena de frío en contenedores reefer inspeccionados en muelles de Balboa, MIT y Cristóbal."}
        ],
        source_url="https://apa.gob.pa/marco-legal/"
    ),
    PanamaMaritimeRegulation(
        regulation_id="LEY_57_2008_MARINA_MERCANTE",
        official_title="Ley General de Marina Mercante de Panamá",
        law_number="Ley 57 de 6 de agosto de 2008",
        promulgation_date="2008-08-06",
        enforcing_authority="Autoridad Marítima de Panamá (AMP) - Dirección General de Marina Mercante",
        scope_and_applicability="Régimen jurídico del Registro de Naves de Panamá (el mayor registro de abanderamiento de buques del mundo), abanderamiento provisional y definitivo, hipotecas navales y seguridad de la vida humana en el mar.",
        key_articles=[
            {"article": "Artículo 2", "content": "Competencia privativa de la Dirección General de Marina Mercante sobre el abanderamiento de buques de navegación interior e internacional."},
            {"article": "Artículo 34", "content": "Cumplimiento estricto de las normas internacionales de la Organización Marítima Internacional (OMI), SOLAS y MARPOL."}
        ],
        source_url="https://panamashipregistry.com/legal-framework/"
    ),
    PanamaMaritimeRegulation(
        regulation_id="LEY_6_2002_TRANSPARENCIA",
        official_title="Ley de Transparencia en la Gestión Pública",
        law_number="Ley 6 de 22 de enero de 2002",
        promulgation_date="2002-01-22",
        enforcing_authority="ANTAI y todas las entidades gubernamentales de la República de Panamá",
        scope_and_applicability="Establece normas para la transparencia en la gestión pública, consagra el derecho fundamental de acceso a la información estadística y mandata la publicación proactiva de datos portuarios y macroeconómicos.",
        key_articles=[
            {"article": "Artículo 1", "content": "Toda persona tiene derecho a solicitar y recibir información veraz y oportuna de los órganos del Estado."},
            {"article": "Artículo 8", "content": "Obligatoriedad de mantener actualizadas las páginas web institucionales con estadísticas operativas, presupuestarias y contratos de concesión."}
        ],
        source_url="https://www.antai.gob.pa/ley-6-de-2002/"
    )
]


class PanamaRegulationsRegistry:
    """Provides querying and lookup capabilities for Panama maritime regulations."""

    @classmethod
    def list_regulations(cls) -> List[Dict[str, Any]]:
        return [r.__dict__ for r in PANAMA_MARITIME_REGULATIONS]

    @classmethod
    def lookup_regulation(cls, query: str) -> Optional[PanamaMaritimeRegulation]:
        q = query.lower().strip()
        for reg in PANAMA_MARITIME_REGULATIONS:
            if q in reg.regulation_id.lower() or q in reg.law_number.lower() or q in reg.official_title.lower():
                return reg
        return None
