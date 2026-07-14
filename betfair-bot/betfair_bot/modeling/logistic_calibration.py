"""Logistic blend calibrator: the fitted successor to ShrinkageCalibrator.

Learns  p_fair = sigmoid( a·logit(p_model) + b·logit(p_market) + c )
from graded history. This simultaneously:

- calibrates the model (a < 1 shrinks overconfidence, a > 1 sharpens),
- learns how much the market already knows (b),
- corrects systematic bias, e.g. longshot bias (c).

Drop-in replacement for ShrinkageCalibrator: same `calibrate(model_p,
market_p)` interface, so the pipeline switches by construction argument only.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


def _logit(p: float) -> float:
    p = min(max(p, 1e-6), 1.0 - 1e-6)
    return math.log(p / (1.0 - p))


def _sigmoid(x: float) -> float:
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


@dataclass
class LogisticCalibrator:
    a: float = 1.0   # weight on model logit
    b: float = 0.0   # weight on market logit
    c: float = 0.0   # intercept (bias correction)
    n_fitted: int = 0

    def calibrate(self, model_p: float, market_p: float | None) -> float:
        x = self.a * _logit(model_p)
        if market_p is not None:
            x += self.b * _logit(market_p)
        return _sigmoid(x + self.c)

    @classmethod
    def fit(
        cls,
        model_probs: list[float],
        market_probs: list[float | None],
        outcomes: list[int],
        iterations: int = 4000,
        learning_rate: float = 0.5,
        l2: float = 1e-4,
    ) -> "LogisticCalibrator":
        """Fit by gradient descent on log loss (logistic regression on logits).

        Gradients are exact: d(loss)/d(param) = (p - y) * feature.
        """
        if not model_probs or len(model_probs) != len(outcomes):
            raise ValueError("model_probs and outcomes must be same non-zero length")
        n = len(model_probs)
        feats = [
            (
                _logit(mp),
                _logit(kp) if kp is not None else 0.0,
                1.0 if kp is not None else 0.0,  # market presence mask for b
            )
            for mp, kp in zip(model_probs, market_probs)
        ]
        a, b, c = 1.0, 0.0, 0.0
        for _ in range(iterations):
            ga = gb = gc = 0.0
            for (fm, fk, mask), y in zip(feats, outcomes):
                p = _sigmoid(a * fm + b * fk * mask + c)
                err = p - y
                ga += err * fm
                gb += err * fk * mask
                gc += err
            a -= learning_rate * (ga / n + l2 * (a - 1.0))
            b -= learning_rate * (gb / n + l2 * b)
            c -= learning_rate * (gc / n + l2 * c)
        return cls(a=a, b=b, c=c, n_fitted=n)

    def log_loss(
        self,
        model_probs: list[float],
        market_probs: list[float | None],
        outcomes: list[int],
    ) -> float:
        total = 0.0
        for mp, kp, y in zip(model_probs, market_probs, outcomes):
            p = min(max(self.calibrate(mp, kp), 1e-12), 1 - 1e-12)
            total += -(y * math.log(p) + (1 - y) * math.log(1 - p))
        return total / max(len(outcomes), 1)
