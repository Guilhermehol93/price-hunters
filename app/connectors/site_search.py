"""Best-effort search for user-provided sites with common search URL patterns."""

import json
import re
from decimal import Decimal, InvalidOperation
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

import httpx
from bs4 import BeautifulSoup

from app.connectors.base import BaseConnector, ScrapedItem
from app.services.ssrf_guard import validate_target_url


class SiteSearchConnector(BaseConnector):
    def __init__(self, search_site: str):
        parsed = urlparse(search_site)
        self.search_site = search_site
        self.hostname = parsed.hostname or "site"
        super().__init__(self.hostname.removeprefix("www."), f"{parsed.scheme}://{parsed.netloc}")

    def build_search_url(self, query: str) -> str:
        parsed = urlparse(self.search_site)
        query_keys = {key.lower() for key, _ in parse_qsl(parsed.query, keep_blank_values=True)}
        key = "k" if "amazon." in self.hostname else "q"
        if "{query}" in self.search_site:
            return self.search_site.replace("{query}", urlencode({"q": query})[2:])
        params = parse_qsl(parsed.query, keep_blank_values=True)
        if not query_keys.intersection({"q", "query", "k", "search", "search_query"}):
            params.append((key, query))
        else:
            params = [(name, query if name.lower() in {"q", "query", "k", "search", "search_query"} else value) for name, value in params]
        return urlunparse(parsed._replace(query=urlencode(params)))

    async def search(self, query: str, limit: int = 20) -> list[ScrapedItem]:
        url = self.build_search_url(query)
        validate_target_url(url)
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; PriceHunter/1.0; +https://pricehunter.local)",
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        }
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=False) as client:
            response = await client.get(url, headers=headers)
        if response.status_code != 200 or "html" not in response.headers.get("content-type", "").lower():
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        page_url = str(response.url)
        items = self._json_ld_items(soup, page_url, limit)
        if items:
            return items
        return self._card_items(soup, page_url, limit)

    def _json_ld_items(self, soup: BeautifulSoup, page_url: str, limit: int) -> list[ScrapedItem]:
        items: list[ScrapedItem] = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or script.get_text())
                objects = data if isinstance(data, list) else data.get("@graph", [data]) if isinstance(data, dict) else []
                for obj in objects:
                    if not isinstance(obj, dict):
                        continue
                    if obj.get("@type") == "ItemList":
                        objects.extend(node.get("item", {}) for node in obj.get("itemListElement", []) if isinstance(node, dict))
                        continue
                    if obj.get("@type") not in {"Product", "IndividualProduct"}:
                        continue
                    offers = obj.get("offers", {})
                    if isinstance(offers, list):
                        offers = offers[0] if offers else {}
                    if not isinstance(offers, dict):
                        continue
                    price = offers.get("price") or offers.get("lowPrice")
                    title = obj.get("name")
                    link = obj.get("url") or obj.get("offers", {}).get("url") if isinstance(obj.get("offers"), dict) else obj.get("url")
                    if not (title and price and link):
                        continue
                    items.append(ScrapedItem(
                        title=str(title)[:500], current_price=Decimal(str(price)),
                        original_price=Decimal(str(offers["highPrice"])) if offers.get("highPrice") else None,
                        currency=offers.get("priceCurrency", "BRL"), url=urljoin(page_url, str(link)),
                        store_slug=self.site_slug, raw_payload={"source": "json-ld"}
                    ))
                    if len(items) >= limit:
                        return items
            except (ValueError, TypeError, InvalidOperation):
                continue
        return items

    def _card_items(self, soup: BeautifulSoup, page_url: str, limit: int) -> list[ScrapedItem]:
        items: list[ScrapedItem] = []
        seen: set[str] = set()
        for card in soup.select("article, [itemtype*=Product], [class*=product], [data-testid*=product]"):
            title_el = card.select_one("h2, h3, [itemprop=name], [class*=title], [class*=name]")
            link_el = card.select_one("a[href]")
            if not title_el or not link_el:
                continue
            title = title_el.get("content") or title_el.get_text(" ", strip=True)
            href = urljoin(page_url, link_el.get("href", ""))
            if not title or href in seen or urlparse(href).hostname != urlparse(page_url).hostname:
                continue
            text = card.get_text(" ", strip=True)
            match = re.search(r"R\$\s*([\d.]+,\d{2}|[\d,]+\.\d{2})", text)
            if not match:
                continue
            raw = match.group(1)
            normalized = raw.replace(".", "").replace(",", ".") if "," in raw else raw
            try:
                price = Decimal(normalized)
            except InvalidOperation:
                continue
            seen.add(href)
            items.append(ScrapedItem(title=title[:500], current_price=price, url=href, store_slug=self.site_slug))
            if len(items) >= limit:
                break
        return items

    async def fetch_product_details(self, url: str):
        return None
