"""Catalog: the card-identity knowledge base.

Holds products -> parallels (scoped per product) and the player list with
aliases/misspellings. This is what lets the resolver know that "blue glitter"
is a Donruss Optic SSP but nonsense in Prizm, where the SSP is "blue sparkle".
In production, back this with JunkWaxHero/CardLists JSON.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_DEFAULT = Path(__file__).parent / "data" / "catalog.sample.json"


@dataclass
class Parallel:
    name: str
    rarity: str            # "common" | "SP" | "SSP"
    serial: Optional[int]


@dataclass
class Product:
    canonical: str
    aliases: list[str]
    parallels: dict[str, Parallel]


@dataclass
class Player:
    name: str
    sport: str
    catalyst: float
    aliases: list[str]
    misspellings: list[str]


class Catalog:
    def __init__(self, products: dict[str, Product], players: list[Player]):
        self.products = products
        self.players = players

    @classmethod
    def load(cls, path: str | Path = _DEFAULT) -> "Catalog":
        raw = json.loads(Path(path).read_text())
        products: dict[str, Product] = {}
        for canon, pdata in raw["products"].items():
            parallels = {
                pname: Parallel(pname, pv.get("rarity", "common"), pv.get("serial"))
                for pname, pv in pdata["parallels"].items()
            }
            products[canon] = Product(canon, [a.lower() for a in pdata["aliases"]], parallels)
        players = [
            Player(p["name"], p.get("sport", ""), float(p.get("catalyst", 0.5)),
                   [a.lower() for a in p["aliases"]], [m.lower() for m in p.get("misspellings", [])])
            for p in raw["players"]
        ]
        return cls(products, players)

    def match_product(self, title_lc: str) -> Optional[Product]:
        """Longest alias wins so 'topps chrome ucc' beats a bare 'chrome'."""
        best: Optional[Product] = None
        best_len = 0
        for prod in self.products.values():
            for alias in prod.aliases:
                if alias in title_lc and len(alias) > best_len:
                    best, best_len = prod, len(alias)
        return best

    def match_player(self, title_lc: str) -> tuple[Optional[Player], bool]:
        """Return (player, is_misspelled). Longest alias wins."""
        best: Optional[Player] = None
        best_alias = ""
        for pl in self.players:
            for alias in pl.aliases:
                if alias in title_lc and len(alias) > len(best_alias):
                    best, best_alias = pl, alias
        if best is None:
            return None, False
        return best, best_alias in best.misspellings
