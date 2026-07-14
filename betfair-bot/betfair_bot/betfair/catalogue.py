"""Daily market discovery via listMarketCatalogue."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from ..models import MarketSnapshot, RunnerBook, Sport
from .client import BetfairClient

log = logging.getLogger(__name__)

MARKET_PROJECTION = [
    "EVENT",
    "COMPETITION",
    "MARKET_START_TIME",
    "MARKET_DESCRIPTION",
    "RUNNER_DESCRIPTION",
]


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def discover_markets(
    client: BetfairClient,
    discovery_cfg: dict[str, Any],
    now: datetime | None = None,
) -> list[MarketSnapshot]:
    """Find every configured market starting within the next N hours.

    Returns catalogue-level snapshots (no prices yet); prices are attached by
    the price poller. turnInPlayEnabled is requested so in-play behaviour is
    known before any order is considered.
    """
    now = now or datetime.now(timezone.utc)
    horizon = now + timedelta(hours=discovery_cfg.get("hours_ahead", 24))
    min_matched = float(discovery_cfg.get("min_total_matched", 0))
    snapshots: list[MarketSnapshot] = []

    for sport_key, sport_cfg in (discovery_cfg.get("sports") or {}).items():
        try:
            sport = Sport(sport_key)
        except ValueError:
            log.warning("Unknown sport %r in config; skipping", sport_key)
            continue
        market_filter: dict[str, Any] = {
            "eventTypeIds": [sport_cfg["event_type_id"]],
            "marketTypeCodes": sport_cfg.get("market_types", []),
            "marketStartTime": {
                "from": now.isoformat().replace("+00:00", "Z"),
                "to": horizon.isoformat().replace("+00:00", "Z"),
            },
        }
        if sport_cfg.get("countries"):
            market_filter["marketCountries"] = sport_cfg["countries"]

        result = client.call(
            "listMarketCatalogue",
            {
                "filter": market_filter,
                "marketProjection": MARKET_PROJECTION,
                "maxResults": 1000,
                "sort": "FIRST_TO_START",
            },
        )
        for cat in result:
            total_matched = float(cat.get("totalMatched") or 0.0)
            if min_matched and total_matched < min_matched:
                continue
            desc = cat.get("description") or {}
            # marketBaseRate arrives as a percentage (e.g. 5.0); commission on
            # this specific market — AU racing is often higher than sports.
            mbr = desc.get("marketBaseRate")
            snapshots.append(
                MarketSnapshot(
                    market_id=cat["marketId"],
                    sport=sport,
                    market_type=desc.get("marketType", ""),
                    market_base_rate=float(mbr) / 100.0 if mbr is not None else None,
                    event_id=str((cat.get("event") or {}).get("id", "")),
                    event_name=(cat.get("event") or {}).get("name", ""),
                    competition=(cat.get("competition") or {}).get("name", ""),
                    start_time=_parse_time(cat["marketStartTime"]),
                    turn_in_play_enabled=bool(desc.get("turnInPlayEnabled", False)),
                    total_matched=total_matched,
                    runners=[
                        RunnerBook(
                            selection_id=r["selectionId"],
                            name=r.get("runnerName", ""),
                        )
                        for r in cat.get("runners", [])
                    ],
                )
            )
        log.info("Discovered %d %s markets", sum(1 for s in snapshots if s.sport == sport), sport.value)

    return snapshots
