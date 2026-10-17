"""Tests for Alert Rules, Cooldown Logic, and Notification Persistence"""

from decimal import Decimal
from datetime import datetime, timedelta
from app.models.user import User
from app.models.store import Store
from app.models.product import Product
from app.models.listing import CommercialListing
from app.models.monitoring import MonitoredProduct, AlertRule
from app.models.notification import Notification
from app.repositories.notification_repo import NotificationRepository


def test_cooldown_detection(db_session):
    repo = NotificationRepository(db_session)

    # Criar dados base
    user = User(email="teste@user.com", full_name="User Teste")
    db_session.add(user)
    db_session.commit()

    store = Store(slug="amazon_test", name="Amazon Teste", domain="amazon.com.br")
    db_session.add(store)
    db_session.commit()

    prod = Product(title="Headset Gamer", category="Audio")
    db_session.add(prod)
    db_session.commit()

    listing = CommercialListing(
        store_id=store.id,
        product_id=prod.id,
        url="https://amazon.com.br/dp/B000",
        title="Headset Gamer 7.1",
        current_price=Decimal("250.00"),
        opportunity_score=80
    )
    db_session.add(listing)
    db_session.commit()

    monitored = MonitoredProduct(
        user_id=user.id,
        product_id=prod.id,
        listing_id=listing.id,
        target_price=Decimal("260.00")
    )
    db_session.add(monitored)
    db_session.commit()

    # Inicialmente não deve haver alerta recente
    assert repo.has_recent_alert(monitored.id, "target_price", cooldown_hours=24) is False

    # Inserir notificação enviada há 2 horas
    notif = Notification(
        user_id=user.id,
        monitored_product_id=monitored.id,
        listing_id=listing.id,
        title="Alerta Teste",
        message="Corpo do alerta",
        channel="telegram",
        status="sent",
        sent_at=datetime.utcnow() - timedelta(hours=2)
    )
    db_session.add(notif)
    db_session.commit()

    # Agora o cooldown de 24 horas deve ser detectado
    assert repo.has_recent_alert(monitored.id, "target_price", cooldown_hours=24) is True

    # Com cooldown de 1 hora, já expirou
    assert repo.has_recent_alert(monitored.id, "target_price", cooldown_hours=1) is False
