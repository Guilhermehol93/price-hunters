"""Commercial Listings and Price History API Routes"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.repositories.listing_repo import ListingRepository
from app.schemas.listing import (
    CommercialListingResponse, ListingDetailResponse, PriceHistoryPoint
)
from app.services.intelligence import PriceIntelligenceService

router = APIRouter(prefix="/listings", tags=["Anúncios e Histórico"])


@router.get("/{listing_id}", response_model=ListingDetailResponse)
def get_listing_detail(listing_id: UUID, db: Session = Depends(get_db)):
    repo = ListingRepository(db)
    listing = repo.get_with_relations(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Anúncio não encontrado")

    history = repo.get_history(listing_id, days=90)
    stats = PriceIntelligenceService.calculate_stats(history, listing.current_price)

    return ListingDetailResponse(
        id=listing.id,
        product_id=listing.product_id,
        store_id=listing.store_id,
        store=listing.store,
        external_id=listing.external_id,
        url=listing.url,
        title=listing.title,
        current_price=listing.current_price,
        original_price=listing.original_price,
        currency=listing.currency,
        in_stock=listing.in_stock,
        condition=listing.condition,
        rating=listing.rating,
        reviews_count=listing.reviews_count,
        opportunity_score=listing.opportunity_score,
        historical_discount_pct=listing.historical_discount_pct,
        last_checked_at=listing.last_checked_at,
        is_active=listing.is_active,
        created_at=listing.created_at,
        updated_at=listing.updated_at,
        price_history=[PriceHistoryPoint.model_validate(p) for p in history],
        stats=stats
    )


@router.get("/{listing_id}/history", response_model=list[PriceHistoryPoint])
def get_listing_price_history(
    listing_id: UUID,
    days: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db)
):
    repo = ListingRepository(db)
    history = repo.get_history(listing_id, days=days)
    return [PriceHistoryPoint.model_validate(p) for p in history]
