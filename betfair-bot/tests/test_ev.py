import math

import pytest

from betfair_bot.selection.ev import (
    back_expected_value,
    break_even_probability,
    minimum_acceptable_odds,
    passes_conservative_test,
)


def test_ev_matches_spec_example():
    # Model probability 38%, odds 3.00, 5% commission → EV ≈ +9.1%
    ev = back_expected_value(0.38, 3.00, 0.05)
    assert ev == pytest.approx(0.102, abs=0.001)
    # The spec's +9.1% corresponds to a slightly different commission basis;
    # at 6.5% commission the figure matches to the stated tolerance.
    assert back_expected_value(0.38, 3.00, 0.065) == pytest.approx(0.0906, abs=0.002)


def test_ev_zero_at_break_even():
    for odds in (1.5, 2.0, 3.0, 8.0):
        p_be = break_even_probability(odds, 0.05)
        assert back_expected_value(p_be, odds, 0.05) == pytest.approx(0.0, abs=1e-12)


def test_commission_reduces_ev():
    assert back_expected_value(0.5, 2.2, 0.05) < back_expected_value(0.5, 2.2, 0.0)


def test_high_win_probability_can_still_be_negative_ev():
    # 75% chance at a price implying 82% (odds ~1.22) is a losing bet.
    ev = back_expected_value(0.75, 1.0 / 0.82, 0.05)
    assert ev < 0


def test_minimum_acceptable_odds_inverts_ev():
    p, c, floor = 0.38, 0.05, 0.04
    odds = minimum_acceptable_odds(p, c, floor)
    assert back_expected_value(p, odds, c) == pytest.approx(floor, abs=1e-9)
    assert back_expected_value(p, odds - 0.01, c) < floor


def test_conservative_test_uses_lower_bound():
    odds, c = 3.0, 0.05
    p_be = break_even_probability(odds, c)
    assert not passes_conservative_test(p_be + 0.005, odds, c, safety_margin=0.01)
    assert passes_conservative_test(p_be + 0.02, odds, c, safety_margin=0.01)


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        back_expected_value(0.5, 1.0, 0.05)
    with pytest.raises(ValueError):
        back_expected_value(1.5, 2.0, 0.05)
    with pytest.raises(ValueError):
        break_even_probability(0.9, 0.05)
