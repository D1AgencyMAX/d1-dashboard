"""Execution: final validation and order placement (paper or live).

Every opportunity is re-validated at execution time — price refreshed, market
open, data fresh, odds still above the minimum acceptable, risk engine
approval — before a LIMIT order is placed with a unique customer order
reference. Unmatched remainders are cancelled after a timeout and the order is
reconciled before its exposure is trusted.
"""

from __future__ import annotations

import abc
import logging
import time
from datetime import datetime, timezone

from ..betfair.client import BetfairClient, BetfairError
from ..betfair.orders import (
    account_funds,
    cancel_unmatched,
    new_customer_ref,
    place_limit_order,
    reconcile_order,
)
from ..betfair.prices import refresh_prices
from ..models import BetRecord, Opportunity, RejectionReason
from ..risk.engine import RiskEngine

log = logging.getLogger(__name__)


class Executor(abc.ABC):
    def __init__(self, risk_engine: RiskEngine, customer_ref_prefix: str = "d1bot"):
        self.risk = risk_engine
        self.prefix = customer_ref_prefix
        self.placed: list[BetRecord] = []

    @abc.abstractmethod
    def refresh(self, opportunity: Opportunity) -> None:
        """Refresh executable prices for the opportunity's market."""

    @abc.abstractmethod
    def submit(self, opportunity: Opportunity, stake: float, ref: str) -> BetRecord:
        """Place the order and return the (reconciled) bet record."""

    def execute(self, ranked: list[Opportunity]) -> list[BetRecord]:
        """Run the execution loop over ranked opportunities."""
        results: list[BetRecord] = []
        for opp in ranked:
            record = self._execute_one(opp)
            if record is not None:
                results.append(record)
        return results

    def _execute_one(self, opp: Opportunity) -> BetRecord | None:
        try:
            self.refresh(opp)
        except BetfairError as exc:
            log.warning("price refresh failed for %s: %s", opp.market.market_id, exc)
            return None

        market = opp.market
        if market.status != "OPEN" or market.in_play:
            log.info("skip %s: market not open", market.market_id)
            return None

        book_age = (datetime.now(timezone.utc) - market.captured_at).total_seconds()
        if book_age > 120:
            log.info("skip %s: stale book (%.0fs)", market.market_id, book_age)
            return None

        runner = market.runner(opp.selection_id)
        if runner is None or runner.status != "ACTIVE" or not runner.back_price:
            return None
        current_odds = runner.back_price
        if current_odds < opp.minimum_acceptable_odds:
            log.info(
                "skip %s/%s: odds %.2f below minimum %.2f",
                market.market_id, opp.selection_name, current_odds, opp.minimum_acceptable_odds,
            )
            return None
        # Price protection: refuse if the price moved materially since scoring.
        drift = abs(current_odds - opp.odds) / opp.odds
        if drift > 0.05:
            log.info("skip %s/%s: price drift %.1f%%", market.market_id, opp.selection_name, drift * 100)
            return None
        if runner.back_size < min(opp.market.total_available, 1.0) and runner.back_size <= 0:
            return None

        approved, reasons = self.risk.approve(opp)
        if not approved:
            log.info("risk rejected %s/%s: %s", market.market_id, opp.selection_name,
                     [r.value for r in reasons])
            return None

        stake = self.risk.calculate_stake(opp)
        if stake <= 0:
            return None
        if runner.back_size < stake:
            log.info("skip %s/%s: only %.2f available for stake %.2f",
                     market.market_id, opp.selection_name, runner.back_size, stake)
            return None

        ref = new_customer_ref(self.prefix)
        record = self.submit(opp, stake, ref)
        self.placed.append(record)
        if record.matched_size > 0 or record.status == "PENDING":
            self.risk.commit(opp, record.matched_size or stake)
        log.info(
            "%s %s %s @ %.2f x %.2f [%s] EV=%.1f%% p=%.3f",
            record.mode.upper(), record.side.value, record.selection_name,
            record.requested_price, record.requested_size, record.status,
            opp.expected_value * 100, opp.estimate.probability,
        )
        return record


class PaperExecutor(Executor):
    """Records what would have been bet, placing nothing.

    Fills are simulated against the visible order book at the top-of-book
    price and size, which is the honest ceiling on what a live order could
    have matched instantly.
    """

    def __init__(self, risk_engine: RiskEngine, client: BetfairClient | None = None,
                 customer_ref_prefix: str = "d1bot"):
        super().__init__(risk_engine, customer_ref_prefix)
        self.client = client

    def refresh(self, opportunity: Opportunity) -> None:
        if self.client is not None:
            refresh_prices(self.client, {opportunity.market.market_id: opportunity.market})

    def submit(self, opp: Opportunity, stake: float, ref: str) -> BetRecord:
        runner = opp.market.runner(opp.selection_id)
        fill = min(stake, runner.back_size if runner else 0.0)
        return BetRecord(
            customer_order_ref=ref,
            market_id=opp.market.market_id,
            selection_id=opp.selection_id,
            selection_name=opp.selection_name,
            sport=opp.market.sport,
            event_id=opp.market.event_id,
            side=opp.side,
            requested_price=runner.back_price if runner else opp.odds,
            requested_size=stake,
            matched_price=runner.back_price if fill > 0 and runner else None,
            matched_size=round(fill, 2),
            status="MATCHED" if fill >= stake else ("PARTIAL" if fill > 0 else "LAPSED"),
            mode="paper",
            expected_value=opp.expected_value,
            model_probability=opp.estimate.probability,
        )


class LiveExecutor(Executor):
    """Places real LIMIT orders. Requires explicit env confirmation upstream."""

    def __init__(
        self,
        risk_engine: RiskEngine,
        client: BetfairClient,
        persistence_type: str = "LAPSE",
        order_timeout_seconds: float = 20.0,
        customer_ref_prefix: str = "d1bot",
    ):
        super().__init__(risk_engine, customer_ref_prefix)
        self.client = client
        self.persistence_type = persistence_type
        self.order_timeout = order_timeout_seconds

    def refresh(self, opportunity: Opportunity) -> None:
        refresh_prices(self.client, {opportunity.market.market_id: opportunity.market})

    def submit(self, opp: Opportunity, stake: float, ref: str) -> BetRecord:
        from ..betfair.ticks import nearest_tick

        runner = opp.market.runner(opp.selection_id)
        # Book prices are already on the ladder; snapping is a guard against
        # any synthesised price — an off-tick limit is rejected INVALID_ODDS.
        price = nearest_tick(runner.back_price if runner else opp.odds)
        record = BetRecord(
            customer_order_ref=ref,
            market_id=opp.market.market_id,
            selection_id=opp.selection_id,
            selection_name=opp.selection_name,
            sport=opp.market.sport,
            event_id=opp.market.event_id,
            side=opp.side,
            requested_price=price,
            requested_size=stake,
            mode="live",
            expected_value=opp.expected_value,
            model_probability=opp.estimate.probability,
        )
        try:
            report = place_limit_order(
                self.client,
                market_id=opp.market.market_id,
                selection_id=opp.selection_id,
                side=opp.side,
                price=price,
                size=stake,
                persistence_type=self.persistence_type,
                customer_order_ref=ref,
                customer_strategy_ref=self.prefix,
            )
        except BetfairError as exc:
            log.error("placeOrders failed for %s: %s", opp.market.market_id, exc)
            record.status = "CANCELLED"
            return record

        bet_id = report.get("betId")
        record.matched_size = float(report.get("sizeMatched") or 0.0)
        record.matched_price = report.get("averagePriceMatched") or None
        if record.matched_size >= stake:
            record.status = "MATCHED"
        else:
            # Wait briefly for a fill, then cancel the unmatched remainder.
            time.sleep(self.order_timeout)
            try:
                cancel_unmatched(self.client, opp.market.market_id, bet_id)
            except BetfairError as exc:
                log.error("cancelOrders failed for bet %s: %s", bet_id, exc)
            record = reconcile_order(self.client, record)

        self._verify_exposure()
        return record

    def _verify_exposure(self) -> None:
        """Compare exchange exposure with the ledger; halt on discrepancy."""
        try:
            funds = account_funds(self.client)
        except BetfairError as exc:
            log.error("getAccountFunds failed during exposure verification: %s", exc)
            self.risk.halt("cannot verify account exposure")
            return
        self.risk.verify_account(
            ledger_exposure=self.risk.total_open_exposure(),
            account_exposure=float(funds.get("exposure") or 0.0),
            tolerance=max(5.0, self.risk.cfg.bankroll * 0.01),
        )
