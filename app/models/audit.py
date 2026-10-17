"""CollectionRun, CollectionLog, and AuditLog Models"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, ForeignKey,
    DateTime, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import GUID


class CollectionRun(Base):
    __tablename__ = "collection_runs"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    site_id = Column(GUID, ForeignKey("search_sites.id", ondelete="SET NULL"), nullable=True, index=True)
    trigger_type = Column(String(50), nullable=False)  # 'scheduled', 'manual', 'monitoring'
    status = Column(String(50), nullable=False, default="running")  # 'running', 'completed', 'failed', 'cancelled'
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    items_scraped = Column(Integer, default=0, nullable=False)
    items_updated = Column(Integer, default=0, nullable=False)
    errors_count = Column(Integer, default=0, nullable=False)
    log_summary = Column(Text, nullable=True)

    site = relationship("SearchSite", back_populates="collection_runs")
    logs = relationship("CollectionLog", back_populates="run", cascade="all, delete-orphan")


class CollectionLog(Base):
    __tablename__ = "collection_logs"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    run_id = Column(GUID, ForeignKey("collection_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    level = Column(String(20), nullable=False)  # 'info', 'warning', 'error', 'debug'
    message = Column(Text, nullable=False)
    context = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    run = relationship("CollectionRun", back_populates="logs")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(GUID, nullable=True)
    changes = Column(JSON, default=dict)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
