# GrailBot

**A value-gap engine for collectible card markets.** It pulls listings, resolves
each to an exact card identity, values it against *sold* comps, and ranks
opportunities by net-of-fees edge — refusing to act on any card it can't
confidently identify.

GrailBot is the open reference engine for **Project Atlas**, a longer-term vision
of an intelligence layer ("a Bloomberg Terminal") for inefficient collectible
markets. It's built to be forked, extended, and connected as the community sees fit.

[![CI](https://github.com/eastonlearns/card-market-papertrader/actions/workflows/ci.yml/badge.svg)](https://github.com/eastonlearns/card-market-papertrader/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

## Run it in 10 seconds (no keys, no network)
Mock mode runs on the Python standard library alone:

```bash
python -m grailbot scan --all       # rank opportunities on bundled sample data
python -m grailbot papertrade        # simulate buying the recommended cards
pytest -q                            # 15 tests
```

Example `scan` output — note the engine reproducing real market behavior:

```
✅ 55.9 | edge $ 45.74 | comp $168 (n=7) | conf 1.00 | ...Jaden Daniels Blue Glitter #248
      └─ misspelled listing (naive-seller signal) + grade-arb upside
·  ...  | edge $ -8.25 | comp $168 (n=7) | conf 1.00 | ...BLUE GLITTER $145 → fair vs solds, rejected
·   0.0 | comp n/a     | conf 0.65 | ...Prizm "Blue Glitter" /96 → CROSS_PRODUCT_COLOR, refused
```

The card that *looks* 30% cheap is rejected because it's fair against sold comps;
the trap listing (a color word that means different cards in different products)
is refused rather than guessed.

## What's inside
| Stage | Module | Does |
|---|---|---|
| Identity | `resolver.py` + `catalog.py` | title → card + a confidence score |
| Market data | `sources.py` | eBay + price-vendor adapters (mock + live skeletons) |
| Valuation & scoring | `scoring.py` | net-of-fees edge, 0–100 score, guardrails |
| Paper broker & ledger | `ledger.py` | immutable, hash-chained paper trading |
| Terminal | `cli.py` | `scan`, `papertrade` |

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full map.

## Guardrails (the hard-won part)
- **Sold comps, never asking prices** — asks are systematically inflated.
- **Confidence gate** — below a threshold the resolver refuses to value a card.
- **Skip base cards** — fees eat the edge.
- **Max-bid discipline + immutable ledger** — never overpay; `verify_chain()`
  detects any tampering with trade history.

## Paper trading
`papertrade` (Project Atlas Priority #1) opens only *recommended* cards on a
simulated bankroll, records fair value / max bid / expected hold / exit / fees,
and reports realized P&L, ROI, and win-rate — the evidence that the model has a
real edge before anyone risks money.

## Going live
```bash
cp .env.example .env        # add your OWN eBay + price-vendor keys
# set GRAILBOT_MODE=live, then:
pip install -r requirements.txt
python -m grailbot scan --save
```
The one hard dependency is a **sold-comp feed** (eBay walls sold data). Active
listings are free via the eBay Browse API.

## Project layout
```
grailbot/        engine (resolver, sources, scoring, pipeline, ledger, storage, cli)
tests/           pytest suite
docs/            good-first-issues and notes
.github/         CI workflow + issue/PR templates
```

## Contributing
Newcomers welcome — start with [docs/GOOD_FIRST_ISSUES.md](docs/GOOD_FIRST_ISSUES.md)
and [CONTRIBUTING.md](CONTRIBUTING.md). See the [roadmap](ROADMAP.md).

## License
[MIT](LICENSE) — use it, fork it, build on it.
