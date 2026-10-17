"""System Diagnostics, Health, and Stats API Routes"""

import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.config import settings

router = APIRouter(prefix="/system", tags=["Sistema"])


@router.get("/health")
def healthcheck(db: Session = Depends(get_db)):
    """Health check endpoint utilizado pelo Docker e Portainer"""
    db_ok = False
    error = None
    start = time.perf_counter()
    try:
        db.execute(text("SELECT 1;"))
        db_ok = True
    except Exception as e:
        error = str(e)
    latency_ms = round((time.perf_counter() - start) * 1000, 2)

    return {
        "status": "healthy" if db_ok else "unhealthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": {
            "status": "connected" if db_ok else "disconnected",
            "latency_ms": latency_ms,
            "pool_mode": settings.DB_POOL_MODE,
            "error": error
        }
    }


@router.get("/stats")
def get_system_stats(db: Session = Depends(get_db)):
    """Estatísticas gerais do banco e contadores"""
    def count_table(table_name):
        try:
            return db.execute(text(f"SELECT count(*) FROM {table_name}")).scalar() or 0
        except Exception:
            return 0

    return {
        "products_count": count_table("products"),
        "listings_count": count_table("commercial_listings"),
        "price_history_snapshots": count_table("price_history"),
        "monitored_products_count": count_table("monitored_products"),
        "active_alerts_count": count_table("alert_rules"),
        "stores_count": count_table("stores"),
        "search_sites_count": count_table("search_sites"),
    }
