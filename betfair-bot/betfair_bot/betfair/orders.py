"""Order placement, cancellation and reconciliation.

All orders are LIMIT orders with a unique customer order reference for
idempotency; unmatched remainders are cancelled after a timeout and every
placement is reconciled against listCurrentOrders before exposure is trusted.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from ..models import BetRecord, Side
from .client import BetfairClient, BetfairError

log = logging.getLogger(__name__)


def new_customer_ref(prefix: str) -> str:
    # Betfair allows up to 32 chars for customerRef / customerOrderRef.
    return f"{prefix}-{uuid.uuid4().hex[:20]}"


def place_limit_order(
    client: BetfairClient,
    *,
    market_id: str,
    selection_id: int,
    side: Side,
    price: float,
    size: float,
    persistence_type: str = "LAPSE",
    customer_order_ref: str = "",
    customer_strategy_ref: str = "d1bot",
) -> dict[str, Any]:
    """Place a single LIMIT order. Returns the placeOrders instruction report.

    The customerRef doubles as an idempotency key: Betfair rejects a duplicate
    customerRef within its dedup window, so a retried request cannot place a
    second bet.
    """
    params = {
        "marketId": market_id,
        "customerRef": customer_order_ref[:32],
        "customerStrategyRef": customer_strategy_ref[:15],
        "instructions": [
            {
                "selectionId": selection_id,
                "handicap": 0,
                "side": side.value,
                "orderType": "LIMIT",
                "customerOrderRef": customer_order_ref[:32],
                "limitOrder": {
                    "size": round(size, 2),
                    "price": price,
                    "persistenceType": persistence_type,
                },
            }
        ],
    }
    result = client.call("placeOrders", params)
    report = result["instructionReports"][0]
    if result.get("status") != "SUCCESS":
        raise BetfairError(
            f"placeOrders {result.get('status')}: {report.get('errorCode')}",
            code=report.get("errorCode"),
            data=result,
        )
    return report


def cancel_unmatched(client: BetfairClient, market_id: str, bet_id: str | None = None) -> Any:
    instructions = [{"betId": bet_id}] if bet_id else []
    params: dict[str, Any] = {"marketId": market_id}
    if instructions:
        params["instructions"] = instructions
    return client.call("cancelOrders", params)


def reconcile_order(client: BetfairClient, bet: BetRecord) -> BetRecord:
    """Refresh a bet's matched state from listCurrentOrders / listClearedOrders."""
    current = client.call(
        "listCurrentOrders",
        {
            "customerOrderRefs": [bet.customer_order_ref],
            "orderProjection": "ALL",
        },
    )
    orders = current.get("currentOrders", [])
    if orders:
        order = orders[0]
        bet.matched_size = float(order.get("sizeMatched") or 0.0)
        bet.matched_price = order.get("averagePriceMatched") or None
        remaining = float(order.get("sizeRemaining") or 0.0)
        if bet.matched_size and remaining:
            bet.status = "PARTIAL"
        elif bet.matched_size:
            bet.status = "MATCHED"
        return bet

    cleared = client.call(
        "listClearedOrders",
        {
            "betStatus": "SETTLED",
            "customerOrderRefs": [bet.customer_order_ref],
        },
    )
    for co in cleared.get("clearedOrders", []):
        bet.status = "SETTLED"
        bet.matched_price = co.get("priceMatched")
        bet.matched_size = float(co.get("sizeSettled") or 0.0)
        bet.profit = float(co.get("profit") or 0.0)
        return bet

    if bet.matched_size == 0:
        bet.status = "LAPSED"
    return bet


def account_funds(client: BetfairClient) -> dict[str, Any]:
    """Account balance/exposure, used to verify the ledger after each order.

    The Accounts API lives on a sibling endpoint to the betting one.
    """
    endpoint = client.cfg.endpoint.replace("/exchange/betting/", "/exchange/account/")
    client.ensure_session()
    resp = client._http.post(
        endpoint,
        json={
            "jsonrpc": "2.0",
            "method": "AccountAPING/v1.0/getAccountFunds",
            "params": {},
            "id": 1,
        },
        headers={
            "X-Application": client.cfg.app_key,
            "X-Authentication": client._session_token or "",
            "Content-Type": "application/json",
        },
        timeout=20,
    )
    resp.raise_for_status()
    body = resp.json()
    if "error" in body:
        raise BetfairError(f"getAccountFunds failed: {body['error']}")
    return body["result"]
