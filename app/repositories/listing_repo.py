"""CommercialListing and PriceHistory Repository"""

from uuid import UUID
from datetime import datetime, timedelta
from typing import Optional, Sequence
from decimal import Decimal
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, desc
from app.models.listing import CommercialListing, PriceHistory
from app.repositories.base import BaseRepository


class ListingRepository(BaseRepository[CommercialListing]):
    def __init__(self, db: Session):
        super().__init__(CommercialListing, db)

    def get_with_relations(self, listing_id: UUID) -> Optional[CommercialListing]:
        stmt = (
            select(CommercialListing)
            .options(
                selectinload(CommercialListing.store),
                selectinload(CommercialListing.seller),
                selectinload(CommercialListing.price_history),
                selectinload(CommercialListing.product)
            )
            .where(CommercialListing.id == listing_id)
        )
        return self.db.scalars(stmt).first()

    def get_radar_deals(
        self,
        min_score: int = 70,
        min_discount_pct: Decimal = Decimal("10.0"),
        store_slug: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50
    ) -> Sequence[CommercialListing]:
        stmt = (
            select(CommercialListing)
            .options(
                selectinload(CommercialListing.store),
                selectinload(CommercialListing.product)
            )
            .where(
                CommercialListing.is_active == True,
                CommercialListing.in_stock == True,
                CommercialListing.opportunity_score >= min_score,
                CommercialListing.historical_discount_pct >= min_discount_pct
            )
            .order_by(desc(CommercialListing.opportunity_score), desc(CommercialListing.historical_discount_pct))
            .limit(limit)
        )
        return self.db.scalars(stmt).all()

    def find_by_url(self, url: str) -> Optional[CommercialListing]:
        stmt = select(CommercialListing).where(CommercialListing.url == url)
        return self.db.scalars(stmt).first()

    def find_by_store_and_external_id(self, store_id: UUID, external_id: str) -> Optional[CommercialListing]:
        stmt = select(CommercialListing).where(
            CommercialListing.store_id == store_id,
            CommercialListing.external_id == external_id
        )
        return self.db.scalars(stmt).first()

    def get_history(self, listing_id: UUID, days: int = 90) -> Sequence[PriceHistory]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        stmt = (
            select(PriceHistory)
            .where(
                PriceHistory.listing_id == listing_id,
                PriceHistory.observed_at >= cutoff
            )
            .order_by(PriceHistory.observed_at.asc())
        )
        return self.db.scalars(stmt).all()

    def add_price_point(
        self,
        listing_id: UUID,
        current_price: Decimal,
        original_price: Optional[Decimal] = None,
        source: str = "crawler"
    ) -> PriceHistory:
        ph = PriceHistory(
            listing_id=listing_id,
            current_price=current_price,
            original_price=original_price,
            source=source
        )
        self.db.add(ph)
        self.db.commit()
        self.db.refresh(ph)
        return ph
