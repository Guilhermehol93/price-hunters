"""Deal Radar API Routes - Highlights high opportunity deals"""

import asyncio
from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from urllib.parse import urlparse
from app.database import get_db
from app.repositories.listing_repo import ListingRepository
from app.schemas.listing import CommercialListingResponse
from app.schemas.radar import RadarSearchRequest
from app.connectors.site_search import SiteSearchConnector
from app.connectors.mercadolivre import MercadoLivreConnector
from app.connectors.amazon import AmazonConnector
from app.connectors.zoom import ZoomConnector
from app.services.market_price_history import get_product_price_reference
from app.services.ssrf_guard import SSRFSecurityException, validate_target_url
from app.config import settings

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/radar", tags=["Radar de Ofertas"])


@router.post("/search")
async def search_market_offers(payload: RadarSearchRequest):
    """Search selected storefronts and compare promotions with known reference prices."""
    search_query = payload.query
    if payload.category.casefold() not in search_query.casefold():
        search_query = f"{search_query} {payload.category}"
    market_reference = None
    if payload.use_market_history:
        market_reference = await get_product_price_reference(search_query)
        if market_reference and market_reference["observations"] < 3:
            market_reference = None

    async def search_one_site(raw_site: str):
        site = raw_site.strip()
        if "://" not in site:
            site = f"https://{site}"
        if "{query}" in site:
            site = site.replace("{query}", "")
        try:
            validate_target_url(site)
            host = (urlparse(site).hostname or "").lower()
            if "mercadolivre.com" in host or "mercadolibre.com" in host:
                connector = MercadoLivreConnector()
            elif "amazon." in host:
                connector = AmazonConnector()
            elif "zoom.com" in host or "buscape.com" in host:
                connector = ZoomConnector()
            else:
                connector = SiteSearchConnector(site)
            scraped = await connector.search(search_query, limit=20)
            site_results = []
            for item in scraped:
                if item.currency != "BRL":
                    continue
                reference_price = None
                reference_source = None
                if market_reference and market_reference["average_price"] > float(item.current_price):
                    reference_price = market_reference["average_price"]
                    reference_source = market_reference["source"]
                elif item.original_price and item.original_price > item.current_price:
                    reference_price = float(item.original_price)
                    reference_source = "Preço original informado pela loja"
                if not reference_price:
                    continue
                discount_pct = round((reference_price - float(item.current_price)) / reference_price * 100, 2)
                if discount_pct <= payload.min_discount_pct:
                    continue
                site_results.append({
                    "title": item.title,
                    "current_price": float(item.current_price),
                    "reference_price": reference_price,
                    "discount_pct": discount_pct,
                    "reference_source": reference_source,
                    "url": item.url,
                    "store": item.store_slug,
                    "category": payload.category,
                })
            return site_results, None
        except SSRFSecurityException as exc:
            return [], {"site": raw_site, "error": str(exc)}
        except Exception as exc:
            logger.warning("Falha na busca do Radar no site %s: %s", raw_site, exc, exc_info=True)
            return [], {"site": raw_site, "error": "Falha na consulta deste site."}

    site_responses = await asyncio.gather(*(search_one_site(site) for site in payload.sites))
    results = [offer for offers, _ in site_responses for offer in offers]
    site_errors = [error for _, error in site_responses if error]

    results.sort(key=lambda offer: offer["discount_pct"], reverse=True)
    return {
        "category": payload.category,
        "query": search_query,
        "min_discount_pct": payload.min_discount_pct,
        "results": results,
        "site_errors": site_errors,
        "market_reference": market_reference,
        "market_history_configured": bool(settings.REEFAPI_API_KEY),
    }


@router.get("", response_model=list[CommercialListingResponse])
def get_radar_deals(
    min_score: int = Query(70, ge=0, le=100, description="Pontuação mínima de oportunidade"),
    min_discount: float = Query(10.0, ge=0.0, le=100.0, description="Desconto percentual mínimo frente à média"),
    store: Optional[str] = Query(None, description="Filtrar por slug da loja"),
    category: Optional[str] = Query(None, description="Filtrar por categoria"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    repo = ListingRepository(db)
    try:
        deals = repo.get_radar_deals(
            min_score=min_score,
            min_discount_pct=Decimal(str(min_discount)),
            store_slug=store,
            category=category,
            limit=limit
        )
        # Serialize the ORM objects inside this try block so schema failures
        # are logged and returned as a JSON HTTP error instead of a plain 500.
        return [CommercialListingResponse.model_validate(deal) for deal in deals]
    except Exception as e:
        logger.error(f"Erro ao consultar ou serializar ofertas do radar: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Não foi possível carregar as ofertas do Radar. Verifique o banco de dados e os logs do backend."
        )
