"""Pydantic schemas for System, Preferences, and Telegram settings"""

from uuid import UUID
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserPreferenceUpdate(BaseModel):
    default_discount_threshold: Optional[Decimal] = None
    default_opportunity_score_threshold: Optional[int] = None
    telegram_chat_id: Optional[str] = None
    notify_by_telegram: Optional[bool] = None
    notify_by_email: Optional[bool] = None
    preferred_currency: Optional[str] = None
    theme: Optional[str] = None


class UserPreferenceResponse(BaseModel):
    id: UUID
    user_id: UUID
    default_discount_threshold: Decimal
    default_opportunity_score_threshold: int
    telegram_chat_id: Optional[str] = None
    notify_by_telegram: bool
    notify_by_email: bool
    preferred_currency: str
    theme: str

    model_config = ConfigDict(from_attributes=True)


class TelegramTestRequest(BaseModel):
    chat_id: Optional[str] = None
    message: Optional[str] = None


class TelegramTestResponse(BaseModel):
    success: bool
    chat_id: str
    message_id: Optional[int] = None
    error: Optional[str] = None
