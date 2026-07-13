"""Command-line entry point.

    betfair-bot run              # full daily cycle (paper mode by default)
    betfair-bot scan             # one-off market discovery + price snapshot
    betfair-bot report           # print today's report
    betfair-bot check-config     # validate config and credentials presence
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
from .storage.db import Store


def build_research_modules() -> dict:
    return {
        Sport.HORSE_RACING: RacingResearch(),
        Sport.GREYHOUNDS: RacingResearch(),
        Sport.FOOTBALL: FootballResearch(),
        Sport.TENNIS: TennisResearch(),
        Sport.AFL: AflNrlResearch(Sport.AFL),
        Sport.NRL: AflNrlResearch(Sport.NRL),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="betfair-bot")
    parser.add_argument("command", choices=["run", "scan", "report", "check-config"])
    parser.add_argument("--config", default=None, help="path to YAML config")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    cfg = load_config(args.config)

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
    pipeline = DecisionPipeline(cfg, build_research_modules(), feature_store,
                                ShrinkageCalibrator())

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
