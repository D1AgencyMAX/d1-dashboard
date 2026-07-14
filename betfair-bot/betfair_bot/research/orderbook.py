"""Betfair order-book behaviour as an ensemble component.

Reads edge-relevant microstructure out of the exchange itself:

- **Book pressure**: imbalance between money waiting to back and money
  waiting to lay a runner. Sustained lay-side depth at current prices means
  informed money thinks the true probability is higher than implied.
- **Price momentum (steam)**: direction and size of recent implied-probability
  drift from the recorded snapshot history.
- **Late volume**: how much of total matched arrived recently — late, fast
  money is more informative than stale volume.

The output is deliberately a small tilt on the market-implied probability,
never an independent opinion: the order book refines the market prior, it
cannot manufacture an edge on its own. Shortening odds never automatically
create a bet — the tilted probability still has to clear the EV filter at the
*new* price, which is exactly the "the move may have removed the edge" rule.
"""

from __future__ import annotations

from datetime import datetime

from ..models import ComponentEstimate, MarketSnapshot, RunnerBook
from ..modeling.market_prior import market_implied_probabilities

# Cap the total order-book tilt at ±6% relative.
MAX_TILT = 0.06


def book_pressure(runner: RunnerBook, levels: int = 3) -> float:
    """Back/lay depth imbalance in [-1, 1].

    Positive = more money waiting to lay (offering our back side) than to
    back. Heavy available-to-back depth (money wanting to lay off) reads as
    negative pressure on the runner's chance; heavy available-to-lay depth
    reads as support.
    """
    back_depth = sum(ps.size for ps in runner.best_back[:levels])
    lay_depth = sum(ps.size for ps in runner.best_lay[:levels])
    total = back_depth + lay_depth
    if total <= 0:
        return 0.0
    return (back_depth - lay_depth) / total


def price_momentum(history: list[tuple[datetime, float]], window: int = 12) -> float:
    """Relative implied-probability drift over the recent window, in [-1, 1].

    history: chronological (time, implied_probability) samples for a runner.
    Positive = firming (probability rising / odds shortening).
    """
    if len(history) < 2:
        return 0.0
    recent = history[-window:]
    start, end = recent[0][1], recent[-1][1]
    if start <= 0:
        return 0.0
    return max(-1.0, min(1.0, (end - start) / start))


def order_book_component(
    market: MarketSnapshot,
    runner: RunnerBook,
    history: list[tuple[datetime, float]] | None = None,
) -> ComponentEstimate | None:
    """Build the 'betfair_order_book' component for one runner.

    Tilt = 60% pressure + 40% momentum, scaled to at most ±MAX_TILT relative,
    applied to the overround-normalised market probability. Confidence scales
    with visible depth so an empty book contributes almost nothing.
    """
    market_probs = market_implied_probabilities(market)
    base = market_probs.get(runner.selection_id)
    if base is None:
        return None

    pressure = book_pressure(runner)
    momentum = price_momentum(history or [])
    tilt = MAX_TILT * (0.6 * pressure + 0.4 * momentum)
    probability = min(0.99, max(0.01, base * (1.0 + tilt)))

    depth = sum(ps.size for ps in runner.best_back[:3]) + sum(
        ps.size for ps in runner.best_lay[:3]
    )
    # ~0.2 confidence for a thin book, saturating ~0.9 around 20k visible.
    confidence = min(0.9, 0.2 + depth / 25_000.0)
    samples = max(2, len(history or []))

    return ComponentEstimate(
        component="betfair_order_book",
        probability=probability,
        confidence=confidence,
        sample_size=min(samples * 10, 500),
    )
