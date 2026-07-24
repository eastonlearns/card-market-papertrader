"""Card-identity resolver: eBay listing title -> structured Card + confidence.

This is the load-bearing component. The whole diligence takeaway was that the
edge inverts into a loss if you misresolve a parallel (offer $850-card money on
a $170 card). So the resolver is deliberately conservative and *flags its own
uncertainty* rather than guessing.
"""
from __future__ import annotations

import re
from typing import Optional

from grailbot.catalog import Catalog, Product
from grailbot.models import Card, Listing, Resolved

_YEAR = re.compile(r"\b(20\d{2}(?:-\d{2})?)\b")
_CARDNO = re.compile(r"#\s?(\d{1,4})\b")
_SERIAL = re.compile(r"(?:^|[^\d])(\d{1,4})\s*/\s*(\d{1,4})\b")   # 68/99 or /99
_SERIAL_SLASH = re.compile(r"/\s?(\d{1,4})\b")
_GRADE = re.compile(r"\b(psa|bgs|sgc|cgc)\s?(10|9\.5|9|8\.5|8)\b", re.I)

# Color / parallel-ish tokens that signal "this is probably not a base card".
# If one of these is present but we can't map it to the detected product's
# parallel list, we do NOT guess — we flag ambiguity and drop confidence.
_PARALLEL_WORDS = (
    "glitter", "sparkle", "hyper", "shock", "scope", "mojo", "pulsar", "lava",
    "negative", "x-fractor", "xfractor", "refractor", "mini-diamond",
    "mini diamond", "velocity", "wave", "disco", "cracked ice", "die-cut",
)


class Resolver:
    def __init__(self, catalog: Catalog):
        self.cat = catalog

    def resolve(self, listing: Listing) -> Resolved:
        t = listing.title
        tl = t.lower()
        flags: list[str] = []
        conf = 1.0

        # --- player -------------------------------------------------------
        player, misspelled = self.cat.match_player(tl)
        if player is None:
            flags.append("UNKNOWN_PLAYER")
            conf = 0.2
            card = Card(player="?", year=self._year(tl))
            return Resolved(listing, card, round(conf, 3), flags)
        if misspelled:
            flags.append("NAME_MISSPELLED")   # naive-seller signal (a good one)

        # --- product ------------------------------------------------------
        product = self.cat.match_product(tl)
        if product is None:
            flags.append("UNKNOWN_PRODUCT")
            conf -= 0.30

        # --- parallel (scoped to product) --------------------------------
        parallel, serial_to = self._parallel(tl, product, flags)
        if parallel is None:
            parallel = "base"
            if self._has_parallel_word(tl):
                flags.append("PARALLEL_AMBIGUOUS")
                conf -= 0.35

        # --- serial (explicit in title overrides catalog default) --------
        explicit_serial = self._serial(tl)
        if explicit_serial is not None:
            serial_to = explicit_serial

        # --- grade --------------------------------------------------------
        grade = self._grade(t)

        card = Card(
            player=player.name,
            sport=player.sport,
            year=self._year(tl),
            product=product.canonical if product else "",
            card_no=self._cardno(t),
            parallel=parallel,
            serial_to=serial_to,
            grade=grade,
        )
        conf = max(0.0, min(1.0, conf))
        return Resolved(listing, card, round(conf, 3), flags)

    # -- helpers ----------------------------------------------------------
    @staticmethod
    def _year(tl: str) -> str:
        m = _YEAR.search(tl)
        return m.group(1) if m else ""

    @staticmethod
    def _cardno(t: str) -> str:
        m = _CARDNO.search(t)
        return m.group(1) if m else ""

    @staticmethod
    def _serial(tl: str) -> Optional[int]:
        m = _SERIAL.search(tl)
        if m:
            return int(m.group(2))
        m = _SERIAL_SLASH.search(tl)
        return int(m.group(1)) if m else None

    @staticmethod
    def _grade(t: str) -> Optional[str]:
        m = _GRADE.search(t)
        return f"{m.group(1).upper()} {m.group(2)}" if m else None

    @staticmethod
    def _has_parallel_word(tl: str) -> bool:
        return any(w in tl for w in _PARALLEL_WORDS)

    def _parallel(self, tl: str, product: Optional[Product], flags: list[str]):
        """Match the longest parallel name that belongs to THIS product."""
        if product is None:
            return None, None
        best_name: Optional[str] = None
        best_len = 0
        for pname, pinfo in product.parallels.items():
            if pname == "base":
                continue
            if pname in tl and len(pname) > best_len:
                best_name, best_len = pname, len(pname)
        if best_name is None:
            # A parallel word exists but none belongs to this product -> the
            # classic cross-product trap (e.g. "glitter" seen under Prizm).
            if self._has_parallel_word(tl):
                flags.append("CROSS_PRODUCT_COLOR")
            return None, None
        serial = product.parallels[best_name].serial
        return best_name, serial
