"""SearchSite, ConnectorConfig, and SavedSearch Models"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Integer, ForeignKey,
    DateTime, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import GUID, TimestampMixin


class SearchSite(Base, TimestampMixin):
    __tablename__ = "search_sites"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    base_url = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False, default=10)

    connectors = relationship("ConnectorConfig", back_populates="site", cascade="all, delete-orphan")
    collection_runs = relationship("CollectionRun", back_populates="site")


class ConnectorConfig(Base, TimestampMixin):
    __tablename__ = "connector_configs"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    site_id = Column(GUID, ForeignKey("search_sites.id", ondelete="CASCADE"), nullable=False)
    connector_type = Column(String(50), nullable=False)
    api_endpoint = Column(String(500), nullable=True)
    rate_limit_per_minute = Column(Integer, nullable=False, default=30)
    timeout_seconds = Column(Integer, nullable=False, default=15)
    headers = Column(JSON, default=dict)
    auth_config = Column(JSON, default=dict)
    custom_settings = Column(JSON, default=dict)
    is_enabled = Column(Boolean, nullable=False, default=True)
    last_tested_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, default="idle")

    site = relationship("SearchSite", back_populates="connectors")


class SavedSearch(Base, TimestampMixin):
    __tablename__ = "saved_searches"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    query_term = Column(String(255), nullable=False)
    filters = Column(JSON, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    execution_frequency_hours = Column(Integer, nullable=False, default=6)
    last_executed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="saved_searches")
