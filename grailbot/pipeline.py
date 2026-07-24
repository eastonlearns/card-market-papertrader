"""Orchestration: listings -> resolve -> comp -> score -> ranked opportunities."""
from __future__ import annotations

from grailbot.catalog import Catalog
from grailbot.config import Settings
from grailbot.models import Comp, Opportunity
from grailbot.resolver import Resolver
from grailbot.scoring import score_opportunity
from grailbot.sources import CompSource, ListingSource, build_sources


class Pipeline:
    def __init__(self, settings: Settings, catalog: Catalog | None = None,
                 listing_source: ListingSource | None = None,
                 comp_source: CompSource | None = None):
        self.s = settings
        self.cat = catalog or Catalog.load()
        self.resolver = Resolver(self.cat)
        if listing_source is None or comp_source is None:
            ls, cs = build_sources(settings)
            listing_source = listing_source or ls
            comp_source = comp_source or cs
        self.listings = listing_source
        self.comps = comp_source
        self._catalyst = {p.name.lower(): p.catalyst for p in self.cat.players}

    def run(self, query: str = "", limit: int = 50) -> list[Opportunity]:
        out: list[Opportunity] = []
        for listing in self.listings.search(query, limit):
            resolved = self.resolver.resolve(listing)
            comp = self.comps.get_comp(resolved.card)
            if comp is None:
                comp = Comp(card_key=resolved.card.key(), median_sold=0.0, n=0)
                opp = Opportunity(resolved, comp, 0.0, 0.0, 0.0, False,
                                  ["no sold comps found — cannot value"])
                out.append(opp)
                continue
            catalyst = self._catalyst.get(resolved.card.player.lower(), 0.5)
            out.append(score_opportunity(resolved, comp, catalyst, self.s))
        # recommended first, then by score desc
        out.sort(key=lambda o: (o.recommended, o.score), reverse=True)
        return out
