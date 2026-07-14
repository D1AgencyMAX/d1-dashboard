"""Tests for the full cost stack: tick ladder, per-market commission,
premium charge, and spread gating."""

from datetime import datetime, timedelta, timezone

import pytest

from betfair_bot.betfair.ticks import (
    LADDER,
    is_valid_price,
    nearest_tick,
    spread_ticks,
    tick_down,
    tick_up,
    ticks_between,
)
from betfair_bot.config import SelectionConfig
from betfair_bot.models import (
    MarketSnapshot,
    PriceSize,
    ProbabilityEstimate,
    RejectionReason,
    RunnerBook,
    Sport,
)
from betfair_bot.selection.costs import market_commission, relative_spread
from betfair_bot.selection.ev import back_expected_value
from betfair_bot.selection.scoring import build_opportunity, check_rejections

NOW = datetime(2026, 7, 13, 2, 0, tzinfo=timezone.utc)


class TestTickLadder:
    def test_ladder_boundaries(self):
        assert LADDER[0] == 1.01
        assert LADDER[-1] == 1000.0
        # Well-known boundary prices are all valid.
        for p in (1.5, 2.0, 2.02, 3.0, 3.05, 4.0, 4.1, 6.0, 6.2, 10.0, 10.5,
                  20.0, 21.0, 30.0, 32.0, 50.0, 55.0, 100.0, 110.0):
            assert is_valid_price(p), p

    def test_invalid_prices(self):
        for p in (1.005, 2.01, 3.02, 4.05, 7.1, 15.2, 25.5, 101.0):
            assert not is_valid_price(p), p

    def test_nearest_tick(self):
        assert nearest_tick(2.01) == 2.0          # ties round down
        assert nearest_tick(3.07) == 3.05
        assert nearest_tick(3.08) == 3.10
        assert nearest_tick(0.5) == 1.01           # clamped
        assert nearest_tick(5000) == 1000.0

    def test_tick_steps_cross_range_boundaries(self):
        assert tick_up(1.99) == 2.0
        assert tick_up(2.0) == 2.02
        assert tick_down(2.0) == 1.99
        assert tick_up(2.98) == 3.0
        assert tick_up(3.0) == 3.05
        assert tick_down(3.0) == 2.98
        assert tick_down(1.01) == 1.01             # floor
        assert tick_up(1000.0) == 1000.0           # ceiling

    def test_ticks_between_and_spread(self):
        assert ticks_between(2.0, 2.06) == 3
        assert ticks_between(3.0, 3.0) == 0
        assert spread_ticks(2.0, 2.06) == 3
        assert spread_ticks(2.0, None) is None
        assert spread_ticks(None, 2.06) is None


def make_market(mbr=None, back=3.0, lay=3.05, size=500.0):
    runner = RunnerBook(
        selection_id=1, name="Sel",
        best_back=[PriceSize(back, size)],
        best_lay=[PriceSize(lay, size)] if lay else [],
    )
    return MarketSnapshot(
        market_id="1.1", sport=Sport.HORSE_RACING, market_type="WIN",
        event_id="e1", event_name="Race", competition="X",
        start_time=NOW + timedelta(hours=3), runners=[runner],
        total_matched=100_000, market_base_rate=mbr, captured_at=NOW,
    )


class TestCommission:
    def test_market_base_rate_wins_over_fallback(self):
        assert market_commission(make_market(mbr=0.08), fallback_rate=0.05) == 0.08
        assert market_commission(make_market(mbr=None), fallback_rate=0.05) == 0.05

    def test_premium_charge_compounds(self):
        # 5% MBR + 20% premium charge → 1 - 0.95*0.8 = 24% effective take.
        c = market_commission(make_market(mbr=0.05), 0.05, premium_charge_rate=0.20)
        assert c == pytest.approx(0.24)

    def test_higher_mbr_can_kill_a_bet(self):
        # Same price and probability: +EV at 5% commission, below the 4%
        # floor at a 10% AU racing MBR.
        p, odds = 0.36, 3.0
        assert back_expected_value(p, odds, 0.05) > 0.04
        assert back_expected_value(p, odds, 0.10) < 0.04

    def test_relative_spread(self):
        assert relative_spread(3.0, 3.15) == pytest.approx(0.05)
        assert relative_spread(3.0, None) is None
        assert relative_spread(None, 3.0) is None


def make_estimate(p=0.40):
    return ProbabilityEstimate(
        market_id="1.1", selection_id=1, probability=p,
        lower_bound=p - 0.02, upper_bound=p + 0.02,
        confidence=0.85, sample_size=1000, disagreement=0.02,
    )


class TestSpreadGate:
    def _reasons(self, spread):
        return check_rejections(
            make_market(), make_estimate(), odds=3.0, available_size=500,
            cfg=SelectionConfig(), commission=0.05,
            spread_ticks=spread, now=NOW,
        )

    def test_tight_spread_passes(self):
        assert RejectionReason.WIDE_SPREAD not in self._reasons(1)

    def test_wide_spread_rejected(self):
        assert RejectionReason.WIDE_SPREAD in self._reasons(9)

    def test_unquoted_lay_treated_as_wide(self):
        assert RejectionReason.WIDE_SPREAD in self._reasons(None)

    def test_price_stability_derived_from_spread(self):
        cfg = SelectionConfig()
        tight = build_opportunity(make_market(back=3.0, lay=3.05), make_estimate(), cfg, 0.05)
        wide = build_opportunity(make_market(back=3.0, lay=3.4), make_estimate(), cfg, 0.05)
        assert tight is not None and wide is not None
        assert tight.price_stability > wide.price_stability
        assert tight.score > wide.score


class TestBacktestSlippage:
    def test_tick_slippage_degrades_fill(self):
        # One tick down from 3.0 is 2.98 — the fill our backtest assumes.
        assert tick_down(3.0, 1) == 2.98
        assert tick_down(2.0, 2) == 1.98
