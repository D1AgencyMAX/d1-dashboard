"""Ensemble weight learning: replace hand-set priors with fitted weights.

Given a history of graded predictions — each with the component probabilities
that were available at decision time and the eventual outcome — learn the
weight vector that minimises log loss. Weights live on the probability
simplex via a softmax parameterisation, so they stay positive and sum to 1.

Also reports each component's marginal contribution (loss increase when the
component is removed), which is the "does this source still add predictive
value?" test the research spec requires.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class GradedSample:
    """One selection's component probabilities and its graded outcome."""

    component_probs: dict[str, float]     # component name -> probability
    outcome: int                          # 1 if the selection won, else 0


@dataclass
class WeightFit:
    weights: dict[str, float]
    log_loss: float
    baseline_log_loss: float              # equal-weight loss, for comparison
    marginal_value: dict[str, float] = field(default_factory=dict)
    n_samples: int = 0


def _clamp(p: float) -> float:
    return min(max(p, 1e-6), 1.0 - 1e-6)


def _loss(theta: dict[str, float], samples: list[GradedSample]) -> float:
    weights = _softmax(theta)
    total = 0.0
    for s in samples:
        present = {k: v for k, v in s.component_probs.items() if k in weights}
        if not present:
            continue
        wsum = sum(weights[k] for k in present)
        p = _clamp(sum(weights[k] * present[k] for k in present) / wsum)
        total += -(s.outcome * math.log(p) + (1 - s.outcome) * math.log(1 - p))
    return total / max(len(samples), 1)


def _softmax(theta: dict[str, float]) -> dict[str, float]:
    m = max(theta.values())
    exps = {k: math.exp(v - m) for k, v in theta.items()}
    z = sum(exps.values())
    return {k: v / z for k, v in exps.items()}


def fit_weights(
    samples: list[GradedSample],
    components: list[str],
    iterations: int = 300,
    learning_rate: float = 0.5,
    eps: float = 1e-4,
) -> WeightFit:
    """Learn ensemble weights by finite-difference gradient descent on log loss.

    The parameter space is tiny (one theta per component), so numeric
    gradients are robust and dependency-free. Components missing from a
    sample are handled by renormalising over those present, matching how the
    live ensemble treats missing sources.
    """
    if not samples:
        raise ValueError("no graded samples")
    theta = {c: 0.0 for c in components}
    baseline = _loss(theta, samples)

    for _ in range(iterations):
        grad = {}
        f0 = _loss(theta, samples)
        for c in components:
            theta[c] += eps
            grad[c] = (_loss(theta, samples) - f0) / eps
            theta[c] -= eps
        for c in components:
            theta[c] -= learning_rate * grad[c]

    weights = _softmax(theta)
    final = _loss(theta, samples)

    # Marginal contribution: how much loss rises with the component removed.
    marginal: dict[str, float] = {}
    for c in components:
        reduced = {k: v for k, v in theta.items() if k != c}
        if reduced:
            marginal[c] = _loss(reduced, samples) - final

    return WeightFit(
        weights=weights,
        log_loss=final,
        baseline_log_loss=baseline,
        marginal_value=marginal,
        n_samples=len(samples),
    )


def prune_useless_components(fit: WeightFit, min_marginal: float = 0.0) -> list[str]:
    """Components whose removal does not hurt (or helps) — candidates to drop."""
    return [c for c, v in fit.marginal_value.items() if v <= min_marginal]
