"""Price Intelligence and Deal Scoring Engine"""

import statistics
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Sequence, Optional
from app.models.listing import CommercialListing, PriceHistory


class PriceIntelligenceService:
    """Motor de inteligência estatística de preços e cálculo de pontuação de oportunidade."""

    @staticmethod
    def calculate_stats(history: Sequence[PriceHistory], current_price: Decimal) -> dict:
        """Calcula métricas estatísticas detalhadas a partir do histórico de observações."""
        prices = [float(p.current_price) for p in history if p.current_price > 0]
        curr = float(current_price)

        if not prices:
            return {
                "count": 0,
                "all_time_min": curr,
                "all_time_max": curr,
                "median_price": curr,
                "avg_30d": curr,
                "avg_60d": curr,
                "avg_90d": curr,
                "historical_discount_pct": 0.0,
                "is_all_time_low": True,
                "fake_discount_detected": False,
            }

        all_min = min(prices)
        all_max = max(prices)
        median_val = statistics.median(prices)

        now = datetime.utcnow()
        # Filtros por período
        p30 = [float(p.current_price) for p in history if (now - p.observed_at).days <= 30]
        p60 = [float(p.current_price) for p in history if (now - p.observed_at).days <= 60]
        p90 = [float(p.current_price) for p in history if (now - p.observed_at).days <= 90]

        avg_30 = statistics.mean(p30) if p30 else median_val
        avg_60 = statistics.mean(p60) if p60 else median_val
        avg_90 = statistics.mean(p90) if p90 else median_val

        # Desconto real em relação à média de 30 dias
        if avg_30 > 0 and curr < avg_30:
            hist_discount = round(((avg_30 - curr) / avg_30) * 100.0, 2)
        else:
            hist_discount = 0.0

        is_atl = curr <= all_min

        # Detecção de Maquiagem de Desconto:
        # Se o preço original anunciado for muito superior (ex: +30%) à máxima histórica já observada
        fake_discount = False
        latest_item = history[0] if history else None
        if latest_item and latest_item.original_price:
            orig = float(latest_item.original_price)
            if all_max > 0 and orig > (all_max * 1.30):
                fake_discount = True

        return {
            "count": len(prices),
            "all_time_min": round(all_min, 2),
            "all_time_max": round(all_max, 2),
            "median_price": round(median_val, 2),
            "avg_30d": round(avg_30, 2),
            "avg_60d": round(avg_60, 2),
            "avg_90d": round(avg_90, 2),
            "historical_discount_pct": hist_discount,
            "is_all_time_low": is_atl,
            "fake_discount_detected": fake_discount,
        }

    @staticmethod
    def calculate_opportunity_score(
        current_price: Decimal,
        stats: dict,
        store_reputation: float = 8.0,
        seller_rating: Optional[float] = None
    ) -> int:
        """Calcula o Opportunity Score de 0 a 100.

        Ponderação:
        - 40% Profundidade do desconto frente à média móvel de 30 dias
        - 30% Proximidade do menor preço histórico (All-time low)
        - 15% Confiabilidade da loja e vendedor
        - 15% Densidade estatística (número de observações no histórico)
        """
        curr = float(current_price)
        avg_30 = float(stats.get("avg_30d", curr))
        atl = float(stats.get("all_time_min", curr))
        count = int(stats.get("count", 0))

        # 1. Componente de Desconto (0 - 40 pts)
        discount_pts = 0.0
        if avg_30 > 0:
            discount_pct = ((avg_30 - curr) / avg_30) * 100.0
            if discount_pct > 0:
                # 30% de desconto atinge a pontuação máxima do componente (40 pts)
                discount_pts = min(40.0, (discount_pct / 30.0) * 40.0)

        # 2. Componente de Mínima Histórica (0 - 30 pts)
        atl_pts = 0.0
        if curr <= atl:
            atl_pts = 30.0
        elif atl > 0:
            diff_from_atl_pct = ((curr - atl) / atl) * 100.0
            if diff_from_atl_pct <= 10.0:  # Até 10% acima da mínima histórica
                atl_pts = max(0.0, 30.0 - (diff_from_atl_pct * 3.0))

        # 3. Componente de Reputação (0 - 15 pts)
        rep = float(store_reputation or 8.0)
        rep_norm = min(10.0, max(0.0, rep)) / 10.0  # normaliza 0.0 a 1.0
        rep_pts = rep_norm * 15.0

        # 4. Componente de Confiança Estatística (0 - 15 pts)
        # Mais de 10 observações confere confiança máxima
        density_norm = min(1.0, count / 10.0)
        conf_pts = density_norm * 15.0

        total_score = discount_pts + atl_pts + rep_pts + conf_pts

        # Penalidade severa se fraude / desconto falso for detectado
        if stats.get("fake_discount_detected", False):
            total_score *= 0.60

        return int(round(max(0.0, min(100.0, total_score))))

    @staticmethod
    def evaluate_alert(
        rule_type: str,
        threshold_value: Decimal,
        current_price: Decimal,
        opportunity_score: int,
        historical_discount_pct: Decimal,
        all_time_min: Decimal
    ) -> bool:
        """Avalia se uma regra de alerta foi atingida."""
        thresh = float(threshold_value)
        curr = float(current_price)
        score = int(opportunity_score)
        disc = float(historical_discount_pct)
        atl = float(all_time_min)

        if rule_type == "target_price":
            return curr <= thresh
        elif rule_type == "percentage_drop":
            return disc >= thresh
        elif rule_type == "opportunity_score":
            return score >= thresh
        elif rule_type == "all_time_low":
            return curr <= atl
        return False
