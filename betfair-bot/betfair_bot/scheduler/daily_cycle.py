"""Daily operating cycle.

04:00        discover every configured market starting in the next 24 hours
04:15 →      research each event; recalculate every 15–60 minutes as prices
             move, selections firm, scratches occur and news arrives
pre-event    sport-specific final checkpoints (racing 10/5/2/1 min, football
             6h/90m/15m, tennis 4h/30m/5m, AFL/NRL 6h/60m/10m); the order is
             placed only after one final validation of price, freshness,
             exposure and liquidity
22:00        daily report

Implemented as a single asyncio loop with a checkpoint queue rather than a
heavyweight workflow engine; Prefect/Airflow can wrap `run_once` later without
changing the decision code.
"""

from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from ..betfair.catalogue import discover_markets
from ..betfair.client import BetfairClient
from ..betfair.prices import refresh_prices
from ..config import BotConfig
from ..execution.executor import Executor
from ..models import MarketSnapshot
from ..pipeline import DecisionPipeline
from ..reporting.daily_report import build_report
from ..storage.db import Store

log = logging.getLogger(__name__)


@dataclass
class TrackedMarket:
    snapshot: MarketSnapshot
    checkpoints: list[float] = field(default_factory=list)  # minutes before start, desc
    next_recalc: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    done: bool = False


class DailyCycle:
    def __init__(
        self,
        cfg: BotConfig,
        client: BetfairClient,
        pipeline: DecisionPipeline,
        executor: Executor,
        store: Store,
    ):
        self.cfg = cfg
        self.client = client
        self.pipeline = pipeline
        self.executor = executor
        self.store = store
        self.tracked: dict[str, TrackedMarket] = {}

    # ------------------------------------------------------------ discovery

    def discover(self) -> None:
        snapshots = discover_markets(self.client, self.cfg.discovery)
        checkpoints_cfg = self.cfg.research.get("final_checks_minutes", {})
        for snap in snapshots:
            if snap.market_id in self.tracked:
                continue
            minutes = sorted(
                (float(m) for m in checkpoints_cfg.get(snap.sport.value, [15, 5])),
                reverse=True,
            )
            self.tracked[snap.market_id] = TrackedMarket(snapshot=snap, checkpoints=minutes)
            self.store.save_market(snap)
        self.store.audit("discovery", f"{len(snapshots)} markets, {len(self.tracked)} tracked")
        log.info("Tracking %d markets", len(self.tracked))

    # ------------------------------------------------------------- research

    def _recalc_delay(self) -> timedelta:
        lo = int(self.cfg.research.get("recalc_minutes_min", 15))
        hi = int(self.cfg.research.get("recalc_minutes_max", 60))
        return timedelta(minutes=random.randint(lo, hi))

    def refresh_all_prices(self) -> None:
        open_markets = {
            mid: t.snapshot
            for mid, t in self.tracked.items()
            if not t.done and t.snapshot.status != "CLOSED"
        }
        if not open_markets:
            return
        refresh_prices(self.client, open_markets)
        for snap in open_markets.values():
            self.store.save_price_snapshot(snap)

    def recalculate(self, tracked: TrackedMarket, now: datetime) -> None:
        """Re-run estimates for one market and persist the decision trail."""
        market = tracked.snapshot
        ranked, rejections = self.pipeline.evaluate_market(
            market, api_healthy=self.client.healthy, now=now
        )
        for opp in ranked:
            self.store.save_opportunity(opp, decision="QUALIFIED", reasons=[])
        for selection_id, reasons in rejections.items():
            log.debug(
                "reject %s/%s: %s", market.market_id, selection_id, [r.value for r in reasons]
            )
        tracked.next_recalc = now + self._recalc_delay()

    # ------------------------------------------------------------ execution

    def final_check_and_execute(self, tracked: TrackedMarket, now: datetime) -> None:
        market = tracked.snapshot
        ranked, _ = self.pipeline.evaluate_market(
            market, api_healthy=self.client.healthy, now=now
        )
        if not ranked:
            return
        placed = self.executor.execute(ranked)
        for bet in placed:
            self.store.save_bet(bet)
        if placed:
            tracked.done = True  # one position per market

    # ---------------------------------------------------------------- loop

    async def run_once(self) -> None:
        """One pass: refresh prices, run due recalcs and due final checkpoints."""
        now = datetime.now(timezone.utc)
        self.refresh_all_prices()

        for tracked in list(self.tracked.values()):
            if tracked.done:
                continue
            market = tracked.snapshot
            secs = market.seconds_to_start(now)

            if market.status == "CLOSED" or secs < -300:
                tracked.done = True
                continue

            # Final pre-event checkpoints take priority over routine recalcs.
            while tracked.checkpoints and secs <= tracked.checkpoints[0] * 60:
                tracked.checkpoints.pop(0)
                self.final_check_and_execute(tracked, now)
                if tracked.done:
                    break

            if not tracked.done and now >= tracked.next_recalc:
                self.recalculate(tracked, now)

    async def run_forever(self) -> None:
        """The full daily cycle. Runs until cancelled."""
        discovery_hour = int(str(self.cfg.discovery.get("run_at", "04:00")).split(":")[0])
        report_hour = int(self.cfg.raw.get("reporting", {}).get("daily_report_hour", 22))
        last_discovery_day = None
        last_report_day = None
        poll = int(self.cfg.betfair.price_poll_seconds)

        while True:
            now_local = datetime.now(timezone.utc)  # cron alignment is by UTC hour of tz-adjusted deployment
            if last_discovery_day != now_local.date() and now_local.hour >= discovery_hour:
                self.discover()
                last_discovery_day = now_local.date()
            try:
                await self.run_once()
            except Exception:
                log.exception("cycle error; continuing")
            if last_report_day != now_local.date() and now_local.hour >= report_hour:
                report = build_report(self.store, now_local.date().isoformat())
                self.store.audit("daily_report", report)
                log.info("\n%s", report)
                last_report_day = now_local.date()
            self.client.keep_alive()
            await asyncio.sleep(poll)
