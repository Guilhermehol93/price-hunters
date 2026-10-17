"""Notification and NotificationDelivery Models"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Numeric, Integer, ForeignKey,
    DateTime
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import GUID, TimestampMixin


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    monitored_product_id = Column(GUID, ForeignKey("monitored_products.id", ondelete="SET NULL"), nullable=True)
    listing_id = Column(GUID, ForeignKey("commercial_listings.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    channel = Column(String(50), nullable=False, default="telegram")
    status = Column(String(50), nullable=False, default="pending")  # 'pending', 'sent', 'failed'
    trigger_price = Column(Numeric(12, 2), nullable=True)
    trigger_discount_pct = Column(Numeric(5, 2), nullable=True)
    trigger_opportunity_score = Column(Integer, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="notifications")
    monitored_product = relationship("MonitoredProduct", back_populates="notifications")
    listing = relationship("CommercialListing")
    deliveries = relationship("NotificationDelivery", back_populates="notification", cascade="all, delete-orphan")


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    notification_id = Column(GUID, ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(String(50), nullable=False)
    attempt_number = Column(Integer, nullable=False, default=1)
    status = Column(String(50), nullable=False)  # 'success', 'failed', 'retry'
    external_response = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    notification = relationship("Notification", back_populates="deliveries")
