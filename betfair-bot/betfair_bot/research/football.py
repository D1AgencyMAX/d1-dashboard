"""Football research module.

Primary model: Dixon–Coles adjusted Poisson over a score grid, driven by
opponent-adjusted attack/defence ratings (expected goals). Produces MATCH_ODDS
(home/draw/away) and OVER_UNDER_25 probabilities. The market-implied
probability enters the ensemble as its own component; availability facts
(line-ups, keeper out, suspensions) adjust the goal expectations before the
grid is computed.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass

from ..models import ComponentEstimate, MarketSnapshot
from ..modeling.market_prior import market_implied_probabilities
from .base import ResearchModule
from .feature_store import FeatureStore

log = logging.getLogger(__name__)

MAX_GOALS = 10


@dataclass
class TeamRating:
    """Opponent-adjusted strengths, fitted offline from historical results/xG."""

    attack: float = 1.0   # multiplicative goal-scoring strength
    defence: float = 1.0  # multiplicative goals-conceded factor (lower is better)
    sample_size: int = 0


def _poisson_pmf(lam: float, k: int) -> float:
    return math.exp(-lam) * lam**k / math.factorial(k)


def dixon_coles_tau(x: int, y: int, lam: float, mu: float, rho: float) -> float:
    """Low-score dependence correction from Dixon & Coles (1997)."""
    if x == 0 and y == 0:
        return 1.0 - lam * mu * rho
    if x == 0 and y == 1:
        return 1.0 + lam * rho
    if x == 1 and y == 0:
        return 1.0 + mu * rho
    if x == 1 and y == 1:
        return 1.0 - rho
    return 1.0


def score_grid(lam_home: float, lam_away: float, rho: float = -0.05) -> list[list[float]]:
    """P(home=x, away=y) for x,y in 0..MAX_GOALS, renormalised."""
    grid = [
        [
            _poisson_pmf(lam_home, x)
            * _poisson_pmf(lam_away, y)
            * dixon_coles_tau(x, y, lam_home, lam_away, rho)
            for y in range(MAX_GOALS + 1)
        ]
        for x in range(MAX_GOALS + 1)
    ]
    total = sum(sum(row) for row in grid)
    return [[p / total for p in row] for row in grid]


def match_odds_probs(grid: list[list[float]]) -> tuple[float, float, float]:
    """(home win, draw, away win) from a score grid."""
    home = sum(grid[x][y] for x in range(MAX_GOALS + 1) for y in range(MAX_GOALS + 1) if x > y)
    draw = sum(grid[x][x] for x in range(MAX_GOALS + 1))
    away = 1.0 - home - draw
    return home, draw, away


def over_under_25(grid: list[list[float]]) -> tuple[float, float]:
    """(over 2.5 goals, under 2.5 goals)."""
    under = sum(
        grid[x][y] for x in range(MAX_GOALS + 1) for y in range(MAX_GOALS + 1) if x + y <= 2
    )
    return 1.0 - under, under


def expected_goals(
    home: TeamRating,
    away: TeamRating,
    league_avg_goals: float = 1.35,
    home_advantage: float = 1.25,
) -> tuple[float, float]:
    lam_home = league_avg_goals * home.attack * away.defence * home_advantage
    lam_away = league_avg_goals * away.attack * home.defence
    return lam_home, lam_away


class FootballResearch(ResearchModule):
    required_fact_types = ["lineup_change", "player_injury", "weather"]

    #: goal-expectation multipliers applied per confirmed availability fact
    IMPACT = {
        ("player_injury", "confirmed_out"): 0.93,   # generic starter absent
        ("goalkeeper_out", "confirmed_out"): 0.85,  # keeper absences hurt defence most
        ("suspension", "confirmed_out"): 0.93,
    }

    def __init__(self, ratings: dict[str, TeamRating] | None = None):
        self.ratings = ratings or {}

    def _rating(self, team: str) -> TeamRating:
        return self.ratings.get(team, TeamRating())

    def _availability_multiplier(self, team: str, market: MarketSnapshot, store: FeatureStore) -> float:
        mult = 1.0
        for fact in store.facts(market.event_id):
            if team.lower() not in str(fact.subject).lower():
                continue
            key = (fact.fact_type, str(fact.value))
            if key in self.IMPACT and (fact.official or fact.source_reliability >= 0.8):
                mult *= self.IMPACT[key]
        return mult

    def component_estimates(
        self, market: MarketSnapshot, store: FeatureStore
    ) -> dict[int, list[ComponentEstimate]]:
        market_probs = market_implied_probabilities(market)
        runners = market.active_runners
        estimates: dict[int, list[ComponentEstimate]] = {r.selection_id: [] for r in runners}

        # Market consensus component is always available.
        for sid, p in market_probs.items():
            if sid in estimates:
                estimates[sid].append(
                    ComponentEstimate(
                        component="independent_market_consensus",
                        probability=p,
                        confidence=min(1.0, market.total_matched / 50_000.0 + 0.4),
                        sample_size=1000,
                    )
                )

        # Model component requires MATCH_ODDS structure (home/away as first two
        # runners by Betfair convention; third runner is The Draw) or O/U.
        if market.market_type == "MATCH_ODDS" and len(runners) == 3:
            home_name, away_name = runners[0].name, runners[1].name
            home_r, away_r = self._rating(home_name), self._rating(away_name)
            if home_r.sample_size and away_r.sample_size:
                lam_h, lam_a = expected_goals(home_r, away_r)
                lam_h *= self._availability_multiplier(home_name, market, store)
                lam_a *= self._availability_multiplier(away_name, market, store)
                grid = score_grid(lam_h, lam_a)
                p_home, p_draw, p_away = match_odds_probs(grid)
                n = min(home_r.sample_size, away_r.sample_size)
                conf = min(0.9, 0.4 + n / 500.0)
                for runner, p in zip(runners, (p_home, p_away, p_draw)):
                    estimates[runner.selection_id].append(
                        ComponentEstimate(
                            component="historical_model",
                            probability=p,
                            confidence=conf,
                            sample_size=n,
                        )
                    )
        elif market.market_type == "OVER_UNDER_25" and len(runners) == 2:
            # Runner names distinguish Under/Over on Betfair.
            names = [r.name.lower() for r in runners]
            teams = market.event_name.split(" v ")
            if len(teams) == 2:
                home_r, away_r = self._rating(teams[0]), self._rating(teams[1])
                if home_r.sample_size and away_r.sample_size:
                    lam_h, lam_a = expected_goals(home_r, away_r)
                    over, under = over_under_25(score_grid(lam_h, lam_a))
                    n = min(home_r.sample_size, away_r.sample_size)
                    conf = min(0.9, 0.4 + n / 500.0)
                    for runner, name in zip(runners, names):
                        p = under if "under" in name else over
                        estimates[runner.selection_id].append(
                            ComponentEstimate(
                                component="historical_model",
                                probability=p,
                                confidence=conf,
                                sample_size=n,
                            )
                        )

        return estimates

    def selections_confirmed(self, market, store, now=None) -> bool:
        """Within 90 minutes of kickoff, require line-up facts before betting."""
        if market.seconds_to_start(now) > 90 * 60:
            return True
        return any(f.fact_type in ("lineup", "lineup_change")
                   for f in store.facts(market.event_id, now=now))
