import pytest

pytest.importorskip("mcp")  # only runs when the MCP SDK is installed

from grailbot import mcp_server as m


def test_resolve_flags_misspelling():
    d = m.resolve_card_data("2024 Donruss Optic Jaden Daniels Blue Glitter #248")
    assert d["player"] == "Jayden Daniels"
    assert "NAME_MISSPELLED" in d["flags"]
    assert d["identified"] is True


def test_resolve_refuses_cross_product_trap():
    d = m.resolve_card_data("2024 Panini Prizm Jayden Daniels Blue Glitter #347 /96 SSP")
    assert d["identified"] is False
    assert "CROSS_PRODUCT_COLOR" in d["flags"]


def test_value_rejects_fair_card():
    d = m.value_card_data("2024 Donruss Optic Jaden Daniels Blue Glitter #248", 145.0, 3.99)
    assert d["valued"] is True and d["recommended"] is False


def test_value_flags_real_deal():
    d = m.value_card_data("2024 Donruss Optic Jaden Daniels Blue Glitter #248", 95.0)
    assert d["recommended"] is True and d["net_edge"] > 15


def test_scan_returns_only_recommended():
    d = m.scan_data()
    assert d["recommended"] >= 1
    assert all(o["recommended"] for o in d["opportunities"])


def test_paper_trade_reports_pnl_and_valid_chain():
    d = m.paper_trade_data(25000)
    assert d["realized_pnl"] > 0
    assert d["chain_valid"] is True
