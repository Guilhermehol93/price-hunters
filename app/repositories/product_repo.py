"""Product and Variant Repository"""

from uuid import UUID
from typing import Optional, Sequence
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from app.models.product import Product, ProductVariant
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    def __init__(self, db: Session):
        super().__init__(Product, db)

    def list_all(self, skip: int = 0, limit: int = 100) -> Sequence[Product]:
        stmt = (
            select(Product)
            .options(selectinload(Product.variants))
            .offset(skip)
            .limit(limit)
        )
        return self.db.scalars(stmt).all()

    def get_with_variants(self, product_id: UUID) -> Optional[Product]:
        stmt = (
            select(Product)
            .options(selectinload(Product.variants))
            .where(Product.id == product_id)
        )
        return self.db.scalars(stmt).first()

    def search_by_term(self, term: str, limit: int = 50) -> Sequence[Product]:
        pattern = f"%{term}%"
        stmt = (
            select(Product)
            .options(selectinload(Product.variants))
            .where(
                (Product.title.ilike(pattern)) |
                (Product.brand.ilike(pattern)) |
                (Product.category.ilike(pattern)) |
                (Product.ean_gtin == term)
            )
            .limit(limit)
        )
        return self.db.scalars(stmt).all()

    def find_by_ean(self, ean: str) -> Optional[Product]:
        stmt = select(Product).where(Product.ean_gtin == ean)
        return self.db.scalars(stmt).first()
