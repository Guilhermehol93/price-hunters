"""Pydantic schemas for Products and Variants"""

from uuid import UUID
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field


class VariantBase(BaseModel):
    sku: Optional[str] = None
    title: str
    attributes: dict[str, Any] = Field(default_factory=dict)


class VariantCreate(VariantBase):
    pass


class VariantResponse(VariantBase):
    id: UUID
    product_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):
    title: str
    description: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    category: Optional[str] = None
    ean_gtin: Optional[str] = None
    image_url: Optional[str] = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    category: Optional[str] = None
    ean_gtin: Optional[str] = None
    image_url: Optional[str] = None
    metadata_json: Optional[dict[str, Any]] = None


class ProductResponse(ProductBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    variants: list[VariantResponse] = []

    model_config = ConfigDict(from_attributes=True)
