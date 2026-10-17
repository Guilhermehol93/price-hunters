"""Pydantic schemas for Search Sites, Connectors, and Saved Searches"""

from uuid import UUID
from datetime import datetime
from typing import Optional, Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class SearchSiteResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    base_url: str
    is_active: bool
    priority: int

    model_config = ConfigDict(from_attributes=True)


class ConnectorConfigResponse(BaseModel):
    id: UUID
    site_id: UUID
    connector_type: str
    rate_limit_per_minute: int
    timeout_seconds: int
    is_enabled: bool
    status: str
    last_tested_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SavedSearchCreate(BaseModel):
    query_term: str
    filters: dict[str, Any] = Field(default_factory=dict)
    execution_frequency_hours: int = 6


class SavedSearchResponse(BaseModel):
    id: UUID
    user_id: UUID
    query_term: str
    filters: dict[str, Any]
    is_active: bool
    execution_frequency_hours: int
    last_executed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
