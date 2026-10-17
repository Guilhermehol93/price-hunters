"""Unit Tests for Connectors and Scraped Item Models"""

from decimal import Decimal
from app.connectors.base import ScrapedItem
from app.connectors import get_connector_for_url
from app.connectors.mercadolivre import MercadoLivreConnector
from app.connectors.amazon import AmazonConnector
from app.connectors.zoom import ZoomConnector
from app.connectors.generic_scraper import GenericScraper


def test_connector_dispatcher():
    conn_ml = get_connector_for_url("https://www.mercadolivre.com.br/produto/p/MLB123")
    assert isinstance(conn_ml, MercadoLivreConnector)

    conn_amz = get_connector_for_url("https://www.amazon.com.br/dp/B0DF1M7R6L")
    assert isinstance(conn_amz, AmazonConnector)

    conn_zoom = get_connector_for_url("https://www.zoom.com.br/search?q=tv")
    assert isinstance(conn_zoom, ZoomConnector)

    conn_gen = get_connector_for_url("https://www.kabum.com.br/produto/12345")
    assert isinstance(conn_gen, GenericScraper)


def test_scraped_item_model():
    item = ScrapedItem(
        title="Teclado Mecânico RGB",
        current_price=Decimal("199.90"),
        original_price=Decimal("299.90"),
        url="https://loja.com/teclado",
        store_slug="loja"
    )
    assert item.title == "Teclado Mecânico RGB"
    assert item.current_price == Decimal("199.90")
    assert item.in_stock is True
