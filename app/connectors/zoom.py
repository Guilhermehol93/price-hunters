"""Zoom / Buscapé Comparator Connector"""

import logging
from decimal import Decimal
from typing import Optional
import httpx
from bs4 import BeautifulSoup
from app.connectors.base import BaseConnector, ScrapedItem
from app.services.ssrf_guard import validate_target_url

logger = logging.getLogger(__name__)


class ZoomConnector(BaseConnector):
    def __init__(self):
        super().__init__("zoom", "https://www.zoom.com.br")

    async def search(self, query: str, limit: int = 20) -> list[ScrapedItem]:
        items: list[ScrapedItem] = []
        search_url = f"{self.base_url}/search"
        params = {"q": query}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=False) as client:
                resp = await client.get(search_url, params=params, headers=headers)
                if resp.status_code != 200:
                    return items

                soup = BeautifulSoup(resp.text, "html.parser")
                cards = soup.select("[data-testid='product-card']") or soup.select(".Hits_ProductCard__1s213")

                for card in cards[:limit]:
                    title_elem = card.select_one("h2") or card.select_one("[data-testid='product-card::name']")
                    price_elem = card.select_one("[data-testid='product-card::price']") or card.select_one(".Text_Text__19ndq")
                    link_elem = card.select_one("a")

                    if not (title_elem and price_elem and link_elem):
                        continue

                    title = title_elem.get_text(strip=True)
                    price_str = price_elem.get_text(strip=True).replace("R$", "").replace(".", "").replace(",", ".").strip()
                    try:
                        price_val = Decimal(price_str)
                    except Exception:
                        continue

                    href = link_elem.get("href", "")
                    full_url = href if href.startswith("http") else f"{self.base_url}{href}"

                    items.append(ScrapedItem(
                        title=title,
                        current_price=price_val,
                        url=full_url,
                        store_slug="zoom"
                    ))
        except Exception as e:
            logger.error(f"Erro ao buscar no Zoom: {e}")

        return items

    async def fetch_product_details(self, url: str) -> Optional[ScrapedItem]:
        validate_target_url(url)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=False) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    return None

                soup = BeautifulSoup(resp.text, "html.parser")
                title_elem = soup.select_one("h1")
                if not title_elem:
                    return None
                title = title_elem.get_text(strip=True)

                price_elem = soup.select_one("[data-testid='price-value']") or soup.select_one(".Price_Value__234")
                if not price_elem:
                    return None

                price_str = price_elem.get_text(strip=True).replace("R$", "").replace(".", "").replace(",", ".").strip()
                return ScrapedItem(
                    title=title,
                    current_price=Decimal(price_str),
                    url=url,
                    store_slug="zoom"
                )
        except Exception as e:
            logger.error(f"Erro ao obter detalhes no Zoom: {e}")
            return None
