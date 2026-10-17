"""Products and Variants API Routes"""

from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.repositories.product_repo import ProductRepository
from app.models.product import Product, ProductVariant
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter(prefix="/products", tags=["Produtos"])


@router.get("", response_model=list[ProductResponse])
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    q: Optional[str] = None,
    db: Session = Depends(get_db)
):
    repo = ProductRepository(db)
    if q:
        return repo.search_by_term(q, limit=limit)
    return repo.list_all(skip=skip, limit=limit)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: UUID, db: Session = Depends(get_db)):
    repo = ProductRepository(db)
    product = repo.get_with_variants(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return product


@router.post("", response_model=ProductResponse, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    repo = ProductRepository(db)
    new_product = Product(
        title=payload.title,
        description=payload.description,
        brand=payload.brand,
        model=payload.model,
        category=payload.category,
        ean_gtin=payload.ean_gtin,
        image_url=payload.image_url,
        metadata_json=payload.metadata_json
    )
    return repo.create(new_product)
