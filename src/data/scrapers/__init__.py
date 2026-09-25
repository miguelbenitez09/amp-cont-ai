"""
Scrapers Package for Public Governance and Ministries Feeds.
Author: Desarrollado v1.0 Miguel Benítez
"""

from src.data.scrapers.panama_ministries_scraper import (
    PanamaMinistriesScraper,
    MinistryCatalogEntry
)

__all__ = ["PanamaMinistriesScraper", "MinistryCatalogEntry"]
