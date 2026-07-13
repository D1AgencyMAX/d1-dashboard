"""Weighted ensemble with correlation discounting and uncertainty bounds.

P_ensemble = sum(w_i * P_i) over research components, where the weights are
learned per sport/market (config supplies the initial priors). Components in
the same correlation group share one group's worth of weight, so five news
articles repeating one injury report never count as five confirmations.
"""

from __future__ import annotations

import math
from collections import defaultdict

from ..models import ComponentEstimate, ProbabilityEstimate


def _clamp(p: float, lo: float = 1e-4, hi: float = 1.0 - 1e-4) -> float:
    return max(lo, min(hi, p))


def effective_weights(
    components: list[ComponentEstimate],
    base_weights: dict[str, float],
) -> dict[int, float]:
    """Per-component effective weights after correlation discounting.

    1. Each component starts from its configured base weight (scaled by its
       own confidence).
    2. Components sharing a correlation_group split that group's total weight
       equally rather than stacking it.
    3. Weights are renormalised over the components actually present, so a
       missing source (e.g. no weather data) redistributes rather than
       silently deflating every probability.
    """
    raw: list[float] = []
    for c in components:
        w = base_weights.get(c.component, 0.0) * _clamp(c.confidence, 0.0, 1.0)
        raw.append(w)

    groups: dict[str, list[int]] = defaultdict(list)
    for idx, c in enumerate(components):
        if c.correlation_group:
            groups[c.correlation_group].append(idx)

    for indices in groups.values():
        if len(indices) > 1:
            group_total = max(raw[i] for i in indices)
            share = group_total / len(indices)
            for i in indices:
                raw[i] = share

    total = sum(raw)
    if total <= 0:
        return {i: 0.0 for i in range(len(components))}
    return {i: w / total for i, w in enumerate(raw)}


def combine(
    components: list[ComponentEstimate],
    base_weights: dict[str, float],
    market_id: str = "",
    selection_id: int = 0,
) -> ProbabilityEstimate:
    """Combine component probabilities into a single calibrated estimate.

    The lower/upper bounds widen with component disagreement and shrink with
    total evidence (sample size), so a thin or conflicted model produces a
    conservative bound that the EV filter then tests against break-even.
    """
    if not components:
        raise ValueError("no component estimates supplied")

    weights = effective_weights(components, base_weights)
    p = sum(weights[i] * _clamp(c.probability) for i, c in enumerate(components))
    p = _clamp(p)

    # Weighted dispersion between components = model disagreement.
    disagreement = math.sqrt(
        sum(weights[i] * (_clamp(c.probability) - p) ** 2 for i, c in enumerate(components))
    )

    # Confidence: weight-averaged component confidence, penalised by disagreement.
    confidence = sum(weights[i] * c.confidence for i, c in enumerate(components))
    confidence = _clamp(confidence * (1.0 - min(1.0, 2.0 * disagreement)), 0.0, 1.0)

    n = sum(c.sample_size for c in components)
    # Binomial-style standard error floored by half the component spread; a
    # small sample or a conflicted ensemble both widen the interval. The
    # disagreement floor is applied directly (not z-scaled) — disagreement is
    # already a full spread measure, and z-scaling it makes the bound grow
    # faster than any model edge, which would reject every bet by construction.
    se = math.sqrt(p * (1 - p) / max(n, 30))
    half_width = max(1.96 * se, disagreement / 2.0)

    return ProbabilityEstimate(
        market_id=market_id,
        selection_id=selection_id,
        probability=p,
        lower_bound=_clamp(p - half_width, 0.0, 1.0),
        upper_bound=_clamp(p + half_width, 0.0, 1.0),
        confidence=confidence,
        components=components,
        sample_size=n,
        disagreement=disagreement,
    )


def normalise_market(estimates: dict[int, ProbabilityEstimate]) -> dict[int, ProbabilityEstimate]:
    """Scale a win market's estimates so probabilities sum to 1.

    Bounds are scaled by the same factor so relative uncertainty is preserved.
    """
    total = sum(e.probability for e in estimates.values())
    if total <= 0:
        return estimates
    for est in estimates.values():
        factor = 1.0 / total
        est.probability = _clamp(est.probability * factor)
        est.lower_bound = _clamp(est.lower_bound * factor, 0.0, 1.0)
        est.upper_bound = _clamp(est.upper_bound * factor, 0.0, 1.0)
    return estimates
