"""Pydantic schemas for Commercial Listings and Price History"""

from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field


class PriceHistoryPoint(BaseModel):
    id: UUID
    current_price: Decimal
    original_price: Optional[Decimal] = None
    observed_at: datetime
    source: str

    model_config = ConfigDict(from_attributes=True)


class StoreSummary(BaseModel):
    id: UUID
    slug: str
    name: str
    domain: str
    logo_url: Optional[str] = None
    reputation_score: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class CommercialListingBase(BaseModel):
    url: str
    title: str
    current_price: Decimal
    original_price: Optional[Decimal] = None
    currency: str = "BRL"
    in_stock: bool = True
    condition: str = "new"
    rating: Optional[Decimal] = None
    reviews_count: int = 0
    external_id: Optional[str] = None


class CommercialListingCreate(CommercialListingBase):
    store_slug: str
    product_id: Optional[UUID] = None


class CommercialListingResponse(CommercialListingBase):
    id: UUID
    product_id: Optional[UUID] = None
    store_id: UUID
    store: Optional[StoreSummary] = None
    opportunity_score: int
    historical_discount_pct: Decimal
    last_checked_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ListingDetailResponse(CommercialListingResponse):
    price_history: list[PriceHistoryPoint] = []
    stats: dict[str, Any] = Field(default_factory=dict)
