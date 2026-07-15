"""
Pro V4 [SMRT Algo] — Python trading engine.

Bolt-on points (import these):

    from engine import SmrtAlgoParams, SmrtAlgoState, compute
    from engine import TradingEngine, EngineConfig, PaperBroker, CcxtBroker

Typical wiring into an existing engine:

    params = SmrtAlgoParams()                 # matches the settings screenshot
    algo   = SmrtAlgoState(params)            # O(1) per closed candle
    sig    = algo.update(o, h, l, c)          # -> Signal(action="buy"/"sell"/None, ...)

Or let the built-in engine manage positions/orders:

    eng = TradingEngine(params, PaperBroker(), EngineConfig(symbol="ETH/USDT"))
    eng.on_candle(o, h, l, c)                 # feed one closed bar
"""
from .smrt_algo import SmrtAlgoParams, SmrtAlgoState, Signal, compute
from .broker import Broker, PaperBroker, CcxtBroker, Fill
from .trading_engine import TradingEngine, EngineConfig

__all__ = [
    "SmrtAlgoParams", "SmrtAlgoState", "Signal", "compute",
    "Broker", "PaperBroker", "CcxtBroker", "Fill",
    "TradingEngine", "EngineConfig",
]
