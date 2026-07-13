"""End-to-end pipeline tests: snapshot + research -> decision.

Verifies the two headline behaviours:
1. The bot bets on value, not on the highest win probability.
2. "No qualifying bets today" is a reachable, normal outcome.
"""

from datetime import datetime, timedelta, timezone

import pytest

from betfair_bot.config import load_config
from betfair_bot.execution.executor import PaperExecutor
from betfair_bot.modeling.calibration import ShrinkageCalibrator
from betfair_bot.models import MarketSnapshot, PriceSize, RunnerBook, Sport
from betfair_bot.pipeline import DecisionPipeline
from betfair_bot.research.feature_store import FeatureStore
from betfair_bot.research.football import FootballResearch, TeamRating
from betfair_bot.risk.engine import RiskEngine

NOW = datetime(2026, 7, 13, 2, 0, tzinfo=timezone.utc)


def make_market(home_odds, away_odds, draw_odds, size=1000.0):
    def rb(sid, name, odds):
        return RunnerBook(
            sid, name,
            best_back=[PriceSize(odds, size)],
            best_lay=[PriceSize(odds * 1.01, size)],
        )
    return MarketSnapshot(
        market_id="1.1", sport=Sport.FOOTBALL, market_type="MATCH_ODDS",
        event_id="e1", event_name="Home v Away", competition="EPL",
        start_time=NOW + timedelta(hours=6),
        runners=[rb(1, "Home", home_odds), rb(2, "Away", away_odds), rb(3, "The Draw", draw_odds)],
        total_matched=500_000, captured_at=NOW,
    )


def make_pipeline(ratings, calibrator=None):
    cfg = load_config()
    calibrator = calibrator or ShrinkageCalibrator(graded_samples=2000)  # fully trusted model
    store = FeatureStore()
    pipeline = DecisionPipeline(
        cfg, {Sport.FOOTBALL: FootballResearch(ratings=ratings)}, store,
        calibrator, calibration_quality=0.8,
    )
    return cfg, pipeline


# Model rates Home moderately stronger (~48% win) than the market's ~34%
# implied at odds 3.0 — enough edge to qualify without tripping the
# model-disagreement gate.
VALUE_HOME = {
    "Home": TeamRating(attack=1.05, defence=0.95, sample_size=500),
    "Away": TeamRating(attack=1.00, defence=1.00, sample_size=500),
}
VALUE_ODDS = dict(home_odds=3.0, away_odds=2.7, draw_odds=3.5)


def test_efficient_market_produces_no_bets():
    # Model roughly agrees with the market → nothing clears the EV floor.
    ratings = {
        "Home": TeamRating(attack=1.0, defence=1.0, sample_size=500),
        "Away": TeamRating(attack=1.0, defence=1.0, sample_size=500),
    }
    _, pipeline = make_pipeline(ratings)
    # Prices consistent with an even-ish home-advantage match.
    market = make_market(home_odds=2.20, away_odds=3.60, draw_odds=3.40)
    ranked, rejections = pipeline.evaluate_market(market, now=NOW)
    assert ranked == []          # no qualifying bets is a valid outcome
    assert rejections            # and every selection has recorded reasons


def test_mispriced_market_produces_value_bet_not_favourite_bet():
    # Model sees a strong home side but the market prices it as a coin flip.
    _, pipeline = make_pipeline(VALUE_HOME)
    market = make_market(**VALUE_ODDS)
    ranked, _ = pipeline.evaluate_market(market, now=NOW)
    assert ranked, "expected a qualifying opportunity"
    top = ranked[0]
    assert top.selection_name == "Home"
    assert top.expected_value >= pipeline.cfg.selection.minimum_expected_value
    # Estimate exceeds market-implied probability — that's the edge.
    assert top.estimate.probability > 1.0 / top.odds


def test_untrusted_model_shrinks_to_market_and_stays_quiet():
    # Same mispricing, but zero live evidence → shrinkage kills the edge.
    _, pipeline = make_pipeline(VALUE_HOME, calibrator=ShrinkageCalibrator(graded_samples=0))
    market = make_market(**VALUE_ODDS)
    ranked, _ = pipeline.evaluate_market(market, now=NOW)
    assert ranked == []


def test_paper_execution_places_and_sizes_bet():
    cfg, pipeline = make_pipeline(VALUE_HOME)
    market = make_market(**VALUE_ODDS)
    ranked, _ = pipeline.evaluate_market(market, now=NOW)
    # The executor checks book freshness against the wall clock.
    market.captured_at = datetime.now(timezone.utc)
    market.start_time = datetime.now(timezone.utc) + timedelta(hours=6)
    risk = RiskEngine(cfg.risk)
    executor = PaperExecutor(risk, client=None)
    placed = executor.execute(ranked)
    assert len(placed) == 1
    bet = placed[0]
    assert bet.mode == "paper"
    assert bet.status == "MATCHED"
    assert 0 < bet.requested_size <= cfg.risk.maximum_stake_bankroll_pct * cfg.risk.bankroll
    # Exposure recorded in the ledger.
    assert risk.total_open_exposure() == pytest.approx(bet.matched_size)


def test_stop_loss_blocks_execution():
    cfg, pipeline = make_pipeline(VALUE_HOME)
    market = make_market(**VALUE_ODDS)
    ranked, _ = pipeline.evaluate_market(market, now=NOW)
    market.captured_at = datetime.now(timezone.utc)
    market.start_time = datetime.now(timezone.utc) + timedelta(hours=6)
    risk = RiskEngine(cfg.risk)
    risk.ledger.pnl_by_day[datetime.now(timezone.utc).date()] = (
        -cfg.risk.daily_stop_loss_pct * cfg.risk.bankroll - 1
    )
    executor = PaperExecutor(risk, client=None)
    assert executor.execute(ranked) == []
