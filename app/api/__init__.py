"""API Routers Aggregator"""

from fastapi import APIRouter
from app.api.routes_products import router as products_router
from app.api.routes_listings import router as listings_router
from app.api.routes_radar import router as radar_router
from app.api.routes_monitoring import router as monitoring_router
from app.api.routes_connectors import router as connectors_router
from app.api.routes_telegram import router as telegram_router
from app.api.routes_system import router as system_router

api_router = APIRouter(prefix="/api")
api_router.include_router(products_router)
api_router.include_router(listings_router)
api_router.include_router(radar_router)
api_router.include_router(monitoring_router)
api_router.include_router(connectors_router)
api_router.include_router(telegram_router)
api_router.include_router(system_router)

__all__ = ["api_router"]
