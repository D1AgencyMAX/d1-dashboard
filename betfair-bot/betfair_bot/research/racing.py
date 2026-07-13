"""Horse racing and greyhound research module.

Rates each runner from structured form features (speed ratings, distance/track
record, barrier, weight, jockey/trainer, days since run, gear changes), turns
ratings into win probabilities via a softmax, and blends with the Betfair
market prior. Scratches remove runners entirely and the field renormalises.

Production replaces `feature_score` with a gradient-boosted / pairwise-ranking
model; the softmax + market-prior structure stays the same.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone

from ..models import ComponentEstimate, MarketSnapshot
from ..modeling.market_prior import market_implied_probabilities
from .base import ResearchModule
from .feature_store import FeatureStore


@dataclass
class RunnerForm:
    """Point-in-time form features for one runner."""

    speed_rating: float = 0.0          # normalised 0..1 vs field
    distance_record: float = 0.5       # win/place rate at today's distance
    track_going_record: float = 0.5    # record on this track/going
    barrier_score: float = 0.5         # draw suitability 0..1
    weight_score: float = 0.5          # weight relative to field, 1 = well in
    jockey_trainer_score: float = 0.5  # combined J/T strike-rate percentile
    freshness_score: float = 0.5       # days-since-run suitability
    class_change_score: float = 0.5    # dropping in class > 0.5 > rising
    pace_score: float = 0.5            # projected pace-map suitability
    gear_change_bonus: float = 0.0     # e.g. first-time blinkers
    sample_size: int = 0

    WEIGHTS = {
        "speed_rating": 0.30,
        "distance_record": 0.12,
        "track_going_record": 0.12,
        "barrier_score": 0.08,
        "weight_score": 0.08,
        "jockey_trainer_score": 0.10,
        "freshness_score": 0.07,
        "class_change_score": 0.08,
        "pace_score": 0.05,
    }

    def feature_score(self) -> float:
        score = sum(w * getattr(self, k) for k, w in self.WEIGHTS.items())
        return score + self.gear_change_bonus


def softmax_probabilities(scores: dict[int, float], temperature: float = 0.12) -> dict[int, float]:
    """Convert runner scores to win probabilities.

    Lower temperature sharpens the distribution; the default is deliberately
    soft so the raw form model never overrides the market on its own.
    """
    if not scores:
        return {}
    exps = {sid: math.exp(s / temperature) for sid, s in scores.items()}
    total = sum(exps.values())
    return {sid: e / total for sid, e in exps.items()}


class RacingResearch(ResearchModule):
    required_fact_types = ["scratching", "track_condition", "gear_change"]

    def __init__(self, form: dict[int, RunnerForm] | None = None):
        # selection_id -> form; populated by the offline form-ingestion job.
        self.form = form or {}

    def component_estimates(
        self, market: MarketSnapshot, store: FeatureStore
    ) -> dict[int, list[ComponentEstimate]]:
        active = market.active_runners  # scratched runners carry status REMOVED
        estimates: dict[int, list[ComponentEstimate]] = {r.selection_id: [] for r in active}

        market_probs = market_implied_probabilities(market)
        for sid, p in market_probs.items():
            if sid in estimates:
                estimates[sid].append(
                    ComponentEstimate(
                        component="independent_market_consensus",
                        probability=p,
                        confidence=min(1.0, market.total_matched / 100_000.0 + 0.4),
                        sample_size=1000,
                    )
                )

        rated = {
            r.selection_id: self.form[r.selection_id]
            for r in active
            if r.selection_id in self.form
        }
        # Only rate the race when the whole active field has form; a partially
        # rated field would silently favour the runners we happen to know.
        if rated and len(rated) == len(active):
            scores = {sid: f.feature_score() for sid, f in rated.items()}
            probs = softmax_probabilities(scores)
            n = min(f.sample_size for f in rated.values())
            conf = min(0.85, 0.3 + n / 100.0)
            for sid, p in probs.items():
                estimates[sid].append(
                    ComponentEstimate(
                        component="historical_model",
                        probability=p,
                        confidence=conf,
                        sample_size=n,
                    )
                )

        return estimates

    def selections_confirmed(self, market, store, now=None) -> bool:
        """Close to the jump, require a fresh scratchings check.

        Betfair marks scratched runners REMOVED; we additionally require the
        order book to have been refreshed in the last two minutes so a late
        scratching cannot slip through on stale data.
        """
        if market.seconds_to_start(now) > 30 * 60:
            return True
        book_age = ((now or datetime.now(timezone.utc)) - market.captured_at).total_seconds()
        return book_age <= 120
