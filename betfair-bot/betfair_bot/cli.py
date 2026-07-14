"""Command-line entry point.

    betfair-bot run              # full daily cycle (paper mode by default)
    betfair-bot scan             # one-off market discovery + price snapshot
    betfair-bot report           # print today's report
    betfair-bot check-config     # validate config and credentials presence
    betfair-bot fit-football     # fit team ratings from football-data.co.uk
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import date

from .betfair.client import BetfairClient
from .config import load_config
from .execution.executor import LiveExecutor, PaperExecutor
from .modeling.calibration import ShrinkageCalibrator
from .models import Sport
from .pipeline import DecisionPipeline
from .research.afl_nrl import AflNrlResearch
from .research.feature_store import FeatureStore
from .research.football import FootballResearch
from .research.racing import RacingResearch
from .research.tennis import TennisResearch
from .risk.engine import RiskEngine
from .reporting.daily_report import build_report
from .scheduler.daily_cycle import DailyCycle
from .storage import ratings as ratings_store
from .storage.db import Store


def build_research_modules() -> dict:
    """Research modules, loading any fitted ratings from data/ratings/."""
    football_ratings, _home_adv = ratings_store.load_football()
    tennis_ratings = ratings_store.load_tennis()
    if football_ratings:
        logging.info("Loaded fitted football ratings for %d teams", len(football_ratings))
    if tennis_ratings:
        logging.info("Loaded fitted tennis Elo for %d players", len(tennis_ratings))
    return {
        Sport.HORSE_RACING: RacingResearch(),
        Sport.GREYHOUNDS: RacingResearch(),
        Sport.FOOTBALL: FootballResearch(ratings=football_ratings),
        Sport.TENNIS: TennisResearch(ratings=tennis_ratings),
        Sport.AFL: AflNrlResearch(Sport.AFL),
        Sport.NRL: AflNrlResearch(Sport.NRL),
    }


def load_learned_parameters() -> tuple[dict, object | None]:
    """Learned per-sport ensemble weights + fitted calibrator, if present."""
    sport_weights = {}
    for sport in Sport:
        w = ratings_store.load_ensemble_weights(sport.value)
        if w:
            sport_weights[sport] = w
    calibrator = ratings_store.load_calibrator("global")
    return sport_weights, calibrator


def cmd_fit_football(args) -> int:
    from .data.football_data import fetch_seasons, load_files
    from .modeling.dixon_coles import fit_ratings, holdout_log_loss

    matches = []
    if args.csv:
        matches.extend(load_files(args.csv))
    if args.league and args.seasons:
        matches.extend(fetch_seasons(args.league, args.seasons.split(",")))
    if not matches:
        print("No matches loaded. Pass --csv files and/or --league E0 --seasons 2324,2425")
        return 1

    matches.sort(key=lambda m: m.played_at)
    split = int(len(matches) * 0.85)
    train, holdout = matches[:split], matches[split:]

    ratings, home_adv = fit_ratings(train)
    ll = holdout_log_loss(ratings, home_adv, holdout)
    path = ratings_store.save_football(ratings, home_adv)

    print(f"Fitted {len(ratings)} teams from {len(train)} matches "
          f"(home advantage {home_adv:.3f})")
    print(f"Holdout 3-way log loss on {len(holdout)} matches: {ll:.4f} "
          f"(uniform baseline: 1.0986)")
    top = sorted(ratings.items(), key=lambda kv: kv[1].attack / kv[1].defence, reverse=True)
    print("Strongest teams:")
    for name, r in top[:8]:
        print(f"  {name:24s} attack={r.attack:.2f} defence={r.defence:.2f} n={r.sample_size}")
    print(f"Saved to {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="betfair-bot")
    parser.add_argument(
        "command",
        choices=["run", "scan", "report", "check-config", "fit-football"],
    )
    parser.add_argument("--config", default=None, help="path to YAML config")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--csv", nargs="*", help="fit-football: local football-data CSV files")
    parser.add_argument("--league", default=None, help="fit-football: division code, e.g. E0")
    parser.add_argument("--seasons", default=None, help="fit-football: e.g. 2324,2425")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    cfg = load_config(args.config)

    if args.command == "fit-football":
        return cmd_fit_football(args)

    if args.command == "check-config":
        problems = []
        if not cfg.betfair.app_key:
            problems.append("BETFAIR_APP_KEY not set")
        if not cfg.betfair.username:
            problems.append("BETFAIR_USERNAME not set")
        if cfg.betfair.login == "certificate" and not cfg.betfair.cert_file:
            problems.append("BETFAIR_CERT_FILE not set (certificate login)")
        if cfg.mode == "live" and not cfg.live_enabled:
            problems.append("mode=live but BETFAIR_LIVE_CONFIRM=YES not set")
        print(f"mode: {cfg.mode} (live enabled: {cfg.live_enabled})")
        print(f"bankroll: {cfg.risk.bankroll}, kelly fraction: {cfg.risk.kelly_fraction}")
        print(f"min EV: {cfg.selection.minimum_expected_value:.1%}, "
              f"min confidence: {cfg.selection.minimum_model_confidence:.0%}")
        for p in problems:
            print(f"PROBLEM: {p}")
        return 1 if problems else 0

    store = Store(cfg.storage.get("sqlite_path", "data/betfair_bot.sqlite3"))

    if args.command == "report":
        print(build_report(store, date.today().isoformat()))
        return 0

    client = BetfairClient(cfg.betfair)
    feature_store = FeatureStore(
        max_fact_age_hours=float(cfg.research.get("max_fact_age_hours", 48))
    )
    risk = RiskEngine(cfg.risk)
    sport_weights, fitted_calibrator = load_learned_parameters()
    if sport_weights:
        logging.info("Loaded learned ensemble weights for %s",
                     [s.value for s in sport_weights])
    if fitted_calibrator:
        logging.info("Loaded fitted logistic calibrator")
    pipeline = DecisionPipeline(
        cfg, build_research_modules(), feature_store,
        fitted_calibrator or ShrinkageCalibrator(),
        price_history_fn=store.price_history,
        sport_weights=sport_weights,
    )

    prefix = str(cfg.execution.get("customer_ref_prefix", "d1bot"))
    if cfg.live_enabled:
        executor = LiveExecutor(
            risk, client,
            persistence_type=str(cfg.execution.get("persistence_type", "LAPSE")),
            order_timeout_seconds=float(cfg.execution.get("order_timeout_seconds", 20)),
            customer_ref_prefix=prefix,
        )
        logging.warning("LIVE execution enabled — real orders will be placed")
    else:
        executor = PaperExecutor(risk, client, customer_ref_prefix=prefix)
        logging.info("Paper mode — no real orders will be placed")

    cycle = DailyCycle(cfg, client, pipeline, executor, store)

    if args.command == "scan":
        client.login()
        cycle.discover()
        cycle.refresh_all_prices()
        print(f"Tracking {len(cycle.tracked)} markets")
        for t in list(cycle.tracked.values())[:20]:
            s = t.snapshot
            print(f"  {s.sport.value:14s} {s.start_time:%H:%M} {s.event_name[:50]:50s} "
                  f"matched={s.total_matched:>12,.0f}")
        return 0

    # run
    client.login()
    try:
        asyncio.run(cycle.run_forever())
    except KeyboardInterrupt:
        print("shutting down")
    return 0


if __name__ == "__main__":
    sys.exit(main())
