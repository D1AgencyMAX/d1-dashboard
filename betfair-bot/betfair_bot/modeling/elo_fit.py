"""Surface-specific Elo fitting for tennis from match history.

Sequential Elo updates with a decaying K-factor (new players move fast,
established ratings move slowly) and cross-surface partial transfer, so a
clay result nudges the hard-court rating without dominating it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..research.tennis import SURFACES, PlayerRating, elo_win_probability


@dataclass
class TennisMatch:
    winner: str
    loser: str
    surface: str            # hard | clay | grass | indoor
    played_at: datetime


CROSS_SURFACE_TRANSFER = 0.35   # fraction of the update applied to other surfaces


def _k_factor(matches_played: int) -> float:
    """Decaying K: 40 for new players → ~16 for veterans."""
    return 16.0 + 24.0 * (0.995 ** matches_played)


def fit_elo(
    matches: list[TennisMatch],
    initial: dict[str, PlayerRating] | None = None,
) -> dict[str, PlayerRating]:
    """Replay matches chronologically, updating surface Elo after each.

    Point-in-time safe by construction: each rating only ever reflects matches
    played before it is read, so the same function serves back-testing.
    """
    ratings: dict[str, PlayerRating] = dict(initial or {})
    for m in sorted(matches, key=lambda x: x.played_at):
        surface = m.surface if m.surface in SURFACES else "hard"
        w = ratings.setdefault(m.winner, PlayerRating())
        l = ratings.setdefault(m.loser, PlayerRating())

        expected_w = elo_win_probability(w.elo[surface], l.elo[surface])
        delta_w = _k_factor(w.matches) * (1.0 - expected_w)
        delta_l = _k_factor(l.matches) * (0.0 - (1.0 - expected_w))

        w.elo[surface] += delta_w
        l.elo[surface] += delta_l
        for s in SURFACES:
            if s != surface:
                w.elo[s] += CROSS_SURFACE_TRANSFER * delta_w
                l.elo[s] += CROSS_SURFACE_TRANSFER * delta_l

        w.matches += 1
        l.matches += 1
    return ratings
