# Architecture

GrailBot is the reference engine for **Project Atlas** — an intelligence layer
for inefficient collectible markets. It is a pipeline of small, swappable stages.

## Data flow
```
 listings              Card              sold comps           Opportunity        ledger
 (eBay Browse)  ─▶  Resolver  ─▶  (price vendor)  ─▶  Scoring  ─▶  Pipeline  ─▶  PaperBroker
   sources.py      resolver.py       sources.py        scoring.py    pipeline.py    ledger.py
                        │                                                              │
                    catalog.py                                                     storage.py
```

## Modules → Atlas layers
| Module | Atlas layer | Responsibility |
|---|---|---|
| `resolver.py`, `catalog.py` | Card Identity | Title → `{player, product, parallel, serial, grade}` + confidence |
| `sources.py` | Market Data | `ListingSource` (eBay) and `CompSource` (price vendor) adapters |
| `scoring.py` | Valuation + Strategy + Risk | Net-of-fees edge, 0–100 score, guardrails |
| `pipeline.py` | Orchestration | Wires the stages, ranks opportunities |
| `ledger.py` | Paper Broker + Portfolio Ledger | Immutable, hash-chained paper trading |
| `storage.py` | Persistence | SQLite (append-only ledger, snapshots, watch) |
| `cli.py` | Analyst Terminal | `scan`, `papertrade` |

## Core types (`models.py`)
`Card` (identity, `.key()` for comp lookup) · `Listing` · `Comp` (sold stats) ·
`Resolved` (card + confidence + flags) · `Opportunity` (edge + score + reasons).

## Guardrails (why this is safe, not just clever)
1. **Sold comps only** — asking prices are systematically inflated; both of our
   pilot "deals" evaporated when valued against realized sales.
2. **Confidence gate** — the resolver scores its own certainty; below
   `MIN_IDENTITY_CONFIDENCE` the engine refuses to recommend. This blocks the
   classic trap where one color word maps to a $170 card in one product and an
   $850 card in another.
3. **Value floor** — base cards are too cheap to clear ~13% fees; skipped.
4. **Max-bid discipline** — the paper broker never pays above the price that
   still clears the minimum edge.
5. **Immutable ledger** — entries are append-only and hash-chained;
   `verify_chain()` detects any tampering.

## Extending it
- **New price vendor**: implement `CompSource.get_comp(card) -> Comp | None` in
  `sources.py`; wire it in `build_sources()`.
- **New marketplace / country**: add a `ListingSource`; model landed cost + forex.
- **New asset class**: `Card` is asset-agnostic (`sport`/`product` are free-form);
  add a catalog and go.
- **New signal**: add a 0..1 component in `scoring.score_opportunity` with a weight.

## Modes
`GRAILBOT_MODE=mock` (default) runs on bundled sample data, stdlib-only, no keys.
`GRAILBOT_MODE=live` activates the real adapters once `.env` has your keys.
