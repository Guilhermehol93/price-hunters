"""Search Sites and Connector Configuration API Routes"""

from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models.search import SearchSite, ConnectorConfig
from app.schemas.search import SearchSiteResponse, ConnectorConfigResponse
from app.connectors.mercadolivre import MercadoLivreConnector
from app.connectors.amazon import AmazonConnector
from app.connectors.zoom import ZoomConnector

router = APIRouter(prefix="/connectors", tags=["Fontes e Conectores"])


@router.get("/sites", response_model=list[SearchSiteResponse])
def list_sites(db: Session = Depends(get_db)):
    stmt = select(SearchSite).order_by(SearchSite.priority.asc())
    return db.scalars(stmt).all()


@router.get("/configs", response_model=list[ConnectorConfigResponse])
def list_configs(db: Session = Depends(get_db)):
    stmt = select(ConnectorConfig).order_by(ConnectorConfig.created_at.asc())
    return db.scalars(stmt).all()


@router.post("/test/{site_slug}")
async def test_connector(site_slug: str, query: str = "monitor gamer", db: Session = Depends(get_db)):
    """Testa a conectividade e scraping de um conector específico"""
    if site_slug == "mercadolivre":
        conn = MercadoLivreConnector()
    elif site_slug in ("amazon_br", "amazon"):
        conn = AmazonConnector()
    elif site_slug in ("zoom", "buscape"):
        conn = ZoomConnector()
    else:
        raise HTTPException(status_code=400, detail=f"Conector desconhecido: {site_slug}")

    try:
        items = await conn.search(query, limit=5)
        # Atualiza status no banco
        stmt = select(ConnectorConfig).join(SearchSite).where(SearchSite.slug == site_slug)
        cfg = db.scalars(stmt).first()
        if cfg:
            cfg.last_tested_at = datetime.utcnow()
            cfg.status = "ok" if items else "degraded"
            db.commit()

        return {
            "status": "success",
            "site": site_slug,
            "items_found": len(items),
            "sample_results": [it.model_dump() for it in items[:3]]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha no teste do conector: {e}")
