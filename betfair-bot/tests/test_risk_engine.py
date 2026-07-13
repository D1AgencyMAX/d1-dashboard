from datetime import datetime, timezone

from betfair_bot.config import RiskConfig
from betfair_bot.models import (
    MarketSnapshot,
    Opportunity,
    PriceSize,
    ProbabilityEstimate,
    RejectionReason,
    RunnerBook,
    Side,
    Sport,
)
from betfair_bot.risk.engine import RiskEngine

NOW = datetime(2026, 7, 13, 2, 0, tzinfo=timezone.utc)


def make_opportunity(event_id="ev1", sport=Sport.FOOTBALL, p=0.45, odds=2.6):
    runner = RunnerBook(selection_id=1, name="Team A", best_back=[PriceSize(odds, 500)])
    market = MarketSnapshot(
        market_id="1.234",
        sport=sport,
        market_type="MATCH_ODDS",
        event_id=event_id,
        event_name="A v B",
        competition="League",
        start_time=datetime(2026, 7, 13, 9, 0, tzinfo=timezone.utc),
        runners=[runner],
    )
    est = ProbabilityEstimate(
        market_id="1.234", selection_id=1, probability=p,
        lower_bound=p - 0.03, upper_bound=p + 0.03, confidence=0.8, sample_size=1000,
    )
    return Opportunity(
        market=market, selection_id=1, selection_name="Team A", side=Side.BACK,
        estimate=est, odds=odds, minimum_acceptable_odds=2.4,
        expected_value=0.08, commission_rate=0.05,
    )


def engine(bankroll=10_000.0):
    return RiskEngine(RiskConfig(bankroll=bankroll, min_stake=1.0))


def test_approves_normal_bet():
    ok, reasons = engine().approve(make_opportunity(), now=NOW)
    assert ok, reasons


def test_daily_stop_loss_blocks():
    e = engine()
    e.ledger.pnl_by_day[NOW.date()] = -0.03 * 10_000  # beyond 2% stop
    ok, reasons = e.approve(make_opportunity(), now=NOW)
    assert not ok
    assert RejectionReason.DAILY_LOSS_LIMIT in reasons


def test_weekly_stop_loss_blocks():
    e = engine()
    for i in range(5):
        from datetime import timedelta
        e.ledger.pnl_by_day[NOW.date() - timedelta(days=i)] = -110.0  # -550 > 5% of 10k
    ok, reasons = e.approve(make_opportunity(), now=NOW)
    assert not ok
    assert RejectionReason.WEEKLY_LOSS_LIMIT in reasons


def test_event_exposure_cap():
    e = engine()
    e.ledger.by_event["ev1"] = 0.0099 * 10_000  # nearly at 1% cap
    ok, reasons = e.approve(make_opportunity(event_id="ev1"), now=NOW)
    assert not ok
    assert RejectionReason.CORRELATED_EXPOSURE in reasons


def test_sport_exposure_cap():
    e = engine()
    e.ledger.by_sport[Sport.FOOTBALL.value] = 0.0299 * 10_000
    ok, reasons = e.approve(make_opportunity(event_id="other"), now=NOW)
    assert not ok
    assert RejectionReason.EXPOSURE_CAP in reasons


def test_halt_blocks_everything():
    e = engine()
    e.halt("test")
    ok, _ = e.approve(make_opportunity(), now=NOW)
    assert not ok


def test_account_discrepancy_halts():
    e = engine()
    e.ledger.by_event["ev1"] = 100.0
    e.verify_account(ledger_exposure=100.0, account_exposure=-250.0, tolerance=1.0)
    assert e.halted


def test_stake_capped_at_half_percent():
    e = engine()
    opp = make_opportunity(p=0.6, odds=3.0)  # huge edge
    assert e.calculate_stake(opp) <= 0.005 * 10_000
