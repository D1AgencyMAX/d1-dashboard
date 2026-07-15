"""
Broker abstraction for the SMRT Algo engine.

  * `Broker`      — protocol the engine talks to.
  * `PaperBroker` — in-memory fill simulator (fast, zero deps). Default.
  * `CcxtBroker`  — thin adapter over any ccxt exchange for live orders.
                    ccxt is imported lazily so the engine has no hard dep on it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol


@dataclass
class Fill:
    side: str          # "buy" | "sell"
    qty: float
    price: float


class Broker(Protocol):
    def market(self, side: str, qty: float, price: float) -> Fill: ...
    def position(self) -> float: ...     # signed base qty (+long / -short)


class PaperBroker:
    """Deterministic paper broker. `price` is the reference fill price."""

    def __init__(self, cash: float = 10_000.0, fee: float = 0.0004, slippage: float = 0.0):
        self.cash = cash
        self.fee = fee
        self.slippage = slippage
        self.qty = 0.0
        self.avg_price = 0.0
        self.realized = 0.0
        self.fills: list[Fill] = []

    def position(self) -> float:
        return self.qty

    def market(self, side: str, qty: float, price: float) -> Fill:
        slip = 1 + (self.slippage if side == "buy" else -self.slippage)
        fill_price = price * slip
        signed = qty if side == "buy" else -qty

        # realize PnL when reducing/flipping
        if self.qty != 0 and (self.qty > 0) != (signed > 0):
            closing = min(abs(signed), abs(self.qty))
            pnl = closing * (fill_price - self.avg_price) * (1 if self.qty > 0 else -1)
            self.realized += pnl

        new_qty = self.qty + signed
        if (self.qty >= 0 and signed > 0) or (self.qty <= 0 and signed < 0):
            # increasing exposure -> blend avg price
            tot = abs(self.qty) + abs(signed)
            self.avg_price = (self.avg_price * abs(self.qty) + fill_price * abs(signed)) / tot if tot else fill_price
        elif new_qty != 0 and (new_qty > 0) != (self.qty > 0):
            self.avg_price = fill_price   # flipped
        self.qty = new_qty
        self.cash -= fill_price * abs(signed) * self.fee

        fill = Fill(side, qty, fill_price)
        self.fills.append(fill)
        return fill

    def equity(self, mark: float) -> float:
        unreal = self.qty * (mark - self.avg_price)
        return self.cash + self.realized + unreal


class CcxtBroker:
    """
    Live broker over a ccxt exchange. Example:

        import ccxt
        ex = ccxt.binanceusdm({"apiKey": ..., "secret": ...})
        broker = CcxtBroker(ex, "ETH/USDT:USDT")
    """

    def __init__(self, exchange, symbol: str):
        self.ex = exchange
        self.symbol = symbol

    def position(self) -> float:
        try:
            for p in self.ex.fetch_positions([self.symbol]):
                if p.get("symbol") == self.symbol:
                    amt = float(p.get("contracts") or p.get("contractSize") or 0)
                    side = p.get("side")
                    return amt if side == "long" else -amt
        except Exception:
            pass
        return 0.0

    def market(self, side: str, qty: float, price: float) -> Fill:
        order = self.ex.create_order(self.symbol, "market", side, qty)
        filled_price = float(order.get("average") or order.get("price") or price)
        return Fill(side, qty, filled_price)
