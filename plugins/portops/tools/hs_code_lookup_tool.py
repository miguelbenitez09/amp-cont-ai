"""
Panama Customs HS Code Lookup Tool — PortOps Plugin
Author: Desarrollado v1.0.0 Miguel Benítez - GNU GPL-3.0
"""

from typing import Dict, Any, List
from src.data.scrapers.ana_hscode_scraper import PanamaTariffDatabase


def lookup_hs_code(query: str) -> Dict[str, Any]:
    """Searches official Panama customs tariff database for HS subheadings, DAI, and ITBMS."""
    db = PanamaTariffDatabase()
    results = db.search(query)
    return {
        "query": query,
        "total_results": len(results),
        "results": results[:10]
    }
