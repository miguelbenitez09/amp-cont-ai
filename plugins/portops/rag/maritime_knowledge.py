"""
PortOps Maritime Knowledge Base & RAG Index.
Provides authoritative semantic lookup for Panama maritime operations, terminal specifications, and regulations.

Author: Desarrollado v1.0.0 Miguel Benítez
License: GNU General Public License v3.0 (GPL-3.0) with Section 7 Mandatory Attribution
"""

from typing import List, Dict, Any, Optional


class PortOpsMaritimeKnowledgeBase:
    """In-memory domain knowledge retriever for Panamanian maritime RAG queries."""

    KNOWLEDGE_DOCS = [
        {
            "doc_id": "AMP_PORTS_BALBOA",
            "title": "Puerto de Balboa - Especificaciones y Capacidades",
            "content": "El Puerto de Balboa está ubicado en la entrada pacífica del Canal de Panamá. Cuenta con 25 grúas pórtico STS, calado de 16 metros y capacidad de 5 millones de TEU anuales. Administrado por Panama Ports Company.",
            "jurisdiction": "Panamá Pacífico",
            "authority": "Autoridad Marítima de Panamá (AMP)"
        },
        {
            "doc_id": "AMP_PORTS_MIT",
            "title": "Manzanillo International Terminal (MIT) - Especificaciones",
            "content": "MIT es la principal terminal de transbordo en el litoral Atlántico, ubicada en la Bahía de Manzanillo, Colón. Dispone de 19 grúas pórtico STS, calado de 16.5 metros y acceso directo a la Zona Libre de Colón y autopista Panamá-Colón.",
            "jurisdiction": "Panamá Atlántico",
            "authority": "Autoridad Marítima de Panamá (AMP)"
        },
        {
            "doc_id": "BUNKER_IMO2020",
            "title": "Regulación IMO 2020 y Despacho de Combustible VLSFO en Panamá",
            "content": "Conforme a la regla 14.1.3 del Anexo VI del Convenio MARPOL, desde el 1 de enero de 2020 todos los buques deben usar combustible marino con contenido de azufre máximo de 0.50% masa/masa (VLSFO). Panamá lidera la región con más de 4.8 millones de toneladas métricas suministradas anualmente a través de barcazas autorizadas por la AMP.",
            "jurisdiction": "Nacional e Internacional",
            "authority": "AMP / OMI"
        },
        {
            "doc_id": "ANA_CUSTOMS_PROCEDURES",
            "title": "Procedimientos Aduaneros para Contenedores de Trasbordo",
            "content": "Los contenedores bajo régimen de trasbordo internacional en puertos panameños están exentos de aranceles DAI e ITBMS. La Autoridad Nacional de Aduanas (ANA) requiere la transmisión electrónica del manifiesto de carga consolidado 24 horas antes del arribo del buque.",
            "jurisdiction": "Aduanas República de Panamá",
            "authority": "Autoridad Nacional de Aduanas (ANA)"
        }
    ]

    @classmethod
    def search_knowledge(cls, query: str) -> List[Dict[str, Any]]:
        q = query.lower()
        results = []
        for doc in cls.KNOWLEDGE_DOCS:
            if any(term in doc["content"].lower() or term in doc["title"].lower() for term in q.split()):
                results.append(doc)
        return results if results else cls.KNOWLEDGE_DOCS[:2]
