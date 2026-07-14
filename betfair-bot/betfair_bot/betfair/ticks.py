"""Betfair price ladder (tick) utilities.

The exchange only accepts prices on its tick ladder; placeOrders rejects
anything else with INVALID_ODDS. The ladder also defines the natural unit for
spread and slippage measurement — "3 ticks" means the same market-impact at
odds 1.5 as at odds 50, while "1%" does not.

Ranges (inclusive lower bound, exclusive upper):
    1.01-2.00 : 0.01      6-10   : 0.2
    2.00-3.00 : 0.02      10-20  : 0.5
    3.00-4.00 : 0.05      20-30  : 1
    4.00-6.00 : 0.10      30-50  : 2
                          50-100 : 5
                          100-1000 : 10
"""

from __future__ import annotations

import bisect

_RANGES = [
    (1.01, 2.0, 0.01),
    (2.0, 3.0, 0.02),
    (3.0, 4.0, 0.05),
    (4.0, 6.0, 0.1),
    (6.0, 10.0, 0.2),
    (10.0, 20.0, 0.5),
    (20.0, 30.0, 1.0),
    (30.0, 50.0, 2.0),
    (50.0, 100.0, 5.0),
    (100.0, 1000.0, 10.0),
]

MIN_PRICE = 1.01
MAX_PRICE = 1000.0


def _build_ladder() -> list[float]:
    ladder = []
    for lo, hi, step in _RANGES:
        p = lo
        while p < hi - 1e-9:
            ladder.append(round(p, 2))
            p += step
    ladder.append(MAX_PRICE)
    return ladder


LADDER = _build_ladder()


def is_valid_price(price: float) -> bool:
    idx = bisect.bisect_left(LADDER, price - 1e-9)
    return idx < len(LADDER) and abs(LADDER[idx] - price) < 1e-9


def nearest_tick(price: float) -> float:
    """Snap to the closest valid price (ties round down = shorter odds)."""
    price = min(max(price, MIN_PRICE), MAX_PRICE)
    idx = bisect.bisect_left(LADDER, price)
    if idx == 0:
        return LADDER[0]
    if idx >= len(LADDER):
        return LADDER[-1]
    below, above = LADDER[idx - 1], LADDER[idx]
    return below if price - below <= above - price else above


def tick_down(price: float, n: int = 1) -> float:
    """n ticks toward shorter odds (worse for a back bet)."""
    idx = bisect.bisect_left(LADDER, nearest_tick(price) - 1e-9)
    return LADDER[max(0, idx - n)]


def tick_up(price: float, n: int = 1) -> float:
    """n ticks toward longer odds (better for a back bet)."""
    idx = bisect.bisect_left(LADDER, nearest_tick(price) - 1e-9)
    return LADDER[min(len(LADDER) - 1, idx + n)]


def ticks_between(low: float, high: float) -> int:
    """Number of ladder steps between two prices (0 if equal/inverted)."""
    if high <= low:
        return 0
    lo_idx = bisect.bisect_left(LADDER, nearest_tick(low) - 1e-9)
    hi_idx = bisect.bisect_left(LADDER, nearest_tick(high) - 1e-9)
    return max(0, hi_idx - lo_idx)


def spread_ticks(back: float | None, lay: float | None) -> int | None:
    """Back/lay spread in ticks; None when either side is unquoted."""
    if not back or not lay:
        return None
    return ticks_between(back, lay)
