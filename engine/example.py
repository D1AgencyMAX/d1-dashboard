"""
Minimal end-to-end example: synthetic candles -> SMRT Algo -> paper broker.

Run:  python -m engine.example
"""
import numpy as np

from engine import SmrtAlgoParams, TradingEngine, EngineConfig, PaperBroker, Signal


def main() -> None:
    rng = np.random.default_rng(42)
    n = 2000
    close = 1800 + rng.standard_normal(n).cumsum()
    open_ = np.concatenate(([close[0]], close[:-1]))
    high = np.maximum(open_, close) + rng.random(n)
    low = np.minimum(open_, close) - rng.random(n)

    def log(sig: Signal, fill):
        tag = "FILL" if fill else "signal"
        px = f"@ {fill.price:.2f}" if fill else ""
        print(f"[{tag}] bar {sig.index:>4}  {sig.action.upper():4}  price {sig.price:8.2f} {px}")

    broker = PaperBroker(cash=10_000)
    engine = TradingEngine(
        SmrtAlgoParams(),                       # screenshot defaults
        broker,
        EngineConfig(symbol="ETH/USDT", timeframe="1m", warmup_bars=50),
        on_signal=log,
    )

    for i in range(n):
        engine.on_candle(open_[i], high[i], low[i], close[i])

    print("-" * 52)
    print(f"final position : {broker.position():.4f}")
    print(f"realized pnl   : {broker.realized:8.2f}")
    print(f"equity (mark)  : {broker.equity(close[-1]):8.2f}")
    print(f"fills          : {len(broker.fills)}")


if __name__ == "__main__":
    main()
