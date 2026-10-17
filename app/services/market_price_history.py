"""Brazilian electronics price history via Zoom/Buscapé (ReefAPI)."""

import logging
from statistics import mean
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)
REEFAPI_BASE_URL = "https://api.reefapi.com/zoom-buscape/v1"


def _records(data: Any) -> list[dict[str, Any]]:
    """Normalize the provider's common list/envelope shapes."""
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("items", "results", "products", "points"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


async def get_product_price_reference(query: str) -> dict[str, Any] | None:
    """Find a matching Zoom/Buscapé product and summarize its daily price history."""
    api_key = settings.REEFAPI_API_KEY
    if not api_key or not query.strip():
        return None

    headers = {"x-api-key": api_key, "content-type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            search_response = await client.post(
                f"{REEFAPI_BASE_URL}/search",
                headers=headers,
                json={"query": query, "site": "zoom", "page_size": 10},
            )
            search_response.raise_for_status()
            search_payload = search_response.json()
            if not isinstance(search_payload, dict):
                return None
            if not search_payload.get("ok", True):
                logger.info("ReefAPI search retornou erro: %s", search_payload.get("error"))
                return None
            candidates = _records(search_payload.get("data", search_payload))
            product = next(
                (item for item in candidates if item.get("product_id") and item.get("row_type", "product") == "product"),
                None,
            )
            if not product:
                return None

            history_response = await client.post(
                f"{REEFAPI_BASE_URL}/price_history",
                headers=headers,
                json={"product_id": str(product["product_id"]), "period": "12m", "site": "zoom"},
            )
            history_response.raise_for_status()
            history_payload = history_response.json()
            if not isinstance(history_payload, dict):
                return None
            if not history_payload.get("ok", True):
                logger.info("ReefAPI price_history retornou erro: %s", history_payload.get("error"))
                return None

        history_data = history_payload.get("data", history_payload)
        points = _records(history_data)
        prices = []
        for point in points:
            value = point.get("price", point.get("value"))
            try:
                price = float(value)
            except (TypeError, ValueError):
                continue
            if price > 0:
                prices.append(price)
        if not prices and isinstance(history_data, dict):
            for key in ("median", "price_median", "last_price", "price_min"):
                try:
                    value = float(history_data[key])
                    if value > 0:
                        prices.append(value)
                        break
                except (KeyError, TypeError, ValueError):
                    continue
        if len(prices) < 3:
            return None

        return {
            "average_price": round(mean(prices), 2),
            "observations": len(prices),
            "product_title": product.get("title") or product.get("name") or query,
            "source": "Histórico de preços Zoom / Buscapé (via ReefAPI)",
            "source_url": "https://www.zoom.com.br/",
            "license": "API ReefAPI; 1.000 créditos gratuitos na criação da conta, chamadas seguintes conforme plano",
        }
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        logger.info("Histórico Zoom/Buscapé indisponível para '%s': %s", query, exc)
        return None
