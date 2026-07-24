"""Core domain models. Plain dataclasses so the engine runs dependency-free."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Card:
    """A resolved card identity — the atomic unit everything keys on."""
    player: str
    sport: str = ""
    year: str = ""
    product: str = ""            # canonical product family, e.g. "donruss optic"
    card_no: str = ""
    parallel: str = "base"       # canonical parallel within the product
    serial_to: Optional[int] = None   # print run denominator, e.g. 96 for /96
    grade: Optional[str] = None       # "PSA 10", "BGS 9.5", or None (raw)

    def key(self) -> str:
        """Stable comp-lookup key. Grade folded in because raw != graded."""
        g = self.grade or "RAW"
        return "|".join(
            x.lower() for x in (self.player, self.year, self.product, self.parallel, g)
        )


@dataclass
class Listing:
    """A raw listing pulled from a marketplace."""
    listing_id: str
    title: str
    price: float
    shipping: float = 0.0
    currency: str = "USD"
    url: str = ""
    location: str = "US"
    seller_feedback: float = 100.0      # % positive
    fmt: str = "BIN"                     # "BIN" | "AUCTION"

    @property
    def landed(self) -> float:
        return round(self.price + self.shipping, 2)


@dataclass
class Comp:
    """Sold-comp statistics for a card key."""
    card_key: str
    median_sold: float
    n: int                              # number of solds in the window
    low: float = 0.0
    high: float = 0.0
    psa10_median: Optional[float] = None  # for raw->10 grade-arb signal
    velocity: int = 0                   # solds in last 30d (liquidity)
    distinct_buyers: int = 0            # unique buyers in window (demand breadth)
    source: str = "mock"


@dataclass
class Resolved:
    listing: Listing
    card: Card
    confidence: float                   # 0..1 identity confidence
    flags: list[str] = field(default_factory=list)


@dataclass
class Opportunity:
    resolved: Resolved
    comp: Comp
    net_edge: float                     # $ profit after fees + shipping
    roi: float                          # net_edge / landed cost
    score: float                        # 0..100
    recommended: bool
    reasons: list[str] = field(default_factory=list)

    @property
    def title(self) -> str:
        return self.resolved.listing.title
