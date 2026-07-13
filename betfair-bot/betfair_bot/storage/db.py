"""SQLite persistence: markets, price snapshots, facts, estimates, bets, audit.

SQLite keeps the bootstrap dependency-free; the schema maps 1:1 onto the
production PostgreSQL/TimescaleDB layout so migration is mechanical.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from ..models import BetRecord, Fact, MarketSnapshot, Opportunity

SCHEMA = """
CREATE TABLE IF NOT EXISTS markets (
    market_id TEXT PRIMARY KEY,
    sport TEXT NOT NULL,
    market_type TEXT NOT NULL,
    event_id TEXT,
    event_name TEXT,
    competition TEXT,
    start_time TEXT NOT NULL,
    turn_in_play_enabled INTEGER DEFAULT 0,
    discovered_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS price_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id TEXT NOT NULL,
    selection_id INTEGER NOT NULL,
    captured_at TEXT NOT NULL,
    back_price REAL, back_size REAL,
    lay_price REAL, lay_size REAL,
    last_traded REAL,
    total_matched REAL,
    status TEXT
);
CREATE INDEX IF NOT EXISTS idx_snap_market ON price_snapshots (market_id, captured_at);

CREATE TABLE IF NOT EXISTS facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT, event_id TEXT, fact_type TEXT,
    value TEXT, subject TEXT,
    published_at TEXT, collected_at TEXT,
    source_reliability REAL, confidence REAL,
    official INTEGER DEFAULT 0,
    claim_key TEXT
);
CREATE INDEX IF NOT EXISTS idx_facts_event ON facts (event_id, fact_type);

CREATE TABLE IF NOT EXISTS estimates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id TEXT, selection_id INTEGER,
    probability REAL, lower_bound REAL, upper_bound REAL,
    confidence REAL, disagreement REAL, sample_size INTEGER,
    components TEXT,
    computed_at TEXT
);

CREATE TABLE IF NOT EXISTS opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id TEXT, selection_id INTEGER, selection_name TEXT,
    odds REAL, expected_value REAL, score REAL,
    score_breakdown TEXT,
    decision TEXT, rejection_reasons TEXT,
    scored_at TEXT
);

CREATE TABLE IF NOT EXISTS bets (
    customer_order_ref TEXT PRIMARY KEY,
    market_id TEXT, selection_id INTEGER, selection_name TEXT,
    sport TEXT, event_id TEXT, side TEXT,
    requested_price REAL, requested_size REAL,
    matched_price REAL, matched_size REAL,
    status TEXT, mode TEXT,
    expected_value REAL, model_probability REAL,
    closing_price REAL, profit REAL,
    placed_at TEXT, settled_at TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    at TEXT NOT NULL,
    kind TEXT NOT NULL,
    detail TEXT
);
"""


class Store:
    def __init__(self, path: str | Path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # ------------------------------------------------------------- writers

    def save_market(self, snap: MarketSnapshot) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO markets
               (market_id, sport, market_type, event_id, event_name, competition,
                start_time, turn_in_play_enabled, discovered_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                snap.market_id, snap.sport.value, snap.market_type, snap.event_id,
                snap.event_name, snap.competition, snap.start_time.isoformat(),
                int(snap.turn_in_play_enabled), datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def save_price_snapshot(self, snap: MarketSnapshot) -> None:
        rows = [
            (
                snap.market_id, r.selection_id, snap.captured_at.isoformat(),
                r.back_price, r.back_size, r.lay_price,
                r.best_lay[0].size if r.best_lay else None,
                r.last_price_traded, r.total_matched, r.status,
            )
            for r in snap.runners
        ]
        self.conn.executemany(
            """INSERT INTO price_snapshots
               (market_id, selection_id, captured_at, back_price, back_size,
                lay_price, lay_size, last_traded, total_matched, status)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            rows,
        )
        self.conn.commit()

    def save_fact(self, fact: Fact) -> None:
        self.conn.execute(
            """INSERT INTO facts
               (source, event_id, fact_type, value, subject, published_at,
                collected_at, source_reliability, confidence, official, claim_key)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                fact.source, fact.event_id, fact.fact_type, json.dumps(fact.value),
                fact.subject, fact.published_at.isoformat(), fact.collected_at.isoformat(),
                fact.source_reliability, fact.confidence, int(fact.official), fact.claim_key,
            ),
        )
        self.conn.commit()

    def save_opportunity(self, opp: Opportunity, decision: str, reasons: list[str]) -> None:
        self.conn.execute(
            """INSERT INTO opportunities
               (market_id, selection_id, selection_name, odds, expected_value,
                score, score_breakdown, decision, rejection_reasons, scored_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                opp.market.market_id, opp.selection_id, opp.selection_name,
                opp.odds, opp.expected_value, opp.score,
                json.dumps(opp.score_breakdown), decision, json.dumps(reasons),
                opp.scored_at.isoformat(),
            ),
        )
        self.conn.commit()

    def save_bet(self, bet: BetRecord) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO bets
               (customer_order_ref, market_id, selection_id, selection_name, sport,
                event_id, side, requested_price, requested_size, matched_price,
                matched_size, status, mode, expected_value, model_probability,
                closing_price, profit, placed_at, settled_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                bet.customer_order_ref, bet.market_id, bet.selection_id,
                bet.selection_name, bet.sport.value, bet.event_id, bet.side.value,
                bet.requested_price, bet.requested_size, bet.matched_price,
                bet.matched_size, bet.status, bet.mode, bet.expected_value,
                bet.model_probability, bet.closing_price, bet.profit,
                bet.placed_at.isoformat(),
                bet.settled_at.isoformat() if bet.settled_at else None,
            ),
        )
        self.conn.commit()

    def audit(self, kind: str, detail: str) -> None:
        self.conn.execute(
            "INSERT INTO audit_log (at, kind, detail) VALUES (?,?,?)",
            (datetime.now(timezone.utc).isoformat(), kind, detail),
        )
        self.conn.commit()

    # ------------------------------------------------------------- readers

    def bets_for_day(self, day_iso: str) -> list[sqlite3.Row]:
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.execute(
            "SELECT * FROM bets WHERE placed_at LIKE ? ORDER BY placed_at",
            (f"{day_iso}%",),
        )
        return cur.fetchall()

    def opportunity_counts_for_day(self, day_iso: str) -> dict[str, int]:
        cur = self.conn.execute(
            "SELECT decision, COUNT(*) FROM opportunities WHERE scored_at LIKE ? GROUP BY decision",
            (f"{day_iso}%",),
        )
        return {row[0]: row[1] for row in cur.fetchall()}

    def price_history(self, market_id: str, selection_id: int) -> list[tuple[datetime, float]]:
        """(time, implied probability) series for already-priced analysis."""
        cur = self.conn.execute(
            """SELECT captured_at, back_price FROM price_snapshots
               WHERE market_id=? AND selection_id=? AND back_price IS NOT NULL
               ORDER BY captured_at""",
            (market_id, selection_id),
        )
        return [
            (datetime.fromisoformat(ts), 1.0 / price)
            for ts, price in cur.fetchall()
            if price and price > 1.0
        ]
