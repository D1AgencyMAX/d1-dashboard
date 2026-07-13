"""Expected-value and break-even mathematics for exchange back bets.

For a back bet at decimal odds O with commission rate c on net winnings:

    EV = P_model * (O - 1) * (1 - c) - (1 - P_model)

The break-even probability is where EV = 0:

    P_breakeven = 1 / ((O - 1) * (1 - c) + 1)

A bet qualifies only when the *lower confidence bound* of the model
probability clears break-even plus a safety margin — the point estimate alone
is never sufficient.
"""

from __future__ import annotations


def back_expected_value(model_p: float, odds: float, commission: float) -> float:
    """Commission-adjusted EV per unit stake for a back bet."""
    if odds <= 1.0:
        raise ValueError(f"invalid decimal odds: {odds}")
    if not 0.0 <= model_p <= 1.0:
        raise ValueError(f"invalid probability: {model_p}")
    return model_p * (odds - 1.0) * (1.0 - commission) - (1.0 - model_p)


def break_even_probability(odds: float, commission: float) -> float:
    """Model probability at which a back bet has zero EV after commission."""
    if odds <= 1.0:
        raise ValueError(f"invalid decimal odds: {odds}")
    return 1.0 / ((odds - 1.0) * (1.0 - commission) + 1.0)


def minimum_acceptable_odds(model_p: float, commission: float, min_ev: float) -> float:
    """Lowest decimal odds at which the bet still clears the EV floor.

    Solves EV(O) = min_ev for O. Used as the execution-time price floor: if
    the market drifts below this, the opportunity no longer qualifies.
    """
    if not 0.0 < model_p < 1.0:
        raise ValueError(f"invalid probability: {model_p}")
    return 1.0 + (min_ev + 1.0 - model_p) / (model_p * (1.0 - commission))


def passes_conservative_test(
    lower_bound_p: float,
    odds: float,
    commission: float,
    safety_margin: float,
) -> bool:
    """P_lower_bound > P_breakeven + safety_margin — the acceptance test."""
    return lower_bound_p > break_even_probability(odds, commission) + safety_margin
