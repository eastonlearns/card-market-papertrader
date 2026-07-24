from grailbot.config import Settings
from grailbot.pipeline import Pipeline


def _by_id(opps):
    return {o.resolved.listing.listing_id: o for o in opps}


def test_pipeline_runs_and_ranks():
    opps = Pipeline(Settings()).run()
    assert len(opps) == 7
    m = _by_id(opps)
    # v2: underpriced + misspelled -> recommended
    assert m["v2"].recommended
    # v1: fair vs solds -> rejected
    assert not m["v1"].recommended
    # v3: cross-product trap -> rejected (safety)
    assert not m["v3"].recommended
    # v4: scarce /30 underpriced -> recommended
    assert m["v4"].recommended
    # v5: base too cheap -> rejected
    assert not m["v5"].recommended
    # v6: unknown player -> rejected
    assert not m["v6"].recommended
    # recommended sort to the top
    assert opps[0].recommended
