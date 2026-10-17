"""Mercado Livre Connector"""

import re
import logging
from decimal import Decimal
from typing import Optional
import httpx
from bs4 import BeautifulSoup
from app.connectors.base import BaseConnector, ScrapedItem
from app.services.ssrf_guard import validate_target_url

logger = logging.getLogger(__name__)


class MercadoLivreConnector(BaseConnector):
    def __init__(self):
        super().__init__("mercadolivre", "https://api.mercadolibre.com")

    async def search(self, query: str, limit: int = 20) -> list[ScrapedItem]:
        items: list[ScrapedItem] = []
        # Utiliza a API pública de busca do Mercado Livre Brasil (MLB)
        api_url = f"{self.base_url}/sites/MLB/search"
        params = {"q": query, "limit": min(limit, 50)}

        headers = {
            "User-Agent": "PriceHunter/1.0",
            "Accept": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(api_url, params=params, headers=headers)
                if resp.status_code != 200:
                    logger.warning(f"Mercado Livre API retornou status {resp.status_code}")
                    return items

                data = resp.json()
                results = data.get("results", [])

                for r in results:
                    price_val = r.get("price")
                    if not price_val:
                        continue

                    orig_val = r.get("original_price")
                    items.append(ScrapedItem(
                        title=r.get("title", ""),
                        current_price=Decimal(str(price_val)),
                        original_price=Decimal(str(orig_val)) if orig_val else None,
                        currency=r.get("currency_id", "BRL"),
                        url=r.get("permalink", ""),
                        external_id=r.get("id"),
                        store_slug="mercadolivre",
                        image_url=r.get("thumbnail"),
                        seller_name=r.get("seller", {}).get("nickname"),
                        in_stock=r.get("available_quantity", 1) > 0,
                        raw_payload={"condition": r.get("condition"), "installments": r.get("installments")}
                    ))
        except Exception as e:
            logger.error(f"Erro ao buscar no Mercado Livre: {e}")

        return items

    async def fetch_product_details(self, url: str) -> Optional[ScrapedItem]:
        validate_target_url(url)
        # Extrair ID MLB da URL se existir (ex: MLB-123456789 ou MLB123456789)
        match = re.search(r"MLB-?(\d+)", url)
        if match:
            item_id = f"MLB{match.group(1)}"
            api_url = f"{self.base_url}/items/{item_id}"
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(api_url, headers={"User-Agent": "PriceHunter/1.0"})
                    if resp.status_code == 200:
                        data = resp.json()
                        price_val = data.get("price")
                        orig_val = data.get("original_price")
                        return ScrapedItem(
                            title=data.get("title", ""),
                            current_price=Decimal(str(price_val)),
                            original_price=Decimal(str(orig_val)) if orig_val else None,
                            currency=data.get("currency_id", "BRL"),
                            url=data.get("permalink", url),
                            external_id=data.get("id"),
                            store_slug="mercadolivre",
                            image_url=data.get("pictures", [{}])[0].get("url") if data.get("pictures") else data.get("thumbnail"),
                            in_stock=data.get("available_quantity", 1) > 0,
                            raw_payload=data
                        )
            except Exception as e:
                logger.warning(f"Falha na API direta do ML para {item_id}: {e}")

        # Fallback para parsing HTML
        return await self._scrape_html(url)

    async def _scrape_html(self, url: str) -> Optional[ScrapedItem]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=False) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.text, "html.parser")
            title_tag = soup.select_one("h1.ui-pdp-title") or soup.find("h1")
            title = title_tag.get_text(strip=True) if title_tag else "Produto Mercado Livre"

            price_tag = soup.select_one(".ui-pdp-price__second-line .andes-money-amount__fraction") or soup.select_one(".andes-money-amount__fraction")
            if not price_tag:
                return None

            price_text = price_tag.get_text(strip=True).replace(".", "").replace(",", ".")
            current_price = Decimal(price_text)

            return ScrapedItem(
                title=title,
                current_price=current_price,
                url=url,
                store_slug="mercadolivre"
            )
