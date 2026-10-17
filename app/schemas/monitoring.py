"""Pydantic schemas for Monitored Products and Alert Rules"""

from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field


class AlertRuleBase(BaseModel):
    rule_type: Literal["target_price", "percentage_drop", "opportunity_score", "all_time_low"]
    threshold_value: Decimal
    is_active: bool = True
    cooldown_hours: int = 24
    channel: Literal["telegram", "email", "webhook"] = "telegram"


class AlertRuleCreate(AlertRuleBase):
    pass


class AlertRuleResponse(AlertRuleBase):
    id: UUID
    monitored_product_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MonitoredProductCreate(BaseModel):
    product_id: Optional[UUID] = None
    listing_id: Optional[UUID] = None
    custom_url: Optional[str] = None  # Cadastro direto por URL
    target_price: Optional[Decimal] = None
    target_discount_pct: Optional[Decimal] = None
    check_frequency_minutes: int = 60
    notify_on_stock: bool = True
    rules: list[AlertRuleCreate] = []


class MonitoredProductResponse(BaseModel):
    id: UUID
    user_id: UUID
    product_id: Optional[UUID] = None
    listing_id: Optional[UUID] = None
    target_price: Optional[Decimal] = None
    target_discount_pct: Optional[Decimal] = None
    check_frequency_minutes: int
    is_active: bool
    notify_on_stock: bool
    last_checked_at: Optional[datetime] = None
    last_notified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    alert_rules: list[AlertRuleResponse] = []

    model_config = ConfigDict(from_attributes=True)


class NotificationResponse(BaseModel):
    id: UUID
    title: str
    message: str
    channel: str
    status: str
    trigger_price: Optional[Decimal] = None
    trigger_discount_pct: Optional[Decimal] = None
    trigger_opportunity_score: Optional[int] = None
    sent_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
