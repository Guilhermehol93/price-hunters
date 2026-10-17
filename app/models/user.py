"""User and Preference Models"""

import uuid
from sqlalchemy import Column, String, Boolean, Numeric, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import GUID, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default="user")  # 'admin', 'user', 'viewer'
    is_active = Column(Boolean, nullable=False, default=True)

    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    saved_searches = relationship("SavedSearch", back_populates="user", cascade="all, delete-orphan")
    monitored_products = relationship("MonitoredProduct", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class UserPreference(Base, TimestampMixin):
    __tablename__ = "user_preferences"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    default_discount_threshold = Column(Numeric(5, 2), nullable=False, default=15.00)
    default_opportunity_score_threshold = Column(Integer, nullable=False, default=70)
    telegram_chat_id = Column(String(100), nullable=True)
    notify_by_telegram = Column(Boolean, nullable=False, default=True)
    notify_by_email = Column(Boolean, nullable=False, default=False)
    preferred_currency = Column(String(10), nullable=False, default="BRL")
    theme = Column(String(20), nullable=False, default="dark")

    user = relationship("User", back_populates="preferences")
