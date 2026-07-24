# Changelog

All notable changes to this project are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/); versioning is
[SemVer](https://semver.org/).

## [Unreleased]
### Added
- **MCP server** (`grailbot.mcp_server`, FastMCP) exposing four read-only tools —
  `grailbot_resolve_card`, `grailbot_value_card`, `grailbot_scan_opportunities`,
  `grailbot_paper_trade` — so any MCP client can use the engine in natural language.
  Runs keyless in mock mode. Docs in `docs/MCP.md`.

## [0.1.0] — 2026-07-24
### Added
- Card-identity **resolver** with per-product parallel scoping, misspelling
  detection, and self-confidence scoring (the "Blue Glitter ≠ Blue Sparkle" gate).
- **Valuation + 0–100 scoring** with net-of-fees edge, and a confidence gate,
  value floor, and minimum-edge guardrails.
- Scoring signals: discount, comp confidence, **liquidity/sell-through**,
  catalyst, listing anomaly (naive-seller), grade-arb upside, scarcity, and a
  **seller/authenticity-risk** penalty.
- **Data source adapters**: mock (bundled), plus live `EbayBrowseSource` and
  `SportsCardsProSource` skeletons.
- **Immutable, hash-chained paper-trading ledger** + broker (max-bid discipline,
  realized P&L, tamper detection).
- CLI: `scan` and `papertrade`. SQLite storage. 15-test suite. Mock mode runs
  with zero dependencies and zero keys.
