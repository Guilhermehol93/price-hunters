"""Store and Seller Models"""

import uuid
from sqlalchemy import Column, String, Boolean, Numeric, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import GUID, TimestampMixin


class Store(Base, TimestampMixin):
    __tablename__ = "stores"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False)
    logo_url = Column(String(500), nullable=True)
    reputation_score = Column(Numeric(4, 2), default=8.00)
    is_active = Column(Boolean, default=True, nullable=False)

    sellers = relationship("Seller", back_populates="store", cascade="all, delete-orphan")
    listings = relationship("CommercialListing", back_populates="store", cascade="all, delete-orphan")


class Seller(Base, TimestampMixin):
    __tablename__ = "sellers"
    __table_args__ = (
        UniqueConstraint("store_id", "external_seller_id", name="uq_sellers_store_external"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    store_id = Column(GUID, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    external_seller_id = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    rating = Column(Numeric(3, 2), nullable=True)
    sales_count = Column(Integer, default=0)
    is_official = Column(Boolean, default=False, nullable=False)

    store = relationship("Store", back_populates="sellers")
    listings = relationship("CommercialListing", back_populates="seller")
