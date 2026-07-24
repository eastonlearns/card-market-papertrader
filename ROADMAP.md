# Roadmap

GrailBot is a working slice of the **Project Atlas** vision (a "Bloomberg
Terminal for collectibles"). Phases map to Atlas's stated priorities.

### ✅ Done
- Card-identity resolver + confidence gating
- Valuation + 0–100 scoring with risk guardrails
- Mock + live-skeleton data adapters
- **Immutable, hash-chained paper-trading ledger** (Atlas Priority #1)
- CLI (`scan`, `papertrade`), SQLite storage, test suite

### 🔜 Next
- **Walk-forward simulator** (Atlas #4) — backtest strategies over historical
  comps on top of the ledger; report out-of-sample edge.
- **Real data ingestion** (Atlas #3) — implement a live `CompSource` (SportsCardsPro
  / Card Hedge); schedule daily pulls into `price_snapshots`.
- **Evidence engine** (Atlas #6) — formalize the per-recommendation `reasons`
  into an auditable explanation record.

### 🌅 Later
- Multi-marketplace + country arbitrage (eBay `.co.uk`/`.de`/`.es`, landed cost, forex)
- MCP / FastAPI surface so agents and apps can query opportunities
- Experiment registry (Atlas #7) and research corpus (Atlas #8)
- Multi-asset expansion: Pokémon, sealed wax, comics, watches, sneakers, coins

### Non-negotiables carried through every phase
Sold comps not asks · identity-confidence gate · skip base cards · paper-trade
before real capital · the repo is the source of truth.
