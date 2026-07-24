from grailbot.config import Settings
from grailbot.ledger import PaperBroker
from grailbot.pipeline import Pipeline
from grailbot.sample_data import SAMPLE_EXITS


def _session(bankroll=25000.0):
    s = Settings()
    broker = PaperBroker(s, bankroll)
    for o in Pipeline(s).run():
        broker.open(o)
    for lot in list(broker.open_lots):
        if lot.card_key in SAMPLE_EXITS:
            broker.close(lot, SAMPLE_EXITS[lot.card_key])
    return broker


def test_opens_only_recommended_and_never_overpays():
    b = _session()
    opens = [e for e in b.entries if e.etype == "OPEN"]
    assert len(opens) == 3                       # v2, v4, v7
    for e in opens:
        assert e.price <= e.max_bid              # disciplined max-bid


def test_realized_pnl_positive_and_cash_conserved():
    b = _session(25000.0)
    s = b.summary()
    assert s["positions_closed"] == 3
    assert s["realized_pnl"] > 0
    assert abs(s["cash"] - (25000.0 + s["realized_pnl"])) < 0.01
    assert s["win_rate"] == 1.0
    assert s["chain_valid"]


def test_max_bid_math():
    b = PaperBroker(Settings(), 1000.0)
    # fair 168 -> 168*0.8675 - 5 - 15 = 125.74
    assert abs(b.max_bid(168.0) - 125.74) < 0.01


def test_immutable_chain_detects_tampering():
    b = _session()
    assert b.verify_chain()
    tampered = b.entries[-1]
    object.__setattr__(tampered, "pnl", tampered.pnl + 1000)   # forge history
    assert not b.verify_chain()
