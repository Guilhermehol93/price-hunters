"""Connectors factory and dispatcher"""

from app.connectors.base import BaseConnector, ScrapedItem
from app.connectors.mercadolivre import MercadoLivreConnector
from app.connectors.amazon import AmazonConnector
from app.connectors.zoom import ZoomConnector
from app.connectors.generic_scraper import GenericScraper


def get_connector_for_url(url: str) -> BaseConnector:
    url_lower = url.lower()
    if "mercadolivre.com" in url_lower or "mercadolibre.com" in url_lower:
        return MercadoLivreConnector()
    elif "amazon.com" in url_lower:
        return AmazonConnector()
    elif "zoom.com" in url_lower or "buscape.com" in url_lower:
        return ZoomConnector()
    else:
        return GenericScraper()


__all__ = [
    "BaseConnector",
    "ScrapedItem",
    "MercadoLivreConnector",
    "AmazonConnector",
    "ZoomConnector",
    "GenericScraper",
    "get_connector_for_url",
]
