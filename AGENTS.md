# AGENTS.md — working agreement for AI (and human) contributors

This project is developed with AI assistance. This file is the contract agents
follow so their work stays reproducible and reviewable.

## Roles (from the Project Atlas plan)
- **Architecture / product / quant design / review** — lead with a design note
  or issue *before* large changes.
- **Implementation / refactors / documentation** — small, tested, reviewable PRs.

## Principles
1. **The repository is the source of truth**, not chat logs. Every decision lands
   as code, a test, or a doc.
2. **Mock mode must always run keyless** on the standard library. Never add a
   hard dependency to the core path.
3. **Sold comps, not asking prices.** Any valuation code must use realized sales.
4. **Confidence-gate identity.** The resolver must refuse to value cards it
   cannot identify with confidence (`MIN_IDENTITY_CONFIDENCE`).
5. **Every behavior change ships with a test.** CI must stay green.

## Before you build
- Read [ARCHITECTURE.md](ARCHITECTURE.md) and [ROADMAP.md](ROADMAP.md).
- Keep the layer boundaries: identity → data → valuation → strategy → risk →
  paper broker → ledger → evaluation → API → terminal.

## Definition of done
- `pytest -q` green · docs updated · conventional-commit messages ·
  no secrets committed (`.env` is git-ignored).
