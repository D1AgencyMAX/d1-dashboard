"""Probability calibration and scoring metrics.

Tracks how well predicted probabilities match observed frequencies (Brier
score, log loss, reliability bins) and provides a simple shrinkage calibrator
that pulls extreme predictions toward the market until enough live evidence
accumulates.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


def brier_score(predictions: list[float], outcomes: list[int]) -> float:
    if not predictions:
        return float("nan")
    return sum((p - o) ** 2 for p, o in zip(predictions, outcomes)) / len(predictions)


def log_loss(predictions: list[float], outcomes: list[int], eps: float = 1e-12) -> float:
    if not predictions:
        return float("nan")
    total = 0.0
    for p, o in zip(predictions, outcomes):
        p = min(max(p, eps), 1 - eps)
        total += -(o * math.log(p) + (1 - o) * math.log(1 - p))
    return total / len(predictions)


def calibration_bins(
    predictions: list[float], outcomes: list[int], n_bins: int = 10
) -> list[dict[str, float]]:
    """Reliability table: mean prediction vs observed rate per bin."""
    bins: list[list[tuple[float, int]]] = [[] for _ in range(n_bins)]
    for p, o in zip(predictions, outcomes):
        idx = min(int(p * n_bins), n_bins - 1)
        bins[idx].append((p, o))
    table = []
    for i, bucket in enumerate(bins):
        if not bucket:
            continue
        mean_p = sum(p for p, _ in bucket) / len(bucket)
        rate = sum(o for _, o in bucket) / len(bucket)
        table.append(
            {
                "bin": i,
                "count": len(bucket),
                "mean_prediction": mean_p,
                "observed_rate": rate,
                "gap": mean_p - rate,
            }
        )
    return table


def calibration_quality(predictions: list[float], outcomes: list[int]) -> float:
    """0..1 score used by the opportunity ranker; 1 = perfectly calibrated.

    Based on the expected calibration error (ECE) over reliability bins.
    """
    table = calibration_bins(predictions, outcomes)
    if not table:
        return 0.5  # unknown → neutral
    n = sum(row["count"] for row in table)
    ece = sum(row["count"] * abs(row["gap"]) for row in table) / n
    return max(0.0, 1.0 - 4.0 * ece)  # ECE of 0.25+ → zero quality


@dataclass
class ShrinkageCalibrator:
    """Blend model output toward the market-implied probability.

    With little live evidence the model earns only a small share of the final
    estimate; the blend weight grows with the graded sample. This is a
    deliberately conservative stand-in until an isotonic/Platt calibrator is
    fitted from back-test data.
    """

    graded_samples: int = 0
    full_trust_samples: int = 2000
    max_model_share: float = 0.7

    def model_share(self) -> float:
        frac = min(1.0, self.graded_samples / self.full_trust_samples)
        return self.max_model_share * frac

    def calibrate(self, model_p: float, market_p: float | None) -> float:
        if market_p is None:
            return model_p
        share = self.model_share()
        return share * model_p + (1.0 - share) * market_p


@dataclass
class PerformanceTracker:
    """Rolling record of graded predictions for calibration monitoring."""

    predictions: list[float] = field(default_factory=list)
    outcomes: list[int] = field(default_factory=list)
    window: int = 5000

    def record(self, prediction: float, outcome: int) -> None:
        self.predictions.append(prediction)
        self.outcomes.append(outcome)
        if len(self.predictions) > self.window:
            self.predictions = self.predictions[-self.window:]
            self.outcomes = self.outcomes[-self.window:]

    def report(self) -> dict[str, float]:
        return {
            "n": len(self.predictions),
            "brier": brier_score(self.predictions, self.outcomes),
            "log_loss": log_loss(self.predictions, self.outcomes),
            "calibration_quality": calibration_quality(self.predictions, self.outcomes),
        }
