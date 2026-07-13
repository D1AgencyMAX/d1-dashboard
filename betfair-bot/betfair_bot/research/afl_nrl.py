"""AFL and NRL research module.

Team ratings produce an expected margin; the win probability is the normal
CDF of that margin over the sport's historical margin volatility. Late team
changes and venue/travel effects adjust the expected margin before conversion.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..models import ComponentEstimate, MarketSnapshot, Sport
from ..modeling.market_prior import market_implied_probabilities
from .base import ResearchModule
from .feature_store import FeatureStore

# Historical margin standard deviations (points).
MARGIN_SIGMA = {Sport.AFL: 36.0, Sport.NRL: 15.0}
HOME_ADVANTAGE = {Sport.AFL: 8.0, Sport.NRL: 3.0}


@dataclass
class TeamStrength:
    rating: float = 0.0            # points above an average team on neutral ground
    games: int = 0
    key_players_out: int = 0       # confirmed unavailable best-22/best-17 players
    travel_penalty: float = 0.0    # points, e.g. interstate short turnaround

PLAYER_OUT_POINTS = {Sport.AFL: 2.0, Sport.NRL: 1.5}


def margin_to_win_probability(expected_margin: float, sigma: float) -> float:
    """P(win) from expected margin via the normal CDF (draws ignored)."""
    return 0.5 * (1.0 + math.erf(expected_margin / (sigma * math.sqrt(2.0))))


class AflNrlResearch(ResearchModule):
    required_fact_types = ["lineup_change", "player_injury", "weather"]

    def __init__(self, sport: Sport, strengths: dict[str, TeamStrength] | None = None):
        if sport not in (Sport.AFL, Sport.NRL):
            raise ValueError(f"unsupported sport: {sport}")
        self.sport = sport
        self.strengths = strengths or {}

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
                        confidence=min(1.0, market.total_matched / 40_000.0 + 0.4),
                        sample_size=1000,
                    )
                )

        if len(runners) == 2:
            home, away = runners  # Betfair lists home team first for AFL/NRL
            hs = self.strengths.get(home.name)
            as_ = self.strengths.get(away.name)
            if hs and as_ and hs.games >= 10 and as_.games >= 10:
                out_pts = PLAYER_OUT_POINTS[self.sport]
                margin = (
                    (hs.rating - as_.rating)
                    + HOME_ADVANTAGE[self.sport]
                    - hs.key_players_out * out_pts
                    + as_.key_players_out * out_pts
                    - hs.travel_penalty
                    + as_.travel_penalty
                )
                p_home = margin_to_win_probability(margin, MARGIN_SIGMA[self.sport])
                n = min(hs.games, as_.games)
                conf = min(0.85, 0.4 + n / 100.0)
                estimates[home.selection_id].append(
                    ComponentEstimate("historical_model", p_home, conf, n)
                )
                estimates[away.selection_id].append(
                    ComponentEstimate("historical_model", 1.0 - p_home, conf, n)
                )

        return estimates

    def selections_confirmed(self, market, store, now=None) -> bool:
        """Inside 90 minutes of the bounce/kickoff, require confirmed teams."""
        if market.seconds_to_start(now) > 90 * 60:
            return True
        return any(
            f.fact_type in ("lineup", "lineup_change")
            for f in store.facts(market.event_id, now=now)
        )
