# Contributing to GrailBot

GrailBot is an open, loosely-coupled engine for finding value gaps in collectible
card markets. It's built to be extended — new data sources, new asset classes,
new signals — so contributions of all sizes are welcome.

## Ground rules
- Be kind and constructive (see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)).
- Keep the core dependency-free: mock mode must run on the Python standard
  library alone. Third-party libs belong behind the `live`/`dev` extras.
- **Price off sold comps, never asking prices.** This is a first principle.
- **Never let the resolver guess.** If identity confidence is low, flag it and
  refuse to value — do not invent a price.

## Dev setup
```bash
git clone https://github.com/eastonlearns/card-market-papertrader.git
cd card-market-papertrader
python -m grailbot scan --all       # runs on the stdlib, no keys
pip install -r requirements.txt     # only needed for live mode + tooling
pytest -q                           # test suite
```

## Making a change
1. Fork and branch: `feat/<short-name>` or `fix/<short-name>`.
2. Add/adjust tests under `tests/` — every behavior change needs a test.
3. Keep commits small and use [Conventional Commits](https://www.conventionalcommits.org/)
   (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).
4. Ensure `pytest -q` is green (CI runs it on every PR).
5. Open a PR using the template; describe the *why*, not just the *what*.

## Good places to start
See [docs/GOOD_FIRST_ISSUES.md](docs/GOOD_FIRST_ISSUES.md). High-leverage areas:
- **Data adapters** (`sources.py`) — implement a real price-vendor `CompSource`,
  or add an eBay marketplace (`.co.uk`, `.de`) with landed-cost + forex.
- **Resolver** (`resolver.py`) — extend the catalog from open checklist data
  (e.g. JunkWaxHero/CardLists); improve parallel disambiguation.
- **New asset classes** — the `Card` model is asset-agnostic; add Pokémon, wax,
  comics, etc. behind the same interfaces.
- **Walk-forward simulator** — build backtesting on top of the immutable ledger.

## Architecture
Read [ARCHITECTURE.md](ARCHITECTURE.md) first — it maps every module to a layer
and explains the guardrails.
