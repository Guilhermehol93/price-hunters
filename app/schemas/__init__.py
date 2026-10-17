"""Schemas package initialization"""

from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, VariantResponse
from app.schemas.listing import (
    CommercialListingCreate, CommercialListingResponse,
    ListingDetailResponse, PriceHistoryPoint, StoreSummary
)
from app.schemas.monitoring import (
    MonitoredProductCreate, MonitoredProductResponse,
    AlertRuleCreate, AlertRuleResponse, NotificationResponse
)
from app.schemas.search import (
    SearchSiteResponse, ConnectorConfigResponse,
    SavedSearchCreate, SavedSearchResponse
)
from app.schemas.config import (
    UserPreferenceUpdate, UserPreferenceResponse,
    TelegramTestRequest, TelegramTestResponse
)

__all__ = [
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "VariantResponse",
    "CommercialListingCreate",
    "CommercialListingResponse",
    "ListingDetailResponse",
    "PriceHistoryPoint",
    "StoreSummary",
    "MonitoredProductCreate",
    "MonitoredProductResponse",
    "AlertRuleCreate",
    "AlertRuleResponse",
    "NotificationResponse",
    "SearchSiteResponse",
    "ConnectorConfigResponse",
    "SavedSearchCreate",
    "SavedSearchResponse",
    "UserPreferenceUpdate",
    "UserPreferenceResponse",
    "TelegramTestRequest",
    "TelegramTestResponse",
]
