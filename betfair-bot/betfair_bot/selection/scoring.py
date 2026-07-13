"""Opportunity scoring and automatic rejection rules.

Every candidate first runs the rejection gauntlet; survivors are ranked by a
weighted opportunity score. The bot must be comfortable rejecting everything:
"there are no qualifying bets today" is a valid — and common — outcome.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone

from ..config import SelectionConfig
from ..models import (
    MarketSnapshot,
    Opportunity,
    ProbabilityEstimate,
    RejectionReason,
    Side,
)
from .ev import back_expected_value, minimum_acceptable_odds, passes_conservative_test

log = logging.getLogger(__name__)


def check_rejections(
    market: MarketSnapshot,
    estimate: ProbabilityEstimate,
    odds: float,
    available_size: float,
    cfg: SelectionConfig,
    commission: float,
    *,
    has_unverified_material_news: bool = False,
    selections_confirmed: bool = True,
    api_healthy: bool = True,
    data_fresh: bool = True,
    now: datetime | None = None,
) -> list[RejectionReason]:
    """Run every automatic rejection condition; empty list means eligible."""
    now = now or datetime.now(timezone.utc)
    reasons: list[RejectionReason] = []

    if market.status != "OPEN" or market.in_play:
        reasons.append(RejectionReason.MARKET_CLOSED)
    if market.seconds_to_start(now) < cfg.min_seconds_before_start:
        reasons.append(RejectionReason.STARTS_TOO_SOON)
    if not api_healthy:
        reasons.append(RejectionReason.API_UNHEALTHY)
    if not data_fresh:
        reasons.append(RejectionReason.STALE_DATA)
    if has_unverified_material_news:
        reasons.append(RejectionReason.UNVERIFIED_NEWS)
    if not selections_confirmed:
        reasons.append(RejectionReason.MISSING_SELECTIONS)
    if available_size < cfg.min_available_liquidity:
        reasons.append(RejectionReason.INSUFFICIENT_LIQUIDITY)
    if estimate.confidence < cfg.minimum_model_confidence:
        reasons.append(RejectionReason.LOW_CONFIDENCE)
    if estimate.disagreement > cfg.max_model_disagreement:
        reasons.append(RejectionReason.MODEL_DISAGREEMENT)
    if estimate.sample_size < cfg.min_historical_sample:
        reasons.append(RejectionReason.SMALL_SAMPLE)

    ev = back_expected_value(estimate.probability, odds, commission)
    if ev < cfg.minimum_expected_value:
        reasons.append(RejectionReason.EV_TOO_LOW)
    if not passes_conservative_test(estimate.lower_bound, odds, commission, cfg.safety_margin):
        reasons.append(RejectionReason.LOWER_BOUND_FAIL)

    return reasons


def _liquidity_score(available: float, floor: float) -> float:
    """0..1, saturating around 20x the minimum liquidity requirement."""
    if available <= 0:
        return 0.0
    return min(1.0, math.log10(1.0 + available / max(floor, 1.0)) / math.log10(21.0))


def build_opportunity(
    market: MarketSnapshot,
    estimate: ProbabilityEstimate,
    cfg: SelectionConfig,
    commission: float,
    *,
    source_quality: float = 0.5,
    price_stability: float = 1.0,
    calibration_quality: float = 0.5,
    data_completeness: float = 1.0,
) -> Opportunity | None:
    """Score one selection as a BACK opportunity; None if no executable price."""
    runner = market.runner(estimate.selection_id)
    if runner is None or runner.status != "ACTIVE" or not runner.back_price:
        return None
    odds = runner.back_price
    ev = back_expected_value(estimate.probability, odds, commission)

    w = cfg.opportunity_score_weights
    # EV mapped so the configured floor scores 0 and 3x the floor saturates at 1.
    ev_span = max(cfg.minimum_expected_value * 2.0, 1e-6)
    breakdown = {
        "expected_value": max(0.0, min(1.0, (ev - cfg.minimum_expected_value) / ev_span)),
        "model_confidence": estimate.confidence,
        "calibration_quality": calibration_quality,
        "market_liquidity": _liquidity_score(runner.back_size, cfg.min_available_liquidity),
        "source_quality": source_quality,
        "price_stability": price_stability,
        "data_completeness": data_completeness,
    }
    score = sum(w.get(k, 0.0) * v for k, v in breakdown.items())

    return Opportunity(
        market=market,
        selection_id=estimate.selection_id,
        selection_name=runner.name,
        side=Side.BACK,
        estimate=estimate,
        odds=odds,
        minimum_acceptable_odds=minimum_acceptable_odds(
            estimate.probability, commission, cfg.minimum_expected_value
        ),
        expected_value=ev,
        commission_rate=commission,
        score=score,
        score_breakdown=breakdown,
        source_quality=source_quality,
        price_stability=price_stability,
        calibration_quality=calibration_quality,
        data_completeness=data_completeness,
    )


def rank_opportunities(opportunities: list[Opportunity]) -> list[Opportunity]:
    return sorted(opportunities, key=lambda o: o.score, reverse=True)
