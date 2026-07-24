#!/usr/bin/env python3
"""MCP server for GrailBot — talk to the card value-gap engine from any MCP client.

Exposes the engine as four tools an LLM can call in natural language:
  * grailbot_resolve_card     — title -> exact card identity + confidence
  * grailbot_value_card       — is this listing a deal vs sold comps?
  * grailbot_scan_opportunities — rank opportunities from listings
  * grailbot_paper_trade      — simulate a bankroll against the immutable ledger

Runs in mock mode with zero keys, so any client can connect and try it instantly.
Run:  python -m grailbot.mcp_server   (stdio transport)

The tool *logic* lives in plain `_*_data` functions (importable/testable without
the MCP SDK); the `@mcp.tool` wrappers just serialize their output.
"""
from __future__ import annotations

import json
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from mcp.server.fastmcp import FastMCP

from grailbot.catalog import Catalog
from grailbot.config import Settings
from grailbot.ledger import PaperBroker
from grailbot.models import Comp, Listing, Opportunity
from grailbot.pipeline import Pipeline
from grailbot.resolver import Resolver
from grailbot.scoring import score_opportunity
from grailbot.sources import build_sources

mcp = FastMCP("grailbot_mcp")

# Shared engine singletons (cheap, stateless).
_SETTINGS = Settings.load()
_CATALOG = Catalog.load()
_RESOLVER = Resolver(_CATALOG)
_CATALYST = {p.name.lower(): p.catalyst for p in _CATALOG.players}

_READONLY = {"readOnlyHint": True, "destructiveHint": False,
             "idempotentHint": True, "openWorldHint": True}


# --------------------------------------------------------------------------
# Pure logic (no MCP dependency) — this is what the unit tests exercise.
# --------------------------------------------------------------------------
def _opp_to_dict(o: Opportunity) -> dict:
    c = o.resolved.card
    return {
        "title": o.title,
        "recommended": o.recommended,
        "score": o.score,
        "net_edge": o.net_edge,
        "roi": o.roi,
        "confidence": o.resolved.confidence,
        "card": {"player": c.player, "product": c.product, "parallel": c.parallel,
                 "serial_to": c.serial_to, "grade": c.grade, "card_key": c.key()},
        "comp": {"median_sold": o.comp.median_sold, "n": o.comp.n,
                 "psa10_median": o.comp.psa10_median},
        "flags": o.resolved.flags,
        "reasons": o.reasons,
    }


def resolve_card_data(title: str) -> dict:
    r = _RESOLVER.resolve(Listing(listing_id="q", title=title, price=0.0))
    c = r.card
    return {
        "player": c.player, "sport": c.sport, "year": c.year, "product": c.product,
        "card_no": c.card_no, "parallel": c.parallel, "serial_to": c.serial_to,
        "grade": c.grade, "confidence": r.confidence, "flags": r.flags,
        "card_key": c.key(),
        "identified": r.confidence >= _SETTINGS.min_identity_confidence,
    }


def value_card_data(title: str, price: float, shipping: float = 0.0) -> dict:
    listing = Listing(listing_id="q", title=title, price=price, shipping=shipping)
    resolved = _RESOLVER.resolve(listing)
    comp_source = build_sources(_SETTINGS)[1]
    comp = comp_source.get_comp(resolved.card)
    if comp is None:
        return {"title": title, "valued": False,
                "reason": "No sold comps found for this card — cannot value.",
                "confidence": resolved.confidence, "flags": resolved.flags,
                "card_key": resolved.card.key()}
    catalyst = _CATALYST.get(resolved.card.player.lower(), 0.5)
    opp = score_opportunity(resolved, comp, catalyst, _SETTINGS)
    out = _opp_to_dict(opp)
    out["valued"] = True
    return out


def scan_data(query: str = "", limit: int = 25, recommended_only: bool = True) -> dict:
    opps = Pipeline(_SETTINGS).run(query=query, limit=limit)
    rows = [o for o in opps if o.recommended or not recommended_only]
    return {
        "mode": _SETTINGS.mode,
        "scanned": len(opps),
        "recommended": sum(o.recommended for o in opps),
        "returned": len(rows),
        "opportunities": [_opp_to_dict(o) for o in rows],
    }


def paper_trade_data(bankroll: float = 25000.0) -> dict:
    broker = PaperBroker(_SETTINGS, starting_cash=bankroll)
    for o in Pipeline(_SETTINGS).run():
        broker.open(o)
    if _SETTINGS.mode == "mock":
        from grailbot import sample_data
        for lot in list(broker.open_lots):
            if lot.card_key in sample_data.SAMPLE_EXITS:
                broker.close(lot, sample_data.SAMPLE_EXITS[lot.card_key])
    s = broker.summary()
    s["ledger"] = [
        {"seq": e.seq, "type": e.etype, "title": e.title, "price": e.price,
         "pnl": e.pnl, "cash_delta": e.cash_delta}
        for e in broker.entries
    ]
    return s


# --------------------------------------------------------------------------
# Input models
# --------------------------------------------------------------------------
class TitleInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    title: str = Field(..., min_length=3, max_length=300,
                       description="A card listing title, e.g. '2024 Donruss Optic Jayden Daniels Blue Glitter #248'")


class ValueInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    title: str = Field(..., min_length=3, max_length=300, description="The card listing title")
    price: float = Field(..., ge=0, description="Listing/ask price in USD")
    shipping: float = Field(default=0.0, ge=0, description="Shipping cost in USD (default 0)")


class ScanInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    query: str = Field(default="", max_length=100, description="Optional text filter over listings")
    limit: int = Field(default=25, ge=1, le=200, description="Max listings to scan")
    recommended_only: bool = Field(default=True, description="Return only recommended opportunities")


class PaperTradeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bankroll: float = Field(default=25000.0, ge=1.0, description="Simulated starting bankroll in USD")


# --------------------------------------------------------------------------
# Tools
# --------------------------------------------------------------------------
@mcp.tool(name="grailbot_resolve_card",
          annotations={"title": "Resolve card identity", **_READONLY})
def grailbot_resolve_card(params: TitleInput) -> str:
    """Resolve a messy listing title into an exact card identity with a confidence score.

    Returns JSON: {player, sport, year, product, card_no, parallel, serial_to, grade,
    confidence (0-1), flags (e.g. NAME_MISSPELLED, CROSS_PRODUCT_COLOR), card_key,
    identified (bool)}. Low confidence means the engine refuses to trust the ID —
    do not act on it.
    """
    return json.dumps(resolve_card_data(params.title), indent=2)


@mcp.tool(name="grailbot_value_card",
          annotations={"title": "Value a card vs sold comps", **_READONLY})
def grailbot_value_card(params: ValueInput) -> str:
    """Decide whether a listing is a deal by valuing it against SOLD comps (not asks).

    Returns JSON with net-of-fees edge, ROI, 0-100 score, the sold-comp stats, and
    `recommended` plus human-readable `reasons`. If the card can't be identified or
    has no comps, returns `valued: false` with the reason.
    """
    return json.dumps(value_card_data(params.title, params.price, params.shipping), indent=2)


@mcp.tool(name="grailbot_scan_opportunities",
          annotations={"title": "Scan and rank opportunities", **_READONLY})
def grailbot_scan_opportunities(params: ScanInput) -> str:
    """Scan available listings and rank value-gap opportunities.

    Returns JSON: {mode, scanned, recommended, returned, opportunities:[...]}. Each
    opportunity includes score, net_edge, comp stats, confidence, flags and reasons.
    In mock mode this runs on bundled sample data with no keys.
    """
    return json.dumps(scan_data(params.query, params.limit, params.recommended_only), indent=2)


@mcp.tool(name="grailbot_paper_trade",
          annotations={"title": "Run a paper-trading session", **_READONLY})
def grailbot_paper_trade(params: PaperTradeInput) -> str:
    """Simulate buying the recommended cards on a bankroll and report realized P&L.

    Opens only recommended cards at a disciplined max-bid, records them in the
    immutable hash-chained ledger, simulates exits, and returns JSON with invested,
    realized_pnl, roi, win_rate, chain_valid, and the full ledger of entries.
    """
    return json.dumps(paper_trade_data(params.bankroll), indent=2)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
