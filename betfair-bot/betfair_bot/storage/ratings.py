"""Persistence for fitted model parameters (ratings, weights, calibration).

JSON on disk so fits survive restarts and are human-inspectable; the CLI fit
commands write here and the research modules load from here at startup.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ..modeling.logistic_calibration import LogisticCalibrator
from ..research.football import TeamRating
from ..research.tennis import SURFACES, PlayerRating

DEFAULT_DIR = Path("data/ratings")


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload["fitted_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))


def save_football(
    ratings: dict[str, TeamRating], home_advantage: float, path: Path | None = None
) -> Path:
    path = path or DEFAULT_DIR / "football.json"
    _write(path, {
        "home_advantage": home_advantage,
        "teams": {
            t: {"attack": r.attack, "defence": r.defence, "sample_size": r.sample_size}
            for t, r in ratings.items()
        },
    })
    return path


def load_football(path: Path | None = None) -> tuple[dict[str, TeamRating], float]:
    path = path or DEFAULT_DIR / "football.json"
    if not path.exists():
        return {}, 1.25
    data = json.loads(path.read_text())
    return (
        {
            t: TeamRating(r["attack"], r["defence"], int(r["sample_size"]))
            for t, r in data.get("teams", {}).items()
        },
        float(data.get("home_advantage", 1.25)),
    )


def save_tennis(ratings: dict[str, PlayerRating], path: Path | None = None) -> Path:
    path = path or DEFAULT_DIR / "tennis.json"
    _write(path, {
        "players": {
            name: {"elo": r.elo, "matches": r.matches} for name, r in ratings.items()
        },
    })
    return path


def load_tennis(path: Path | None = None) -> dict[str, PlayerRating]:
    path = path or DEFAULT_DIR / "tennis.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    out = {}
    for name, r in data.get("players", {}).items():
        pr = PlayerRating(matches=int(r.get("matches", 0)))
        for s in SURFACES:
            pr.elo[s] = float(r.get("elo", {}).get(s, 1500.0))
        out[name] = pr
    return out


def save_ensemble_weights(weights: dict[str, float], sport: str, path: Path | None = None) -> Path:
    path = path or DEFAULT_DIR / f"weights_{sport}.json"
    _write(path, {"weights": weights})
    return path


def load_ensemble_weights(sport: str, path: Path | None = None) -> dict[str, float] | None:
    path = path or DEFAULT_DIR / f"weights_{sport}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text()).get("weights")


def save_calibrator(cal: LogisticCalibrator, sport: str, path: Path | None = None) -> Path:
    path = path or DEFAULT_DIR / f"calibration_{sport}.json"
    _write(path, {"a": cal.a, "b": cal.b, "c": cal.c, "n_fitted": cal.n_fitted})
    return path


def load_calibrator(sport: str, path: Path | None = None) -> LogisticCalibrator | None:
    path = path or DEFAULT_DIR / f"calibration_{sport}.json"
    if not path.exists():
        return None
    d = json.loads(path.read_text())
    return LogisticCalibrator(a=d["a"], b=d["b"], c=d["c"], n_fitted=int(d.get("n_fitted", 0)))
