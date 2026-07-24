from grailbot.catalog import Catalog
from grailbot.models import Listing
from grailbot.resolver import Resolver

R = Resolver(Catalog.load())


def _resolve(title):
    return R.resolve(Listing("t", title, price=1.0))


def test_misspelled_name_is_flagged_but_resolved():
    r = _resolve("2024 Donruss Optic Jaden Daniels Blue Glitter #248")
    assert r.card.player == "Jayden Daniels"
    assert "NAME_MISSPELLED" in r.flags
    assert r.card.parallel == "blue glitter"
    assert r.confidence >= 0.7


def test_cross_product_color_trap_lowers_confidence():
    # "Blue Glitter" is Optic-only; under Prizm it must NOT resolve confidently.
    r = _resolve("2024 Panini Prizm Jayden Daniels Blue Glitter #347 /96 SSP")
    assert r.card.product == "prizm"
    assert r.card.parallel == "base"          # refused to guess the parallel
    assert "CROSS_PRODUCT_COLOR" in r.flags
    assert r.confidence < 0.7                  # gate will block recommendation


def test_serial_parsing():
    r = _resolve("2025-26 Topps Chrome UEFA Pau Cubarsi White Refractor /30")
    assert r.card.serial_to == 30
    assert r.card.parallel == "white refractor"


def test_grade_parsing():
    r = _resolve("2024 Donruss Optic Jayden Daniels Blue Glitter PSA 10 #248")
    assert r.card.grade == "PSA 10"


def test_unknown_player_low_confidence():
    r = _resolve("2024 Panini Prizm Marvin Harrison Jr Silver #5")
    assert "UNKNOWN_PLAYER" in r.flags
    assert r.confidence <= 0.3
