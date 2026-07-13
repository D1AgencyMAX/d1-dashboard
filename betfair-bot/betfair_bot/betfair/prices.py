"""Price and order-book retrieval via listMarketBook, weight-batched."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from ..models import MarketSnapshot, PriceSize
from .client import BetfairClient

log = logging.getLogger(__name__)

PRICE_DATA = ["EX_BEST_OFFERS", "EX_TRADED"]


def refresh_prices(client: BetfairClient, markets: dict[str, MarketSnapshot]) -> None:
    """Attach current back/lay prices, traded volume and status to snapshots.

    Batches market ids so each listMarketBook call stays under Betfair's
    aggregate request-weight cap.
    """
    market_ids = list(markets)
    batch = client.market_book_batch_size(PRICE_DATA)
    now = datetime.now(timezone.utc)

    for chunk in client.chunked(market_ids, batch):
        books = client.call(
            "listMarketBook",
            {
                "marketIds": chunk,
                "priceProjection": {
                    "priceData": PRICE_DATA,
                    "virtualise": True,
                },
            },
        )
        for book in books:
            snap = markets.get(book["marketId"])
            if snap is None:
                continue
            snap.status = book.get("status", "OPEN")
            snap.in_play = bool(book.get("inplay", False))
            snap.total_matched = float(book.get("totalMatched") or 0.0)
            snap.total_available = float(book.get("totalAvailable") or 0.0)
            snap.captured_at = now
            by_id = {r.selection_id: r for r in snap.runners}
            for rb in book.get("runners", []):
                runner = by_id.get(rb["selectionId"])
                if runner is None:
                    continue
                runner.status = rb.get("status", "ACTIVE")
                runner.last_price_traded = rb.get("lastPriceTraded")
                runner.total_matched = float(rb.get("totalMatched") or 0.0)
                ex = rb.get("ex") or {}
                runner.best_back = [
                    PriceSize(p["price"], p["size"]) for p in ex.get("availableToBack", [])
                ]
                runner.best_lay = [
                    PriceSize(p["price"], p["size"]) for p in ex.get("availableToLay", [])
                ]
