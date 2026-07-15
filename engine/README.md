# Pro V4 [SMRT Algo] — Python Engine

Python port of `indicators/smrtalgo-pro-v4.pine`, built to **bolt onto a trading
engine**. Signal defaults mirror the settings screenshot (Advance classifier,
Scalp, sensitivity 1.5, calibration 150, all Enhance Systems off).

## Files
| File | Purpose |
| --- | --- |
| `smrt_algo.py` | Signal core. `compute()` (vectorized backtest) + `SmrtAlgoState` (O(1) live). |
| `broker.py` | `Broker` protocol, `PaperBroker` (sim), `CcxtBroker` (live via ccxt). |
| `trading_engine.py` | `TradingEngine` — position/order management + `run_live()` ccxt loop. |
| `example.py` | Synthetic end-to-end demo. |
| `requirements.txt` | `numpy` (core); `ccxt` optional for live. |

## Why it's fast
- **Live path is O(1) per candle** — EMA/ATR are incremental recurrences and the
  enhance modules use bounded ring buffers, so latency never grows with history.
- **Backtest path is vectorized NumPy** — one pass, no per-bar Python loop.
- The two paths are verified to produce **identical signals** (`python -m engine.smrt_algo`).

## Bolt-on: signal only
```python
from engine import SmrtAlgoParams, SmrtAlgoState

algo = SmrtAlgoState(SmrtAlgoParams())         # screenshot defaults
sig  = algo.update(o, h, l, c)                 # call once per CLOSED candle
if sig.action == "buy":  ...                   # "buy" | "sell" | None
```

## Bolt-on: full engine (manages positions)
```python
from engine import SmrtAlgoParams, TradingEngine, EngineConfig, PaperBroker

eng = TradingEngine(SmrtAlgoParams(), PaperBroker(),
                    EngineConfig(symbol="ETH/USDT", timeframe="1m"))
eng.on_candle(o, h, l, c)                       # feed closed bars from your feed
```

## Live via ccxt
```python
import ccxt
from engine import SmrtAlgoParams, TradingEngine, EngineConfig, CcxtBroker

ex = ccxt.binanceusdm({"apiKey": "...", "secret": "..."})
sym = "ETH/USDT:USDT"
eng = TradingEngine(SmrtAlgoParams(), CcxtBroker(ex, sym),
                    EngineConfig(symbol=sym, timeframe="1m"))
eng.run_live(ex)                                # polls closed candles, trades on signals
```

## Run
```bash
pip install -r engine/requirements.txt
python -m engine.smrt_algo     # self-check: live == backtest
python -m engine.example       # demo run
```

> Signals fire on **closed** candles only (no intra-bar repaint). Tune sizing/short
> side via `EngineConfig`. Not financial advice — validate on paper before live.
