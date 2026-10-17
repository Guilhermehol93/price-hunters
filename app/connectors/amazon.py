"""Amazon Brasil Connector"""

import re
import logging
from decimal import Decimal
from typing import Optional
import httpx
from bs4 import BeautifulSoup
from app.connectors.base import BaseConnector, ScrapedItem
from app.services.ssrf_guard import validate_target_url

logger = logging.getLogger(__name__)


class AmazonConnector(BaseConnector):
    def __init__(self):
        super().__init__("amazon_br", "https://www.amazon.com.br")

    async def search(self, query: str, limit: int = 20) -> list[ScrapedItem]:
        items: list[ScrapedItem] = []
        search_url = f"{self.base_url}/s"
        params = {"k": query}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(search_url, params=params, headers=headers)
                if resp.status_code != 200:
                    return items

                soup = BeautifulSoup(resp.text, "html.parser")
                results = soup.select("div[data-component-type='s-search-result']")

                for r in results[:limit]:
                    title_elem = r.select_one("h2 span")
                    price_whole = r.select_one(".a-price-whole")
                    price_frac = r.select_one(".a-price-fraction")
                    link_elem = r.select_one("h2 a")

                    if not (title_elem and price_whole and link_elem):
                        continue

                    whole_str = price_whole.get_text(strip=True).replace(".", "").replace(",", "")
                    frac_str = price_frac.get_text(strip=True) if price_frac else "00"
                    price_val = Decimal(f"{whole_str}.{frac_str}")

                    href = link_elem.get("href", "")
                    full_url = href if href.startswith("http") else f"{self.base_url}{href}"
                    asin = r.get("data-asin")

                    img_elem = r.select_one("img.s-image")
                    img_url = img_elem.get("src") if img_elem else None

                    items.append(ScrapedItem(
                        title=title_elem.get_text(strip=True),
                        current_price=price_val,
                        currency="BRL",
                        url=full_url,
                        external_id=asin,
                        store_slug="amazon",
                        image_url=img_url
                    ))
        except Exception as e:
            logger.error(f"Erro ao buscar na Amazon BR: {e}")

        return items

    async def fetch_product_details(self, url: str) -> Optional[ScrapedItem]:
        validate_target_url(url)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9",
        }
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    return None

                soup = BeautifulSoup(resp.text, "html.parser")
                title_elem = soup.select_one("#productTitle")
                if not title_elem:
                    return None
                title = title_elem.get_text(strip=True)

                # Extrai preço
                price_elem = soup.select_one(".a-price .a-offscreen") or soup.select_one("#priceblock_ourprice")
                if not price_elem:
                    return None

                price_raw = price_elem.get_text(strip=True)
                clean_num = re.sub(r"[^\d,\.]", "", price_raw).replace(".", "").replace(",", ".")
                current_price = Decimal(clean_num)

                # ASIN
                asin_match = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", url)
                asin = asin_match.group(1) if asin_match else None

                return ScrapedItem(
                    title=title,
                    current_price=current_price,
                    url=url,
                    external_id=asin,
                    store_slug="amazon"
                )
        except Exception as e:
            logger.error(f"Erro ao extrair detalhes Amazon para {url}: {e}")
            return None
