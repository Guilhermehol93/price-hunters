"""Unit Tests for Price Intelligence and Opportunity Scoring Engine"""

from decimal import Decimal
from datetime import datetime, timedelta
from app.models.listing import PriceHistory
from app.services.intelligence import PriceIntelligenceService


def test_empty_history_stats():
    stats = PriceIntelligenceService.calculate_stats([], Decimal("100.00"))
    assert stats["count"] == 0
    assert stats["all_time_min"] == 100.0
    assert stats["all_time_max"] == 100.0
    assert stats["historical_discount_pct"] == 0.0
    assert stats["is_all_time_low"] is True


def test_moving_averages_and_discount():
    now = datetime.utcnow()
    history = [
        PriceHistory(current_price=Decimal("120.00"), observed_at=now - timedelta(days=25)),
        PriceHistory(current_price=Decimal("100.00"), observed_at=now - timedelta(days=15)),
        PriceHistory(current_price=Decimal("110.00"), observed_at=now - timedelta(days=5)),
    ]
    # Média de 30 dias: (120 + 100 + 110) / 3 = 110.00
    # Preço atual: 88.00 -> Desconto: (110 - 88) / 110 = 20%
    stats = PriceIntelligenceService.calculate_stats(history, Decimal("88.00"))
    assert stats["count"] == 3
    assert stats["avg_30d"] == 110.0
    assert stats["all_time_min"] == 100.0
    assert stats["all_time_max"] == 120.0
    assert stats["historical_discount_pct"] == 20.0
    assert stats["is_all_time_low"] is True


def test_fake_discount_detection():
    now = datetime.utcnow()
    history = [
        # Preço original inflacionado para 200, quando máxima real era 120
        PriceHistory(current_price=Decimal("100.00"), original_price=Decimal("200.00"), observed_at=now - timedelta(days=2)),
        PriceHistory(current_price=Decimal("110.00"), original_price=Decimal("110.00"), observed_at=now - timedelta(days=10)),
        PriceHistory(current_price=Decimal("120.00"), original_price=Decimal("120.00"), observed_at=now - timedelta(days=20)),
    ]
    stats = PriceIntelligenceService.calculate_stats(history, Decimal("99.00"))
    assert stats["fake_discount_detected"] is True


def test_opportunity_score_calculation():
    stats = {
        "count": 15,
        "avg_30d": 1000.0,
        "all_time_min": 750.0,
        "fake_discount_detected": False
    }

    # Oferta com 25% de desconto e na mínima histórica:
    score = PriceIntelligenceService.calculate_opportunity_score(
        current_price=Decimal("750.00"),
        stats=stats,
        store_reputation=9.5
    )
    # Deve receber pontuação alta (> 80)
    assert score >= 80

    # Oferta sem desconto frente à média:
    score_no_deal = PriceIntelligenceService.calculate_opportunity_score(
        current_price=Decimal("1000.00"),
        stats=stats,
        store_reputation=8.0
    )
    assert score_no_deal < 50


def test_alert_rule_evaluations():
    # Target price: bateu a meta
    assert PriceIntelligenceService.evaluate_alert(
        rule_type="target_price",
        threshold_value=Decimal("800.00"),
        current_price=Decimal("799.00"),
        opportunity_score=85,
        historical_discount_pct=Decimal("15.0"),
        all_time_min=Decimal("750.00")
    ) is True

    # Target price: acima da meta
    assert PriceIntelligenceService.evaluate_alert(
        rule_type="target_price",
        threshold_value=Decimal("700.00"),
        current_price=Decimal("750.00"),
        opportunity_score=85,
        historical_discount_pct=Decimal("15.0"),
        all_time_min=Decimal("700.00")
    ) is False

    # Score threshold
    assert PriceIntelligenceService.evaluate_alert(
        rule_type="opportunity_score",
        threshold_value=Decimal("80"),
        current_price=Decimal("1000.00"),
        opportunity_score=85,
        historical_discount_pct=Decimal("15.0"),
        all_time_min=Decimal("900.00")
    ) is True
