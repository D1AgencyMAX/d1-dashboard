"""Market-implied probabilities with overround removal.

The exchange price is treated as a strong prior: 1/odds gives the raw implied
probability, but the book across all runners sums above 1 (the overround), so
implied probabilities are normalised before being used as a model input.
"""

from __future__ import annotations

from ..models import MarketSnapshot


def implied_probability(odds: float) -> float:
    if odds <= 1.0:
        raise ValueError(f"invalid decimal odds: {odds}")
    return 1.0 / odds


def market_implied_probabilities(snapshot: MarketSnapshot) -> dict[int, float]:
    """Overround-normalised implied win probability per active runner.

    Uses the midpoint of best back/lay where both exist (a better estimate of
    fair value than the back price alone), falling back to whichever side is
    quoted. Runners without any quote are skipped.
    """
    raw: dict[int, float] = {}
    for runner in snapshot.active_runners:
        back, lay = runner.back_price, runner.lay_price
        if back and lay:
            mid = (back + lay) / 2.0
        elif back:
            mid = back
        elif lay:
            mid = lay
        elif runner.last_price_traded:
            mid = runner.last_price_traded
        else:
            continue
        if mid > 1.0:
            raw[runner.selection_id] = 1.0 / mid

    total = sum(raw.values())
    if total <= 0:
        return {}
    return {sid: p / total for sid, p in raw.items()}
