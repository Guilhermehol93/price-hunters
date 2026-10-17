"""Deal Radar API Routes - Highlights high opportunity deals"""

from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.repositories.listing_repo import ListingRepository
from app.schemas.listing import CommercialListingResponse

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/radar", tags=["Radar de Ofertas"])


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
        return deals
    except Exception as e:
        logger.error(f"Erro ao buscar ofertas no radar: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Não foi possível buscar as ofertas no banco de dados. Verifique a conexão com o PostgreSQL/Supabase."
        )
