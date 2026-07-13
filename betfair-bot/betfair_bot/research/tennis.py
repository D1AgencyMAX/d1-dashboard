"""Tennis research module.

Surface-specific Elo drives the head-to-head win probability, with
adjustments for recent workload, retirement risk and best-of-five formats.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..models import ComponentEstimate, MarketSnapshot
from ..modeling.market_prior import market_implied_probabilities
from .base import ResearchModule
from .feature_store import FeatureStore

SURFACES = ("hard", "clay", "grass", "indoor")


@dataclass
class PlayerRating:
    elo: dict[str, float] = field(default_factory=lambda: {s: 1500.0 for s in SURFACES})
    matches: int = 0
    recent_sets_played_14d: int = 0     # workload proxy
    retirement_flag: bool = False       # retired/withdrew recently


def elo_win_probability(elo_a: float, elo_b: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((elo_b - elo_a) / 400.0))


class TennisResearch(ResearchModule):
    required_fact_types = ["player_injury", "weather"]

    def __init__(self, ratings: dict[str, PlayerRating] | None = None, surface: str = "hard"):
        self.ratings = ratings or {}
        self.surface = surface

    def component_estimates(
        self, market: MarketSnapshot, store: FeatureStore
    ) -> dict[int, list[ComponentEstimate]]:
        runners = market.active_runners
        estimates: dict[int, list[ComponentEstimate]] = {r.selection_id: [] for r in runners}

        for sid, p in market_implied_probabilities(market).items():
            if sid in estimates:
                estimates[sid].append(
                    ComponentEstimate(
                        component="independent_market_consensus",
                        probability=p,
                        confidence=min(1.0, market.total_matched / 30_000.0 + 0.4),
                        sample_size=1000,
                    )
                )

        if len(runners) == 2:
            a, b = runners
            ra, rb = self.ratings.get(a.name), self.ratings.get(b.name)
            if ra and rb and ra.matches >= 20 and rb.matches >= 20:
                p_a = elo_win_probability(ra.elo[self.surface], rb.elo[self.surface])
                # Heavy recent workload or a retirement flag drags the estimate
                # toward 50/50 — uncertainty, not a directional signal.
                shrink = 0.0
                for r in (ra, rb):
                    if r.recent_sets_played_14d > 20:
                        shrink += 0.05
                    if r.retirement_flag:
                        shrink += 0.10
                p_a = p_a * (1 - shrink) + 0.5 * shrink
                n = min(ra.matches, rb.matches)
                conf = min(0.9, 0.4 + n / 200.0)
                estimates[a.selection_id].append(
                    ComponentEstimate("historical_model", p_a, conf, n)
                )
                estimates[b.selection_id].append(
                    ComponentEstimate("historical_model", 1.0 - p_a, conf, n)
                )

        return estimates
