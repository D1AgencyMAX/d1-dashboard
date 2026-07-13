import pytest

from betfair_bot.risk.kelly import kelly_fraction, stake


def test_no_edge_no_stake():
    # Fair odds with commission → negative edge → zero.
    assert kelly_fraction(0.5, 2.0, 0.05) == 0.0
    assert stake(0.5, 2.0, 0.05, 10_000) == 0.0


def test_kelly_formula():
    # b = (3-1)*(1-0) = 2, p = 0.4, q = 0.6 → f* = (0.8-0.6)/2 = 0.1
    assert kelly_fraction(0.4, 3.0, 0.0) == pytest.approx(0.10)


def test_fractional_kelly_and_cap():
    bankroll = 10_000.0
    # Strong edge: full Kelly would be large; cap at 0.5% of bankroll = 50.
    s = stake(0.5, 3.0, 0.05, bankroll, fraction=0.10, max_stake_pct=0.005)
    assert s <= 50.0
    assert s > 0


def test_min_stake_not_rounded_up():
    # A tiny edge produces a sub-minimum stake → refuse rather than round up.
    s = stake(0.505, 2.0, 0.0, 1000.0, fraction=0.10, max_stake_pct=0.005, min_stake=5.0)
    assert s == 0.0


def test_commission_reduces_kelly():
    assert kelly_fraction(0.4, 3.0, 0.05) < kelly_fraction(0.4, 3.0, 0.0)
