"""Automated daily performance report."""

from __future__ import annotations

from ..storage.db import Store


def build_report(store: Store, day_iso: str) -> str:
    bets = store.bets_for_day(day_iso)
    counts = store.opportunity_counts_for_day(day_iso)

    total_staked = sum(b["matched_size"] or 0.0 for b in bets)
    settled = [b for b in bets if b["profit"] is not None]
    pnl = sum(b["profit"] for b in settled)
    with_clv = [
        b for b in bets
        if b["closing_price"] and b["matched_price"] and b["closing_price"] > 1.0
    ]
    # Closing-line value: taken price vs closing implied probability.
    clv = (
        sum(b["matched_price"] / b["closing_price"] - 1.0 for b in with_clv) / len(with_clv)
        if with_clv
        else None
    )

    lines = [
        f"Daily report — {day_iso}",
        "=" * 40,
        f"Opportunities qualified:  {counts.get('QUALIFIED', 0)}",
        f"Opportunities rejected:   {counts.get('REJECTED', 0)}",
        f"Bets placed:              {len(bets)}",
        f"Total matched stake:      {total_staked:.2f}",
        f"Settled bets:             {len(settled)}",
        f"Realised P&L:             {pnl:+.2f}" if settled else "Realised P&L:             (none settled)",
    ]
    if clv is not None:
        lines.append(f"Avg closing-line value:   {clv:+.2%} ({len(with_clv)} bets)")
    if not bets:
        lines.append("")
        lines.append("No qualifying bets today — this is a valid outcome.")
    return "\n".join(lines)
