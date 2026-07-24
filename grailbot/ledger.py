"""Immutable paper-trading ledger + broker — Project Atlas Priority #1.

Design goals (from the Atlas master plan):
  * Immutable & accounting-grade: entries are append-only and hash-chained, so
    any tampering with history is detectable (verify_chain()).
  * Paper broker: opens simulated positions at a disciplined max-bid, never
    overpaying, and only on *recommended* opportunities.
  * Portfolio ledger: records fair value, max bid, expected hold, exit, fees and
    realized P&L per lot — the record that proves whether the model has an edge.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional

from grailbot.config import Settings
from grailbot.models import Opportunity

GENESIS = "0" * 64


@dataclass(frozen=True)
class LedgerEntry:
    seq: int
    ts: str
    etype: str            # DEPOSIT | OPEN | CLOSE
    card_key: str
    title: str
    cash_delta: float     # signed effect on cash
    price: float          # entry or exit price for the lot
    fair_value: float
    max_bid: float
    hold_days: int
    fees: float
    pnl: float            # realized on CLOSE, else 0
    note: str
    prev_hash: str
    hash: str = ""

    def digest(self) -> str:
        body = {k: v for k, v in asdict(self).items() if k != "hash"}
        return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


@dataclass
class Lot:
    lot_id: int
    card_key: str
    title: str
    entry_price: float
    fair_value: float
    hold_days: int


class PaperBroker:
    def __init__(self, settings: Settings, starting_cash: float = 25_000.0):
        self.s = settings
        self.entries: list[LedgerEntry] = []
        self.open_lots: list[Lot] = []
        self.cash = 0.0
        self._seq = 0
        self.deposit(starting_cash, note="initial bankroll")

    # -- immutable append -------------------------------------------------
    def _append(self, **kw) -> LedgerEntry:
        self._seq += 1
        prev = self.entries[-1].hash if self.entries else GENESIS
        e = LedgerEntry(
            seq=self._seq,
            ts=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            prev_hash=prev,
            **kw,
        )
        object.__setattr__(e, "hash", e.digest())   # frozen -> set once
        self.entries.append(e)
        self.cash = round(self.cash + e.cash_delta, 2)
        return e

    def _blank(self, **kw):
        base = dict(card_key="", title="", price=0.0, fair_value=0.0, max_bid=0.0,
                    hold_days=0, fees=0.0, pnl=0.0, note="")
        base.update(kw)
        return base

    # -- operations -------------------------------------------------------
    def deposit(self, amount: float, note: str = "") -> LedgerEntry:
        return self._append(etype="DEPOSIT", cash_delta=round(amount, 2),
                            **self._blank(note=note))

    def max_bid(self, fair_value: float) -> float:
        """Highest price that still clears the minimum edge after fees+ship."""
        return round(fair_value * (1 - self.s.fee_rate) - self.s.ship_out
                     - self.s.min_net_edge, 2)

    def _hold_days(self, comp) -> int:
        v = comp.velocity or comp.n
        return 30 if v >= 8 else 60 if v >= 3 else 90

    def open(self, opp: Opportunity) -> Optional[Lot]:
        if not opp.recommended:
            return None
        fair = opp.comp.median_sold
        mb = self.max_bid(fair)
        landed = opp.resolved.listing.landed
        if landed > mb:                 # discipline: never overpay
            return None
        if landed > self.cash:          # bankroll limit
            return None
        e = self._append(
            etype="OPEN", card_key=opp.resolved.card.key(), title=opp.title,
            cash_delta=-landed, price=landed, fair_value=fair, max_bid=mb,
            hold_days=self._hold_days(opp.comp), fees=0.0, pnl=0.0,
            note=f"buy @ {landed:.2f} (max_bid {mb:.2f})",
        )
        lot = Lot(e.seq, e.card_key, e.title, landed, fair, e.hold_days)
        self.open_lots.append(lot)
        return lot

    def close(self, lot: Lot, exit_price: float) -> LedgerEntry:
        fee = round(exit_price * self.s.fee_rate, 2)
        proceeds = round(exit_price * (1 - self.s.fee_rate) - self.s.ship_out, 2)
        pnl = round(proceeds - lot.entry_price, 2)
        self.open_lots.remove(lot)
        return self._append(
            etype="CLOSE", card_key=lot.card_key, title=lot.title,
            cash_delta=proceeds, price=exit_price, fair_value=lot.fair_value,
            max_bid=0.0, hold_days=lot.hold_days, fees=fee, pnl=pnl,
            note=f"sell @ {exit_price:.2f}",
        )

    # -- reporting / integrity -------------------------------------------
    def verify_chain(self) -> bool:
        prev = GENESIS
        for e in self.entries:
            if e.prev_hash != prev or e.hash != e.digest():
                return False
            prev = e.hash
        return True

    def summary(self) -> dict:
        closes = [e for e in self.entries if e.etype == "CLOSE"]
        opens = [e for e in self.entries if e.etype == "OPEN"]
        invested = round(sum(-e.cash_delta for e in opens), 2)
        realized = round(sum(e.pnl for e in closes), 2)
        wins = sum(1 for e in closes if e.pnl > 0)
        return {
            "cash": round(self.cash, 2),
            "positions_opened": len(opens),
            "positions_closed": len(closes),
            "open_lots": len(self.open_lots),
            "invested": invested,
            "realized_pnl": realized,
            "realized_roi": round(realized / invested, 3) if invested else 0.0,
            "win_rate": round(wins / len(closes), 3) if closes else 0.0,
            "chain_valid": self.verify_chain(),
        }
