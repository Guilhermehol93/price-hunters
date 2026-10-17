"""MonitoredProduct and AlertRule Models"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Numeric, Integer, ForeignKey,
    DateTime
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import GUID, TimestampMixin


class MonitoredProduct(Base, TimestampMixin):
    __tablename__ = "monitored_products"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(GUID, ForeignKey("products.id", ondelete="CASCADE"), nullable=True)
    listing_id = Column(GUID, ForeignKey("commercial_listings.id", ondelete="SET NULL"), nullable=True)
    target_price = Column(Numeric(12, 2), nullable=True)
    target_discount_pct = Column(Numeric(5, 2), nullable=True)
    check_frequency_minutes = Column(Integer, nullable=False, default=60)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    notify_on_stock = Column(Boolean, nullable=False, default=True)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    last_notified_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="monitored_products")
    product = relationship("Product", back_populates="monitored_entries")
    listing = relationship("CommercialListing", back_populates="monitored_entries")
    alert_rules = relationship("AlertRule", back_populates="monitored_product", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="monitored_product")


class AlertRule(Base, TimestampMixin):
    __tablename__ = "alert_rules"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    monitored_product_id = Column(GUID, ForeignKey("monitored_products.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_type = Column(String(50), nullable=False)  # 'target_price', 'percentage_drop', 'opportunity_score', 'all_time_low'
    threshold_value = Column(Numeric(12, 2), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    cooldown_hours = Column(Integer, nullable=False, default=24)
    channel = Column(String(50), nullable=False, default="telegram")

    monitored_product = relationship("MonitoredProduct", back_populates="alert_rules")
