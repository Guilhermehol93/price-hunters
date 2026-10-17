"""Generic HTML/JSON-LD/OpenGraph Scraper for Any Store URL"""

import json
import re
import logging
from urllib.parse import urlparse
from decimal import Decimal
from typing import Optional
import httpx
from bs4 import BeautifulSoup
from app.connectors.base import BaseConnector, ScrapedItem
from app.services.ssrf_guard import validate_target_url

logger = logging.getLogger(__name__)


class GenericScraper(BaseConnector):
    def __init__(self):
        super().__init__("generic", "")

    async def search(self, query: str, limit: int = 20) -> list[ScrapedItem]:
        # Scraper genérico não realiza busca global
        return []

    async def fetch_product_details(self, url: str) -> Optional[ScrapedItem]:
        validate_target_url(url)
        domain = urlparse(url).netloc.replace("www.", "").split(".")[0]

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        try:
            # Não seguir redirects automaticamente: o alvo não passou pelo SSRF guard.
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=False) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    return None

                soup = BeautifulSoup(resp.text, "html.parser")

                # 1. Tentar extrair via JSON-LD (Schema.org Product)
                item = self._extract_json_ld(soup, url, domain)
                if item:
                    return item

                # 2. Tentar extrair via Meta Tags OpenGraph / Twitter Cards
                item = self._extract_opengraph(soup, url, domain)
                if item:
                    return item

                # 3. Fallback Heurístico HTML
                return self._extract_heuristic(soup, url, domain)

        except Exception as e:
            logger.error(f"Erro no GenericScraper para {url}: {e}")
            return None

    def _extract_json_ld(self, soup: BeautifulSoup, url: str, domain: str) -> Optional[ScrapedItem]:
        scripts = soup.find_all("script", type="application/ld+json")
        for s in scripts:
            try:
                if not s.string:
                    continue
                data = json.loads(s.string)
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    items = data.get("@graph", [data])
                else:
                    continue

                for obj in items:
                    if obj.get("@type") in ("Product", "IndividualProduct"):
                        title = obj.get("name")
                        offers = obj.get("offers", {})
                        if isinstance(offers, list) and offers:
                            offers = offers[0]

                        price_val = offers.get("price") or offers.get("lowPrice")
                        if title and price_val:
                            clean_price = Decimal(str(price_val).replace(",", "."))
                            img = obj.get("image")
                            img_url = img[0] if isinstance(img, list) else img
                            return ScrapedItem(
                                title=title,
                                current_price=clean_price,
                                currency=offers.get("priceCurrency", "BRL"),
                                url=url,
                                store_slug=domain,
                                image_url=img_url,
                                in_stock="InStock" in str(offers.get("availability", "InStock")),
                                raw_payload={"extracted_via": "json-ld"}
                            )
            except Exception:
                continue
        return None

    def _extract_opengraph(self, soup: BeautifulSoup, url: str, domain: str) -> Optional[ScrapedItem]:
        og_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "twitter:title"})
        og_price = soup.find("meta", property="product:price:amount") or soup.find("meta", property="og:price:amount")
        og_image = soup.find("meta", property="og:image")

        if og_title and og_price and og_price.get("content"):
            title = og_title.get("content", "").strip()
            price_raw = og_price.get("content", "").replace(",", ".").strip()
            try:
                price_val = Decimal(price_raw)
                return ScrapedItem(
                    title=title,
                    current_price=price_val,
                    url=url,
                    store_slug=domain,
                    image_url=og_image.get("content") if og_image else None,
                    raw_payload={"extracted_via": "opengraph"}
                )
            except Exception:
                pass
        return None

    def _extract_heuristic(self, soup: BeautifulSoup, url: str, domain: str) -> Optional[ScrapedItem]:
        title_tag = soup.find("h1") or soup.find("title")
        if not title_tag:
            return None
        title = title_tag.get_text(strip=True)

        # Buscar por texto que pareça preço em reais (ex: R$ 1.499,00)
        price_patterns = [
            r"R\$\s*([\d\.]+,\d{2})",
            r"R\$\s*([\d\.]+\.\d{2})"
        ]

        body_text = soup.get_text()
        for pat in price_patterns:
            matches = re.findall(pat, body_text)
            if matches:
                first_match = matches[0].replace(".", "").replace(",", ".")
                try:
                    price_val = Decimal(first_match)
                    if price_val > 0:
                        return ScrapedItem(
                            title=title,
                            current_price=price_val,
                            url=url,
                            store_slug=domain,
                            raw_payload={"extracted_via": "heuristic_regex"}
                        )
                except Exception:
                    continue
        return None
