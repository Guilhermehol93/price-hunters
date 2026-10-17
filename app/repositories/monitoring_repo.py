"""MonitoredProduct and AlertRule Repository"""

from uuid import UUID
from datetime import datetime, timedelta
from typing import Optional, Sequence
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from app.models.monitoring import MonitoredProduct, AlertRule
from app.repositories.base import BaseRepository


class MonitoringRepository(BaseRepository[MonitoredProduct]):
    def __init__(self, db: Session):
        super().__init__(MonitoredProduct, db)

    def get_by_user(self, user_id: UUID, is_active_only: bool = True) -> Sequence[MonitoredProduct]:
        stmt = (
            select(MonitoredProduct)
            .options(
                selectinload(MonitoredProduct.alert_rules),
                selectinload(MonitoredProduct.product),
                selectinload(MonitoredProduct.listing)
            )
            .where(MonitoredProduct.user_id == user_id)
        )
        if is_active_only:
            stmt = stmt.where(MonitoredProduct.is_active == True)
        return self.db.scalars(stmt).all()

    def get_due_for_check(self, limit: int = 50) -> Sequence[MonitoredProduct]:
        """Recupera itens ativos cujo intervalo de verificação já expirou"""
        now = datetime.utcnow()
        stmt = (
            select(MonitoredProduct)
            .options(
                selectinload(MonitoredProduct.listing),
                selectinload(MonitoredProduct.alert_rules),
                selectinload(MonitoredProduct.user)
            )
            .where(MonitoredProduct.is_active == True)
            .order_by(MonitoredProduct.last_checked_at.asc().nulls_first())
            .limit(limit)
        )
        candidates = self.db.scalars(stmt).all()
        due = []
        for item in candidates:
            if not item.last_checked_at:
                due.append(item)
            else:
                delta = (now - item.last_checked_at).total_seconds() / 60
                if delta >= item.check_frequency_minutes:
                    due.append(item)
        return due

    def add_alert_rule(self, rule: AlertRule) -> AlertRule:
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule
