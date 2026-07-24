"""Local persistence (SQLite, stdlib). Price history + opportunities + watch tags.

Zero-setup default. A dedicated Supabase repo can implement the same surface in
a later phase (isolated project — never Ganymede).
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Optional

from grailbot.models import Opportunity

_SCHEMA = """
CREATE TABLE IF NOT EXISTS price_snapshots (
  id INTEGER PRIMARY KEY,
  card_key TEXT NOT NULL,
  median_sold REAL, n INTEGER, low REAL, high REAL,
  source TEXT, captured_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_snap_card ON price_snapshots(card_key);

CREATE TABLE IF NOT EXISTS opportunities (
  id INTEGER PRIMARY KEY,
  listing_id TEXT, title TEXT, card_key TEXT,
  landed REAL, comp_median REAL, net_edge REAL, roi REAL,
  score REAL, recommended INTEGER, confidence REAL,
  flags TEXT, reasons TEXT, seen_at TEXT
);

CREATE TABLE IF NOT EXISTS watch (
  card_key TEXT PRIMARY KEY,
  tag TEXT, target REAL, note TEXT, updated_at TEXT
);

-- append-only, hash-chained paper-trading ledger (Atlas Priority #1)
CREATE TABLE IF NOT EXISTS ledger (
  seq INTEGER PRIMARY KEY, ts TEXT, etype TEXT, card_key TEXT, title TEXT,
  cash_delta REAL, price REAL, fair_value REAL, max_bid REAL, hold_days INTEGER,
  fees REAL, pnl REAL, note TEXT, prev_hash TEXT, hash TEXT
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, path: str = "grailbot.db"):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(_SCHEMA)
        self.db.commit()

    def save_snapshot(self, comp) -> None:
        self.db.execute(
            "INSERT INTO price_snapshots(card_key,median_sold,n,low,high,source,captured_at)"
            " VALUES(?,?,?,?,?,?,?)",
            (comp.card_key, comp.median_sold, comp.n, comp.low, comp.high, comp.source, _now()),
        )
        self.db.commit()

    def save_opportunity(self, o: Opportunity) -> None:
        c = o.resolved.card
        self.db.execute(
            "INSERT INTO opportunities(listing_id,title,card_key,landed,comp_median,"
            "net_edge,roi,score,recommended,confidence,flags,reasons,seen_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (o.resolved.listing.listing_id, o.title, c.key(), o.resolved.listing.landed,
             o.comp.median_sold, o.net_edge, o.roi, o.score, int(o.recommended),
             o.resolved.confidence, ",".join(o.resolved.flags), " | ".join(o.reasons), _now()),
        )
        self.db.commit()

    def save_ledger_entry(self, e) -> None:
        self.db.execute(
            "INSERT OR IGNORE INTO ledger(seq,ts,etype,card_key,title,cash_delta,"
            "price,fair_value,max_bid,hold_days,fees,pnl,note,prev_hash,hash)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (e.seq, e.ts, e.etype, e.card_key, e.title, e.cash_delta, e.price,
             e.fair_value, e.max_bid, e.hold_days, e.fees, e.pnl, e.note,
             e.prev_hash, e.hash),
        )
        self.db.commit()

    def set_tag(self, card_key: str, tag: str, target: Optional[float] = None,
                note: str = "") -> None:
        self.db.execute(
            "INSERT INTO watch(card_key,tag,target,note,updated_at) VALUES(?,?,?,?,?)"
            " ON CONFLICT(card_key) DO UPDATE SET tag=excluded.tag,target=excluded.target,"
            "note=excluded.note,updated_at=excluded.updated_at",
            (card_key, tag, target, note, _now()),
        )
        self.db.commit()

    def close(self) -> None:
        self.db.close()
