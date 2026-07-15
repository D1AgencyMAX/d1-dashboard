"""
Pro V4 [SMRT Algo] — signal engine (Python).

A 1:1 port of indicators/smrtalgo-pro-v4.pine. Two execution paths:

  * `compute()`          — fully vectorized NumPy pass over an OHLC history.
                           Use for backtests / warmup. O(n), no Python per-bar loop.
  * `SmrtAlgoState`      — incremental, O(1)-per-bar updater for LIVE trading.
                           Feed it one closed candle at a time; it keeps only the
                           rolling state it needs, so latency does not grow with
                           history length.

Both paths share the same defaults, which mirror the settings screenshot
(ETHUSDT.P — Advance classifier, Scalp, sensitivity 1.5, calibration 150).
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


# --------------------------------------------------------------------------- #
# Parameters — every control from the SMRT Algo input panel.
# --------------------------------------------------------------------------- #
@dataclass
class SmrtAlgoParams:
    # --- Basic Settings ---
    show_signals: bool = True
    ai_classifier: str = "Advance"       # Basic | Advance | Pro
    signal_sensitivity: float = 1.5
    signal_calibration: int = 150
    trading_type: str = "Scalp"          # Scalp | Intraday | Swing
    label_offset: int = 1                # kept for parity; not used server-side

    # --- Enhance Systems (toggle + value); all OFF by default ---
    use_fib: bool = False
    fib_len: int = 30
    use_linreg: bool = False
    linreg_len: int = 2
    use_trend: bool = False
    trend_len: int = 100
    use_tr: bool = False
    tr_mult: float = 3.5
    use_liq: bool = False
    liq_len: int = 35
    use_flow: bool = False
    flow_len: int = 4
    use_ma: bool = False
    ma_factor: float = 0.5

    # ---- derived ----
    @property
    def base_len(self) -> int:
        return {"Scalp": 5, "Intraday": 14, "Swing": 34}.get(self.trading_type, 14)

    @property
    def tier_smooth(self) -> int:
        return {"Basic": 1, "Advance": 2, "Pro": 3}.get(self.ai_classifier, 2)

    @property
    def eff_len(self) -> int:
        return max(1, int(self.base_len + self.signal_calibration / 50.0))

    @property
    def any_enhance(self) -> bool:
        return any([self.use_fib, self.use_linreg, self.use_trend, self.use_tr,
                    self.use_liq, self.use_flow, self.use_ma])


@dataclass
class Signal:
    index: int
    action: Optional[str]      # "buy" | "sell" | None
    price: float
    signal_line: float
    upper: float
    lower: float
    score: float


# --------------------------------------------------------------------------- #
# Small numeric helpers (match Pine's ta.* seeding: first value seeds the series)
# --------------------------------------------------------------------------- #
def _ema(x: np.ndarray, length: int) -> np.ndarray:
    """EMA with alpha = 2/(len+1), seeded on the first sample (Pine ta.ema)."""
    alpha = 2.0 / (length + 1.0)
    out = np.empty_like(x, dtype=np.float64)
    acc = x[0]
    for i in range(x.shape[0]):
        acc = x[i] if i == 0 else acc + alpha * (x[i] - acc)
        out[i] = acc
    return out


def _rma(x: np.ndarray, length: int) -> np.ndarray:
    """Wilder's RMA, alpha = 1/len (Pine ta.rma / basis of ta.atr)."""
    alpha = 1.0 / length
    out = np.empty_like(x, dtype=np.float64)
    acc = x[0]
    for i in range(x.shape[0]):
        acc = x[i] if i == 0 else acc + alpha * (x[i] - acc)
        out[i] = acc
    return out


def _true_range(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
    prev_close = np.concatenate(([close[0]], close[:-1]))
    return np.maximum.reduce([
        high - low,
        np.abs(high - prev_close),
        np.abs(low - prev_close),
    ])


# --------------------------------------------------------------------------- #
# Vectorized pass — backtest / warmup
# --------------------------------------------------------------------------- #
def compute(open_, high, low, close, params: SmrtAlgoParams) -> list[Signal]:
    """Vectorized signal computation over a full OHLC history."""
    o = np.asarray(open_, dtype=np.float64)
    h = np.asarray(high, dtype=np.float64)
    l = np.asarray(low, dtype=np.float64)
    c = np.asarray(close, dtype=np.float64)
    n = c.shape[0]

    eff = params.eff_len
    atr = _rma(_true_range(h, l, c), eff)
    band = atr * params.signal_sensitivity
    basis = _ema(c, eff)
    signal_line = _ema(basis, params.tier_smooth)

    # ---- composite score from enabled Enhance Systems (vectorized) ----
    score = np.zeros(n)
    if params.use_fib:
        noise = _rolling_std(c, params.fib_len)
        score += np.where(c > basis + noise, 1, np.where(c < basis - noise, -1, 0))
    if params.use_linreg:
        lr = _rolling_linreg(c, max(2, params.linreg_len))
        score += np.where(c > lr, 1, -1)
    if params.use_trend:
        mid = (_rolling_max(h, params.trend_len) + _rolling_min(l, params.trend_len)) / 2
        score += np.where(c > mid, 1, -1)
    if params.use_tr:
        vol = atr * params.tr_mult
        score += np.where(c > signal_line + vol, 1, np.where(c < signal_line - vol, -1, 0))
    if params.use_liq:
        score += np.where(h >= _rolling_max(h, params.liq_len), -1,
                          np.where(l <= _rolling_min(l, params.liq_len), 1, 0))
    if params.use_flow:
        flow = _ema(c - o, params.flow_len)
        score += np.where(flow > 0, 1, -1)
    if params.use_ma:
        ma = _rolling_mean(c, max(1, int(eff * params.ma_factor)))
        score += np.where(c > ma, 1, -1)

    upper = signal_line + band
    lower = signal_line - band

    # crossover(close, upper) / crossunder(close, lower)
    prev_c = np.concatenate(([c[0]], c[:-1]))
    prev_u = np.concatenate(([upper[0]], upper[:-1]))
    prev_l = np.concatenate(([lower[0]], lower[:-1]))
    cross_up = (prev_c <= prev_u) & (c > upper)
    cross_dn = (prev_c >= prev_l) & (c < lower)

    long_ok = (~params.any_enhance) | (score > 0)
    short_ok = (~params.any_enhance) | (score < 0)
    buy = cross_up & long_ok
    sell = cross_dn & short_ok

    signals: list[Signal] = []
    for i in range(n):
        act = "buy" if buy[i] else "sell" if sell[i] else None
        signals.append(Signal(i, act, float(c[i]), float(signal_line[i]),
                              float(upper[i]), float(lower[i]), float(score[i])))
    return signals


# ---- rolling helpers for the vectorized enhance modules ----
def _rolling_apply(x, w, fn):
    n = len(x)
    out = np.empty(n)
    for i in range(n):
        s = max(0, i - w + 1)
        out[i] = fn(x[s:i + 1])
    return out


def _rolling_std(x, w):  return _rolling_apply(x, w, lambda a: a.std(ddof=1) if len(a) > 1 else 0.0)
def _rolling_mean(x, w): return _rolling_apply(x, w, np.mean)
def _rolling_max(x, w):  return _rolling_apply(x, w, np.max)
def _rolling_min(x, w):  return _rolling_apply(x, w, np.min)


def _rolling_linreg(x, w):
    n = len(x)
    out = np.empty(n)
    for i in range(n):
        s = max(0, i - w + 1)
        seg = x[s:i + 1]
        m = len(seg)
        if m == 1:
            out[i] = seg[-1]
            continue
        t = np.arange(m)
        b, a = np.polyfit(t, seg, 1)
        out[i] = a + b * (m - 1)   # value at the current (last) bar
    return out


# --------------------------------------------------------------------------- #
# Incremental state — LIVE trading, O(1) per closed candle
# --------------------------------------------------------------------------- #
class _IncEMA:
    __slots__ = ("alpha", "val")

    def __init__(self, length: int):
        self.alpha = 2.0 / (length + 1.0)
        self.val: Optional[float] = None

    def update(self, x: float) -> float:
        self.val = x if self.val is None else self.val + self.alpha * (x - self.val)
        return self.val


class _IncRMA(_IncEMA):
    def __init__(self, length: int):
        super().__init__(length)
        self.alpha = 1.0 / length


class SmrtAlgoState:
    """
    Streaming SMRT Algo. Call `update(o, h, l, c)` once per CLOSED candle.

    Only bounded rolling buffers are kept, so a single update is O(window),
    independent of how long the engine has been running — ideal for a hot
    live loop.
    """

    def __init__(self, params: SmrtAlgoParams):
        self.p = params
        eff = params.eff_len
        self._basis = _IncEMA(eff)
        self._signal = _IncEMA(params.tier_smooth)
        self._atr = _IncRMA(eff)
        self._flow = _IncEMA(params.flow_len)

        self._prev_close: Optional[float] = None      # for true range
        self._prev_c: Optional[float] = None          # for crossover
        self._prev_upper: Optional[float] = None
        self._prev_lower: Optional[float] = None
        self._i = -1

        # bounded history for enhance modules that need a window
        self._c_hist: deque = deque(maxlen=max(params.fib_len, params.linreg_len,
                                                int(eff * params.ma_factor) + 1, 2))
        self._h_hist: deque = deque(maxlen=max(params.trend_len, params.liq_len, 1))
        self._l_hist: deque = deque(maxlen=max(params.trend_len, params.liq_len, 1))

    def update(self, o: float, h: float, l: float, c: float) -> Signal:
        self._i += 1
        p = self.p

        # true range -> ATR -> band
        pc = self._prev_close if self._prev_close is not None else c
        tr = max(h - l, abs(h - pc), abs(l - pc))
        atr = self._atr.update(tr)
        band = atr * p.signal_sensitivity

        basis = self._basis.update(c)
        signal_line = self._signal.update(basis)
        upper = signal_line + band
        lower = signal_line - band

        self._c_hist.append(c)
        self._h_hist.append(h)
        self._l_hist.append(l)

        # ---- composite score ----
        score = 0.0
        if p.use_fib:
            arr = np.fromiter(list(self._c_hist)[-p.fib_len:], dtype=np.float64)
            noise = arr.std(ddof=1) if arr.size > 1 else 0.0
            score += 1 if c > basis + noise else -1 if c < basis - noise else 0
        if p.use_linreg:
            seg = np.fromiter(list(self._c_hist)[-max(2, p.linreg_len):], dtype=np.float64)
            if seg.size > 1:
                t = np.arange(seg.size)
                b, a = np.polyfit(t, seg, 1)
                lr = a + b * (seg.size - 1)
            else:
                lr = c
            score += 1 if c > lr else -1
        if p.use_trend and len(self._h_hist) > 0:
            hh = max(list(self._h_hist)[-p.trend_len:])
            ll = min(list(self._l_hist)[-p.trend_len:])
            score += 1 if c > (hh + ll) / 2 else -1
        if p.use_tr:
            vol = atr * p.tr_mult
            score += 1 if c > signal_line + vol else -1 if c < signal_line - vol else 0
        if p.use_liq and len(self._h_hist) > 0:
            if h >= max(list(self._h_hist)[-p.liq_len:]):
                score -= 1
            elif l <= min(list(self._l_hist)[-p.liq_len:]):
                score += 1
        if p.use_flow:
            flow = self._flow.update(c - o)
            score += 1 if flow > 0 else -1
        if p.use_ma:
            w = max(1, int(p.eff_len * p.ma_factor))
            seg = list(self._c_hist)[-w:]
            ma = sum(seg) / len(seg)
            score += 1 if c > ma else -1

        # ---- cross detection ----
        action = None
        if self._prev_c is not None:
            cross_up = self._prev_c <= self._prev_upper and c > upper
            cross_dn = self._prev_c >= self._prev_lower and c < lower
            long_ok = (not p.any_enhance) or score > 0
            short_ok = (not p.any_enhance) or score < 0
            if cross_up and long_ok:
                action = "buy"
            elif cross_dn and short_ok:
                action = "sell"

        # advance state
        self._prev_close = c
        self._prev_c = c
        self._prev_upper = upper
        self._prev_lower = lower

        return Signal(self._i, action, c, signal_line, upper, lower, score)


# --------------------------------------------------------------------------- #
# Self-check: vectorized and incremental paths must agree.
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    rng = np.random.default_rng(7)
    n = 3000
    steps = rng.standard_normal(n).cumsum()
    close = 1800 + steps
    open_ = np.concatenate(([close[0]], close[:-1]))
    high = np.maximum(open_, close) + rng.random(n)
    low = np.minimum(open_, close) - rng.random(n)

    params = SmrtAlgoParams()
    vec = compute(open_, high, low, close, params)

    st = SmrtAlgoState(params)
    inc = [st.update(open_[i], high[i], low[i], close[i]) for i in range(n)]

    mismatches = sum(1 for a, b in zip(vec, inc) if a.action != b.action)
    buys = sum(1 for s in vec if s.action == "buy")
    sells = sum(1 for s in vec if s.action == "sell")
    print(f"bars={n}  buys={buys}  sells={sells}  vec/inc action mismatches={mismatches}")
    assert mismatches == 0, "incremental path diverged from vectorized path"
    print("OK: incremental live path matches vectorized backtest path.")
