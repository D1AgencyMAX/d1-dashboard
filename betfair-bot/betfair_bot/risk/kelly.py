"""Fractional Kelly stake sizing with hard caps.

f* = (b*p - q) / b,  where b = net decimal odds after commission,
p = model probability, q = 1 - p. Production uses a small fraction of f*
(default one-tenth Kelly) and multiple absolute caps on top.
"""

from __future__ import annotations


def kelly_fraction(model_p: float, odds: float, commission: float) -> float:
    """Full-Kelly optimal fraction of bankroll for a back bet; 0 if no edge."""
    if odds <= 1.0:
        raise ValueError(f"invalid decimal odds: {odds}")
    if not 0.0 <= model_p <= 1.0:
        raise ValueError(f"invalid probability: {model_p}")
    b = (odds - 1.0) * (1.0 - commission)
    if b <= 0:
        return 0.0
    q = 1.0 - model_p
    f = (b * model_p - q) / b
    return max(0.0, f)


def stake(
    model_p: float,
    odds: float,
    commission: float,
    bankroll: float,
    *,
    fraction: float = 0.10,
    max_stake_pct: float = 0.005,
    min_stake: float = 5.0,
) -> float:
    """Fractional-Kelly stake, capped at max_stake_pct of bankroll.

    Returns 0.0 when there is no edge or the capped stake would fall below the
    exchange minimum (a sub-minimum stake means the edge is too small to
    express — do not round it up).
    """
    f = kelly_fraction(model_p, odds, commission) * fraction
    amount = min(f * bankroll, max_stake_pct * bankroll)
    if amount < min_stake:
        return 0.0
    return round(amount, 2)
