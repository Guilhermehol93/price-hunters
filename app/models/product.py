"""Product and ProductVariant Models"""

import uuid
from sqlalchemy import Column, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import GUID, TimestampMixin


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    brand = Column(String(100), nullable=True, index=True)
    model = Column(String(100), nullable=True)
    category = Column(String(150), nullable=True, index=True)
    ean_gtin = Column(String(50), nullable=True, index=True)
    image_url = Column(String(1000), nullable=True)
    metadata_json = Column("metadata", JSON, default=dict)

    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    listings = relationship("CommercialListing", back_populates="product")
    monitored_entries = relationship("MonitoredProduct", back_populates="product", cascade="all, delete-orphan")


class ProductVariant(Base, TimestampMixin):
    __tablename__ = "product_variants"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    product_id = Column(GUID, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    sku = Column(String(100), nullable=True)
    title = Column(String(500), nullable=False)
    attributes = Column(JSON, default=dict)

    product = relationship("Product", back_populates="variants")
    listings = relationship("CommercialListing", back_populates="variant")
