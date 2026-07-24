from grailbot.config import Settings
from grailbot.models import Card, Comp, Listing, Resolved
from grailbot.scoring import compute_edge, score_opportunity

S = Settings()  # defaults: fee .1325, ship_out 5, min_edge 15, min_conf .70, floor 8


def _res(title="x", price=95.0, shipping=0.0, conf=1.0, flags=None,
         parallel="blue glitter", serial=None, grade=None):
    card = Card(player="Jayden Daniels", year="2024", product="donruss optic",
                parallel=parallel, serial_to=serial, grade=grade)
    return Resolved(Listing("id", title, price, shipping), card, conf, flags or [])


def test_edge_math():
    comp = Comp("k", median_sold=168.0, n=7)
    net, roi = compute_edge(landed=95.0, comp=comp, s=S)
    assert round(net, 2) == 45.74          # 168*0.8675 - 5 - 95
    assert roi > 0.4


def test_genuine_deal_recommended():
    o = score_opportunity(_res(price=95.0, flags=["NAME_MISSPELLED"]),
                          Comp("k", 168.0, 7, psa10_median=330.0), catalyst=0.7, s=S)
    assert o.recommended
    assert o.net_edge > 15
    assert any("grade-arb" in r for r in o.reasons)


def test_fair_priced_card_rejected():
    o = score_opportunity(_res(price=145.0, shipping=3.99),
                          Comp("k", 168.0, 7), catalyst=0.7, s=S)
    assert not o.recommended               # edge below minimum


def test_value_floor_rejects_cheap_base():
    o = score_opportunity(_res(price=2.0, shipping=1.25, parallel="refractor"),
                          Comp("k", 2.2, 20), catalyst=0.9, s=S)
    assert not o.recommended
    assert any("too cheap" in r for r in o.reasons)


def test_low_confidence_blocks_recommendation():
    o = score_opportunity(_res(price=60.0, conf=0.55, flags=["CROSS_PRODUCT_COLOR"]),
                          Comp("k", 850.0, 5), catalyst=0.8, s=S)
    assert not o.recommended               # would look like a huge deal — gated out
    assert any("LOW CONFIDENCE" in r for r in o.reasons)
