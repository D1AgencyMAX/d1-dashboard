"""All trading costs in one place.

Betfair's real cost stack for a back bet:

1. **Commission** on net market winnings at the market's own Market Base Rate
   (MBR). This varies by market and jurisdiction — Australian racing markets
   commonly carry 6-10% while sports are typically 5% — so the bot reads
   `marketBaseRate` from the market catalogue instead of assuming a flat rate.
   The config commission is only the fallback when the catalogue omits it.
2. **Premium Charge** — for consistently winning accounts Betfair levies an
   additional charge (20%, up to 40-60% for extreme cases) on gross profits
   when standard commission falls below a threshold. A bot that works will
   eventually pay it, so EV can be haircut by `premium_charge_rate` to keep
   long-run economics honest. Default 0 while unproven.
3. **Spread**: the cost of crossing back→lay. We only ever take the back side
   at the quoted price, so spread is not paid directly, but a wide spread
   means the quoted price is fragile and the mid (fair value) is far from our
   execution price — it is gated and scored, not ignored.
4. **Slippage / ticks**: prices exist only on the tick ladder; back-test
   fills are degraded in ladder ticks, not percentages.
5. **Transaction charges**: Betfair charges fees for excessive API
   transaction counts (>1,000 bet transactions/hour) — irrelevant at this
   bot's volume but the executor's one-order-at-a-time design keeps it so.
"""

from __future__ import annotations

from ..models import MarketSnapshot


def market_commission(
    market: MarketSnapshot,
    fallback_rate: float,
    premium_charge_rate: float = 0.0,
) -> float:
    """Effective commission fraction for EV/Kelly on this market.

    Uses the market's own base rate when known. Premium charge applies to
    profits after standard commission, so the combined take on winnings is
    1 - (1 - mbr) * (1 - pc).
    """
    mbr = market.market_base_rate if market.market_base_rate is not None else fallback_rate
    if premium_charge_rate > 0:
        return 1.0 - (1.0 - mbr) * (1.0 - premium_charge_rate)
    return mbr


def relative_spread(back: float | None, lay: float | None) -> float | None:
    """(lay - back) / back; None when either side is unquoted."""
    if not back or not lay or back <= 1.0:
        return None
    return max(0.0, (lay - back) / back)
