"""Realistic sample data mirroring our actual eBay diligence (Jul 2026).

Lets the whole pipeline run end-to-end with no keys, and demonstrates each
guardrail firing on a real-world case.
"""
from __future__ import annotations

from grailbot.models import Comp, Listing

SAMPLE_LISTINGS: list[Listing] = [
    # 1) The "looks cheap vs asks" card that is actually FAIR vs solds -> rejected.
    Listing("v1", "2024 PANINI DONRUSS OPTIC #248 BLUE GLITTER SSP JADEN DANIELS RC",
            price=145.00, shipping=3.99, location="US", seller_feedback=100.0),
    # 2) A genuine underpriced + MISSPELLED naive-seller listing -> recommended.
    Listing("v2", "2024 Donruss Optic Jaden Daniels Blue Glitter Rookie #248",
            price=95.00, shipping=0.0, location="US", seller_feedback=99.4),
    # 3) The TRAP: a Prizm card whose title misuses "Blue Glitter" (Glitter is
    #    Optic-only). Resolver refuses to value it -> NOT recommended.
    Listing("v3", "2024 Panini Prizm Jayden Daniels Blue Glitter #347 /96 SSP",
            price=200.00, shipping=5.00, location="US", seller_feedback=100.0),
    # 4) A real soccer opportunity: scarce /30 SSP underpriced -> recommended.
    Listing("v4", "2025-26 Topps Chrome UEFA Pau Cubarsi White Refractor /30 Barcelona",
            price=55.00, shipping=1.36, location="US", seller_feedback=100.0),
    # 5) Base card: too cheap to flip after fees -> rejected by value floor.
    Listing("v5", "2025-26 Topps Chrome UEFA Club Competitions #183 Pau Cubarsi Refractor",
            price=2.00, shipping=1.25, location="US", seller_feedback=100.0),
    # 6) Unknown player: graceful skip (no catalog entry, no comp).
    Listing("v6", "2024 Panini Prizm Marvin Harrison Jr Silver #5 Rookie",
            price=40.00, shipping=0.0, location="US", seller_feedback=98.0),
    # 7) Cross-border supply (country-arb texture): same /30, EU seller, high ship.
    Listing("v7", "2025-26 Topps Chrome UEFA Pau Cubarsi White Refractor /30",
            price=48.00, shipping=14.50, currency="USD", location="DE", seller_feedback=99.8),
]

# Comps keyed by Card.key()  ==  player|year|product|parallel|grade(RAW if none)
SAMPLE_COMPS: dict[str, Comp] = {
    "jayden daniels|2024|donruss optic|blue glitter|raw":
        Comp("jayden daniels|2024|donruss optic|blue glitter|raw",
             median_sold=168.0, n=7, low=150.0, high=390.0, psa10_median=330.0,
             velocity=6, distinct_buyers=6, source="mock"),
    "pau cubarsi|2025-26|topps chrome ucc|white refractor|raw":
        Comp("pau cubarsi|2025-26|topps chrome ucc|white refractor|raw",
             median_sold=100.0, n=4, low=90.0, high=110.0,
             velocity=3, distinct_buyers=3, source="mock"),
    "pau cubarsi|2025-26|topps chrome ucc|refractor|raw":
        Comp("pau cubarsi|2025-26|topps chrome ucc|refractor|raw",
             median_sold=2.2, n=20, low=1.0, high=3.0,
             velocity=30, distinct_buyers=25, source="mock"),
    # Note: no comp for the Prizm "blue glitter" trap key -> engine cannot value it.
}

# Simulated realized exits — "what the card later sold for" — for paper trading.
SAMPLE_EXITS: dict[str, float] = {
    "jayden daniels|2024|donruss optic|blue glitter|raw": 172.0,
    "pau cubarsi|2025-26|topps chrome ucc|white refractor|raw": 104.0,
}
