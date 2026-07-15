# TradingView Indicators

Pine Script re-creations of chart indicators, one file per build.

## Pro V4 [SMRT Algo] — `smrtalgo-pro-v4.pine`

Reproduces the input panel from the settings screenshot (ETHUSDT.P preset).

### Basic Settings
| Setting | Value |
| --- | --- |
| Show Signals | ✅ on |
| AI Classifier Type | Advance |
| Signal Sensitivity | 1.5 |
| Signal Calibration | 150 |
| Trading Type | Scalp |
| Label Offset | ✅ on · 1 |
| Candle Coloring | Gradient |
| Colors | cyan `#00E5FF` · pink `#FF1E56` · purple `#8000FF` |

### Enhance Systems (all off by default)
| Module | Default |
| --- | --- |
| Fibonacci Number (Price Noise) | 30 |
| Linear Regression (Price Mean) | 2 |
| Trend Ranges (Price Range) | 100 |
| True Range (Price Volatility) | 3.5 |
| Liquidity Ratio (Price Sweep) | 35 |
| Dynamic Flow (Price Flow) | 4 |
| Moving Average (Price Average) | 0.5 |

### How to load
1. Open TradingView → **Pine Editor**.
2. Paste the contents of `smrtalgo-pro-v4.pine`.
3. **Save** → **Add to chart**.
4. Open the indicator's settings (gear icon) to see the same input layout as the screenshot.

Each Enhance System is a toggle + value pair; while any are enabled they act as a
confirmation gate on the classifier's buy/sell crosses.
