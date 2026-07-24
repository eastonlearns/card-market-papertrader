# Good first issues

Starter tasks for new contributors. Each is scoped to a single module and has a
clear "done" test. Open an issue referencing one before you start.

### Data / adapters
- [ ] Implement a real `CompSource` for SportsCardsPro (`sources.py`) and map its
      response into `Comp`. *Done when:* live mode returns comps for a known card.
- [ ] Add an eBay marketplace param end-to-end (`EBAY_GB`) with landed-cost +
      a simple forex hook. *Done when:* a `.co.uk` listing scores correctly in USD.

### Resolver / catalog
- [ ] Load catalog from an external JSON checklist source (e.g. JunkWaxHero/CardLists)
      instead of the bundled sample. *Done when:* `Catalog.load(url_or_path)` works.
- [ ] Add fuzzy player matching (difflib) with a misspelling-confidence penalty.

### Scoring / evidence
- [ ] Emit a structured (not just text) explanation object per opportunity.
- [ ] Add an auction-timing signal (bids, time-left) to `scoring`.

### Ledger / simulation
- [ ] Add `papertrade --resume` that reloads the ledger from SQLite and verifies
      the hash chain on load.
- [ ] Build a minimal walk-forward loop over a date-partitioned comp history.

### Docs / DX
- [ ] Add example output/screenshots to the README.
- [ ] Add type checking (mypy) to CI.
