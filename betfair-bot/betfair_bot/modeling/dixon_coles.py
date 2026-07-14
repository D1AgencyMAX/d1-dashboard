"""Dixon–Coles rating fitter: maximum-likelihood attack/defence estimation.

Fits multiplicative attack and defence strengths plus home advantage from
historical results by gradient ascent on the time-decayed Poisson
log-likelihood. Recent matches count more (exponential decay, half-life in
days). Output plugs straight into `research.football.TeamRating`.

Pure Python on purpose: a few hundred teams × a few thousand matches fits in
well under a second, and there is no numerical dependency to break on a
minimal server.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

from ..research.football import TeamRating


@dataclass
class MatchResult:
    home: str
    away: str
    home_goals: int
    away_goals: int
    played_at: datetime


def _decay_weight(played_at: datetime, as_of: datetime, half_life_days: float) -> float:
    age_days = max(0.0, (as_of - played_at).total_seconds() / 86400.0)
    return 0.5 ** (age_days / half_life_days)


def fit_ratings(
    matches: list[MatchResult],
    as_of: datetime | None = None,
    half_life_days: float = 180.0,
    iterations: int = 400,
    learning_rate: float = 0.05,
    l2: float = 0.01,
) -> tuple[dict[str, TeamRating], float]:
    """Fit team ratings; returns ({team: TeamRating}, home_advantage).

    Model: lam_home = base * attack_h * defence_a * home_adv,
           lam_away = base * attack_a * defence_h
    where base is the decayed league-average goals per side. Parameters are
    optimised in log space (positivity) with an L2 pull toward neutral (1.0)
    so thin samples shrink to average instead of exploding. Attack ratings are
    renormalised to mean 1 each step to fix the scale degeneracy.
    """
    if not matches:
        return {}, 1.25
    as_of = as_of or max(m.played_at for m in matches)

    weights = [_decay_weight(m.played_at, as_of, half_life_days) for m in matches]
    total_w = sum(weights)
    base = sum(
        w * (m.home_goals + m.away_goals) for w, m in zip(weights, matches)
    ) / (2.0 * total_w)
    base = max(base, 0.1)

    teams = sorted({m.home for m in matches} | {m.away for m in matches})
    log_attack = {t: 0.0 for t in teams}
    log_defence = {t: 0.0 for t in teams}
    log_home_adv = math.log(1.25)

    # Effective (decayed) match count per team, for shrinkage-aware sample sizes.
    eff_n: dict[str, float] = {t: 0.0 for t in teams}
    for w, m in zip(weights, matches):
        eff_n[m.home] += w
        eff_n[m.away] += w

    for _ in range(iterations):
        g_attack = {t: 0.0 for t in teams}
        g_defence = {t: 0.0 for t in teams}
        g_home = 0.0

        for w, m in zip(weights, matches):
            lam_h = base * math.exp(
                log_attack[m.home] + log_defence[m.away] + log_home_adv
            )
            lam_a = base * math.exp(log_attack[m.away] + log_defence[m.home])
            # d(logL)/d(log x) = k - lam for every log-parameter lam scales with.
            rh = w * (m.home_goals - lam_h)
            ra = w * (m.away_goals - lam_a)
            g_attack[m.home] += rh
            g_defence[m.away] += rh
            g_home += rh
            g_attack[m.away] += ra
            g_defence[m.home] += ra

        for t in teams:
            n = max(eff_n[t], 1e-9)
            log_attack[t] += learning_rate * (g_attack[t] / n - l2 * log_attack[t])
            log_defence[t] += learning_rate * (g_defence[t] / n - l2 * log_defence[t])
        log_home_adv += learning_rate * g_home / max(total_w, 1e-9)

        # Fix scale: mean log-attack = 0 (mean attack ≈ 1); same for defence.
        # The removed shift affects home and away rates identically, so it
        # belongs in the base rate — folding it into home advantage would
        # corrupt away-goal expectations.
        mean_a = sum(log_attack.values()) / len(teams)
        mean_d = sum(log_defence.values()) / len(teams)
        for t in teams:
            log_attack[t] -= mean_a
            log_defence[t] -= mean_d
        base *= math.exp(mean_a + mean_d)

    ratings = {
        t: TeamRating(
            attack=math.exp(log_attack[t]),
            defence=math.exp(log_defence[t]),
            sample_size=int(round(eff_n[t])),
        )
        for t in teams
    }
    return ratings, math.exp(log_home_adv)


def holdout_log_loss(
    ratings: dict[str, TeamRating],
    home_advantage: float,
    matches: list[MatchResult],
    league_avg_goals: float = 1.35,
) -> float:
    """Mean 3-way (H/D/A) log loss of fitted ratings on held-out matches."""
    from ..research.football import match_odds_probs, score_grid

    if not matches:
        return float("nan")
    total = 0.0
    for m in matches:
        hr = ratings.get(m.home, TeamRating())
        ar = ratings.get(m.away, TeamRating())
        lam_h = league_avg_goals * hr.attack * ar.defence * home_advantage
        lam_a = league_avg_goals * ar.attack * hr.defence
        ph, pd_, pa = match_odds_probs(score_grid(lam_h, lam_a))
        if m.home_goals > m.away_goals:
            p = ph
        elif m.home_goals == m.away_goals:
            p = pd_
        else:
            p = pa
        total += -math.log(max(p, 1e-12))
    return total / len(matches)
