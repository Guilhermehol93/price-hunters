"""Notification and Delivery Repository"""

from uuid import UUID
from datetime import datetime, timedelta
from typing import Optional, Sequence
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, desc
from app.models.notification import Notification, NotificationDelivery
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, db: Session):
        super().__init__(Notification, db)

    def get_by_user(self, user_id: UUID, limit: int = 50) -> Sequence[Notification]:
        stmt = (
            select(Notification)
            .options(selectinload(Notification.deliveries))
            .where(Notification.user_id == user_id)
            .order_by(desc(Notification.created_at))
            .limit(limit)
        )
        return self.db.scalars(stmt).all()

    def has_recent_alert(
        self,
        monitored_product_id: UUID,
        rule_type: str,
        cooldown_hours: int = 24
    ) -> bool:
        """Verifica se já houve alerta recente para prevenir duplicidades"""
        cutoff = datetime.utcnow() - timedelta(hours=cooldown_hours)
        stmt = (
            select(Notification)
            .where(
                Notification.monitored_product_id == monitored_product_id,
                Notification.status == "sent",
                Notification.sent_at >= cutoff
            )
        )
        return self.db.scalars(stmt).first() is not None

    def record_delivery(
        self,
        notification_id: UUID,
        channel: str,
        status: str,
        external_response: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> NotificationDelivery:
        delivery = NotificationDelivery(
            notification_id=notification_id,
            channel=channel,
            status=status,
            external_response=external_response,
            error_message=error_message,
            delivered_at=datetime.utcnow() if status == "success" else None
        )
        self.db.add(delivery)
        self.db.commit()
        self.db.refresh(delivery)
        return delivery
