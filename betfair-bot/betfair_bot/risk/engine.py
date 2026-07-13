"""Risk engine: exposure ledger, stop-losses and final bet approval.

Tracks open exposure per event, sport and day against a fixed, separate
bankroll. Any breach — including an unexplained discrepancy between the
ledger and the account — halts new bets immediately.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

from ..config import RiskConfig
from ..models import Opportunity, RejectionReason
from .kelly import stake as kelly_stake

log = logging.getLogger(__name__)


@dataclass
class ExposureLedger:
    """Open exposure and realised P&L, keyed by event/sport/day."""

    by_event: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    by_sport: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    new_exposure_by_day: dict[date, float] = field(default_factory=lambda: defaultdict(float))
    pnl_by_day: dict[date, float] = field(default_factory=lambda: defaultdict(float))

    def add_exposure(self, event_id: str, sport: str, amount: float, day: date) -> None:
        self.by_event[event_id] += amount
        self.by_sport[sport] += amount
        self.new_exposure_by_day[day] += amount

    def settle(self, event_id: str, sport: str, staked: float, profit: float, day: date) -> None:
        self.by_event[event_id] = max(0.0, self.by_event[event_id] - staked)
        self.by_sport[sport] = max(0.0, self.by_sport[sport] - staked)
        self.pnl_by_day[day] += profit

    def daily_pnl(self, day: date) -> float:
        return self.pnl_by_day.get(day, 0.0)

    def weekly_pnl(self, day: date) -> float:
        return sum(self.pnl_by_day.get(day - timedelta(days=i), 0.0) for i in range(7))


class RiskEngine:
    def __init__(self, cfg: RiskConfig, ledger: ExposureLedger | None = None):
        self.cfg = cfg
        self.ledger = ledger or ExposureLedger()
        self.halted: bool = False
        self.halt_reason: str = ""

    def halt(self, reason: str) -> None:
        """Manual/automatic kill switch; no new bets until explicitly reset."""
        self.halted = True
        self.halt_reason = reason
        log.critical("RISK ENGINE HALTED: %s", reason)

    def reset_halt(self) -> None:
        self.halted = False
        self.halt_reason = ""

    def _today(self, now: datetime | None) -> date:
        return (now or datetime.now(timezone.utc)).date()

    def approve(
        self, opportunity: Opportunity, now: datetime | None = None
    ) -> tuple[bool, list[RejectionReason]]:
        """Check stop-losses and exposure caps for one candidate bet."""
        day = self._today(now)
        cfg = self.cfg
        reasons: list[RejectionReason] = []

        if self.halted:
            reasons.append(RejectionReason.API_UNHEALTHY)
            return False, reasons

        if self.ledger.daily_pnl(day) <= -cfg.daily_stop_loss_pct * cfg.bankroll:
            reasons.append(RejectionReason.DAILY_LOSS_LIMIT)
        if self.ledger.weekly_pnl(day) <= -cfg.weekly_stop_loss_pct * cfg.bankroll:
            reasons.append(RejectionReason.WEEKLY_LOSS_LIMIT)

        event_id = opportunity.market.event_id
        sport = opportunity.market.sport.value
        proposed = self.calculate_stake(opportunity)
        if proposed <= 0:
            reasons.append(RejectionReason.EV_TOO_LOW)
            return False, reasons

        if self.ledger.by_event[event_id] + proposed > cfg.maximum_event_exposure_pct * cfg.bankroll:
            reasons.append(RejectionReason.CORRELATED_EXPOSURE)
        if self.ledger.by_sport[sport] + proposed > cfg.maximum_sport_exposure_pct * cfg.bankroll:
            reasons.append(RejectionReason.EXPOSURE_CAP)
        if (
            self.ledger.new_exposure_by_day[day] + proposed
            > cfg.maximum_daily_new_exposure_pct * cfg.bankroll
        ):
            reasons.append(RejectionReason.EXPOSURE_CAP)

        return (not reasons), reasons

    def calculate_stake(self, opportunity: Opportunity) -> float:
        return kelly_stake(
            opportunity.estimate.probability,
            opportunity.odds,
            opportunity.commission_rate,
            self.cfg.bankroll,
            fraction=self.cfg.kelly_fraction,
            max_stake_pct=self.cfg.maximum_stake_bankroll_pct,
            min_stake=self.cfg.min_stake,
        )

    def commit(self, opportunity: Opportunity, staked: float, now: datetime | None = None) -> None:
        self.ledger.add_exposure(
            opportunity.market.event_id,
            opportunity.market.sport.value,
            staked,
            self._today(now),
        )

    def verify_account(self, ledger_exposure: float, account_exposure: float, tolerance: float = 1.0) -> None:
        """Compare our ledger with the exchange's reported exposure.

        An unexplained discrepancy is grounds for immediate shutdown — it
        means either a reconciliation bug or activity we did not initiate.
        """
        if abs(ledger_exposure - abs(account_exposure)) > tolerance:
            self.halt(
                f"account discrepancy: ledger={ledger_exposure:.2f} "
                f"account={account_exposure:.2f}"
            )

    def total_open_exposure(self) -> float:
        return sum(self.ledger.by_event.values())
