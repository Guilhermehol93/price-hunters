"""CommercialListing, PriceHistory, and ExternalHistorySource Models"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Numeric, Integer, ForeignKey,
    DateTime, UniqueConstraint, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import GUID, TimestampMixin


class CommercialListing(Base, TimestampMixin):
    __tablename__ = "commercial_listings"
    __table_args__ = (
        UniqueConstraint("store_id", "external_id", name="uq_listings_store_external"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    product_id = Column(GUID, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    variant_id = Column(GUID, ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True)
    store_id = Column(GUID, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    seller_id = Column(GUID, ForeignKey("sellers.id", ondelete="SET NULL"), nullable=True)
    external_id = Column(String(255), nullable=True)
    url = Column(String(1500), nullable=False)
    title = Column(String(500), nullable=False)
    current_price = Column(Numeric(12, 2), nullable=False)
    original_price = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(10), nullable=False, default="BRL")
    in_stock = Column(Boolean, nullable=False, default=True)
    condition = Column(String(50), nullable=False, default="new")
    rating = Column(Numeric(3, 2), nullable=True)
    reviews_count = Column(Integer, default=0)
    opportunity_score = Column(Integer, nullable=False, default=0)
    historical_discount_pct = Column(Numeric(5, 2), nullable=False, default=0.00)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    product = relationship("Product", back_populates="listings")
    variant = relationship("ProductVariant", back_populates="listings")
    store = relationship("Store", back_populates="listings")
    seller = relationship("Seller", back_populates="listings")
    price_history = relationship("PriceHistory", back_populates="listing", cascade="all, delete-orphan", order_by="desc(PriceHistory.observed_at)")
    external_sources = relationship("ExternalHistorySource", back_populates="listing", cascade="all, delete-orphan")
    monitored_entries = relationship("MonitoredProduct", back_populates="listing")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    listing_id = Column(GUID, ForeignKey("commercial_listings.id", ondelete="CASCADE"), nullable=False, index=True)
    current_price = Column(Numeric(12, 2), nullable=False)
    original_price = Column(Numeric(12, 2), nullable=True)
    observed_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    source = Column(String(50), nullable=False, default="crawler")
    raw_payload = Column(JSON, default=dict)

    listing = relationship("CommercialListing", back_populates="price_history")


class ExternalHistorySource(Base, TimestampMixin):
    __tablename__ = "external_history_sources"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    listing_id = Column(GUID, ForeignKey("commercial_listings.id", ondelete="CASCADE"), nullable=False)
    source_name = Column(String(100), nullable=False)
    external_product_id = Column(String(255), nullable=True)
    min_price_observed = Column(Numeric(12, 2), nullable=True)
    max_price_observed = Column(Numeric(12, 2), nullable=True)
    avg_price_observed = Column(Numeric(12, 2), nullable=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    data_points_count = Column(Integer, default=0)
    raw_metadata = Column(JSON, default=dict)

    listing = relationship("CommercialListing", back_populates="external_sources")
