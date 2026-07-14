from datetime import datetime, timezone

from betfair_bot.config import SelectionConfig
from betfair_bot.models import (
    MarketSnapshot,
    PriceSize,
    ProbabilityEstimate,
    RejectionReason,
    RunnerBook,
    Sport,
)
from betfair_bot.selection.scoring import build_opportunity, check_rejections, rank_opportunities

NOW = datetime(2026, 7, 13, 2, 0, tzinfo=timezone.utc)
COMMISSION = 0.05


def make_market(odds=3.0, size=500.0, hours_to_start=6.0):
    from datetime import timedelta

    runner = RunnerBook(
        selection_id=1, name="Sel", best_back=[PriceSize(odds, size)],
        best_lay=[PriceSize(odds + 0.05, size)],
    )
    return MarketSnapshot(
        market_id="1.1", sport=Sport.FOOTBALL, market_type="MATCH_ODDS",
        event_id="e1", event_name="A v B", competition="X",
        start_time=NOW + timedelta(hours=hours_to_start),
        runners=[runner], total_matched=100_000,
    )


def make_estimate(p=0.40, lb=None, confidence=0.85, n=1000, disagreement=0.02):
    return ProbabilityEstimate(
        market_id="1.1", selection_id=1, probability=p,
        lower_bound=lb if lb is not None else p - 0.02,
        upper_bound=p + 0.02, confidence=confidence,
        sample_size=n, disagreement=disagreement,
    )


def test_good_bet_passes_all_gates():
    reasons = check_rejections(
        make_market(), make_estimate(), odds=3.0, available_size=500,
        cfg=SelectionConfig(), commission=COMMISSION, spread_ticks=1, now=NOW,
    )
    assert reasons == []


def test_favourite_without_value_rejected():
    # 75% winner priced at implied 82% (odds 1.22): high win chance, bad bet.
    reasons = check_rejections(
        make_market(odds=1.22), make_estimate(p=0.75, lb=0.73), odds=1.22,
        available_size=500, cfg=SelectionConfig(), commission=COMMISSION, now=NOW,
    )
    assert RejectionReason.EV_TOO_LOW in reasons


def test_rejects_low_liquidity():
    reasons = check_rejections(
        make_market(size=50), make_estimate(), odds=3.0, available_size=50,
        cfg=SelectionConfig(), commission=COMMISSION, now=NOW,
    )
    assert RejectionReason.INSUFFICIENT_LIQUIDITY in reasons


def test_rejects_low_confidence_and_disagreement():
    reasons = check_rejections(
        make_market(), make_estimate(confidence=0.5, disagreement=0.2), odds=3.0,
        available_size=500, cfg=SelectionConfig(), commission=COMMISSION, now=NOW,
    )
    assert RejectionReason.LOW_CONFIDENCE in reasons
    assert RejectionReason.MODEL_DISAGREEMENT in reasons


def test_rejects_small_sample_and_stale_data():
    reasons = check_rejections(
        make_market(), make_estimate(n=10), odds=3.0, available_size=500,
        cfg=SelectionConfig(), commission=COMMISSION, data_fresh=False, now=NOW,
    )
    assert RejectionReason.SMALL_SAMPLE in reasons
    assert RejectionReason.STALE_DATA in reasons


def test_rejects_starting_too_soon_and_in_play():
    market = make_market(hours_to_start=0.005)  # 18 seconds out
    reasons = check_rejections(
        market, make_estimate(), odds=3.0, available_size=500,
        cfg=SelectionConfig(), commission=COMMISSION, now=NOW,
    )
    assert RejectionReason.STARTS_TOO_SOON in reasons

    market = make_market()
    market.in_play = True
    reasons = check_rejections(
        market, make_estimate(), odds=3.0, available_size=500,
        cfg=SelectionConfig(), commission=COMMISSION, now=NOW,
    )
    assert RejectionReason.MARKET_CLOSED in reasons


def test_rejects_unverified_news_and_missing_selections():
    reasons = check_rejections(
        make_market(), make_estimate(), odds=3.0, available_size=500,
        cfg=SelectionConfig(), commission=COMMISSION,
        has_unverified_material_news=True, selections_confirmed=False, now=NOW,
    )
    assert RejectionReason.UNVERIFIED_NEWS in reasons
    assert RejectionReason.MISSING_SELECTIONS in reasons


def test_lower_bound_gate():
    # Point estimate clears break-even but the lower bound does not.
    reasons = check_rejections(
        make_market(), make_estimate(p=0.40, lb=0.34), odds=3.0,
        available_size=500, cfg=SelectionConfig(), commission=COMMISSION, now=NOW,
    )
    assert RejectionReason.LOWER_BOUND_FAIL in reasons


def test_opportunity_scoring_and_ranking():
    cfg = SelectionConfig()
    market = make_market()
    strong = build_opportunity(market, make_estimate(p=0.45), cfg, COMMISSION,
                               calibration_quality=0.9, source_quality=0.9)
    weak = build_opportunity(market, make_estimate(p=0.37, confidence=0.72), cfg, COMMISSION,
                             calibration_quality=0.4, source_quality=0.3)
    assert strong is not None and weak is not None
    assert strong.expected_value > weak.expected_value
    ranked = rank_opportunities([weak, strong])
    assert ranked[0] is strong
    # Score is a 0..1 weighted blend.
    assert 0.0 <= weak.score <= strong.score <= 1.0
    assert abs(sum(cfg.opportunity_score_weights.values()) - 1.0) < 1e-9
