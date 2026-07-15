"""
SMRT Algo trading engine.

Wires the incremental `SmrtAlgoState` to a `Broker`. On each CLOSED candle it
updates the signal state in O(1) and, on a fired signal, flips the position
long / flat / short. Fixed-fraction sizing; optional short side.

Two entry points:
  * `on_candle(o,h,l,c)`  — feed one closed bar (embed in your own feed).
  * `run_live(...)`       — turnkey ccxt polling loop.

Keeping the per-bar work O(1) is what makes the live loop "lightning fast":
the hot path is a handful of float ops, not a re-scan of history.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Optional

from .broker import Broker, PaperBroker, Fill
from .smrt_algo import SmrtAlgoParams, SmrtAlgoState, Signal


@dataclass
class EngineConfig:
    symbol: str = "ETH/USDT"
    timeframe: str = "1m"
    risk_fraction: float = 0.10     # fraction of equity per entry
    allow_short: bool = True        # Scalp preset trades both directions
    warmup_bars: int = 200          # bars to seed state before acting live


class TradingEngine:
    def __init__(self, params: SmrtAlgoParams, broker: Broker,
                 config: EngineConfig = EngineConfig(),
                 on_signal: Optional[Callable[[Signal, Optional[Fill]], None]] = None):
        self.params = params
        self.state = SmrtAlgoState(params)
        self.broker = broker
        self.cfg = config
        self.on_signal = on_signal
        self._bars_seen = 0
        self.last_price: float = 0.0

    # ------------------------------------------------------------------ #
    def warmup(self, ohlc_rows) -> None:
        """Prime rolling state on history without trading. rows: (o,h,l,c)."""
        for o, h, l, c in ohlc_rows:
            self.state.update(o, h, l, c)
            self._bars_seen += 1
            self.last_price = c

    def _target_qty(self, price: float) -> float:
        equity = getattr(self.broker, "equity", lambda p: 10_000.0)(price) \
            if isinstance(self.broker, PaperBroker) else 10_000.0
        return max(0.0, (equity * self.cfg.risk_fraction) / price)

    def on_candle(self, o: float, h: float, l: float, c: float) -> Signal:
        sig = self.state.update(o, h, l, c)
        self._bars_seen += 1
        self.last_price = c
        fill: Optional[Fill] = None

        acting = self._bars_seen > self.cfg.warmup_bars
        if acting and sig.action in ("buy", "sell"):
            pos = self.broker.position()
            qty = self._target_qty(c)

            if sig.action == "buy":
                if pos < 0:                       # close short then go long
                    fill = self.broker.market("buy", abs(pos), c)
                if self.broker.position() <= 0:
                    fill = self.broker.market("buy", qty, c)
            else:  # sell
                if pos > 0:                       # close long
                    fill = self.broker.market("sell", abs(pos), c)
                if self.cfg.allow_short and self.broker.position() >= 0:
                    fill = self.broker.market("sell", qty, c)

        if self.on_signal and sig.action:
            self.on_signal(sig, fill)
        return sig

    # ------------------------------------------------------------------ #
    def run_live(self, exchange, poll_seconds: Optional[float] = None) -> None:
        """
        Poll closed candles from a ccxt exchange and drive the engine.
        Only acts on a bar once it has CLOSED (avoids intra-bar repaint).
        """
        tf = self.cfg.timeframe
        tf_ms = exchange.parse_timeframe(tf) * 1000
        poll = poll_seconds if poll_seconds is not None else max(1.0, tf_ms / 1000 / 4)

        # seed
        seed = exchange.fetch_ohlcv(self.cfg.symbol, tf, limit=self.cfg.warmup_bars + 5)
        self.warmup([(r[1], r[2], r[3], r[4]) for r in seed[:-1]])
        last_ts = seed[-2][0]

        while True:
            try:
                rows = exchange.fetch_ohlcv(self.cfg.symbol, tf, limit=3)
                for r in rows:
                    ts = r[0]
                    if ts > last_ts and ts + tf_ms <= exchange.milliseconds():
                        self.on_candle(r[1], r[2], r[3], r[4])
                        last_ts = ts
            except Exception as e:  # network hiccups shouldn't kill the loop
                print(f"[engine] feed error: {e}")
            time.sleep(poll)
