"""Edge math + 0-100 opportunity score, with the diligence guardrails baked in.

edge (buyer flipping):  proceeds = median_sold * (1 - fee_rate)
                        net_edge = proceeds - ship_out - landed_cost
A card only clears if net_edge and ROI are positive AFTER fees — the reason
both football "deals" evaporated when we used sold comps instead of asks.
"""
from __future__ import annotations

from grailbot.config import Settings
from grailbot.models import Comp, Opportunity, Resolved


def _scarcity(serial, rarity_hint: str = "") -> float:
    if serial is None:
        return 0.2
    if serial <= 99:
        return 1.0
    if serial <= 299:
        return 0.6
    return 0.35


def compute_edge(landed: float, comp: Comp, s: Settings) -> tuple[float, float]:
    proceeds = comp.median_sold * (1 - s.fee_rate)
    net = round(proceeds - s.ship_out - landed, 2)
    roi = round(net / landed, 3) if landed > 0 else 0.0
    return net, roi


def score_opportunity(resolved: Resolved, comp: Comp, catalyst: float,
                      s: Settings) -> Opportunity:
    listing = resolved.listing
    landed = listing.landed
    net, roi = compute_edge(landed, comp, s)
    reasons: list[str] = []

    # ---- components (each 0..1), weighted per the Atlas/Chat 0-100 model
    discount = max(0.0, min(1.0, net / comp.median_sold)) if comp.median_sold else 0.0
    comp_conf = max(0.0, min(1.0, comp.n / 8.0))
    liq_basis = comp.velocity or comp.n            # sell-through / demand depth
    liquidity = max(0.0, min(1.0, liq_basis / 12.0))
    scarcity = _scarcity(resolved.card.serial_to)
    anomaly = 1.0 if "NAME_MISSPELLED" in resolved.flags else 0.0
    grade_up = 0.0
    if resolved.card.grade is None and comp.psa10_median:
        if comp.psa10_median > comp.median_sold * 1.6:   # raw->10 upside (pre cost/risk)
            grade_up = 1.0
            reasons.append("grade-arb upside (raw vs PSA10)")

    # seller / authenticity risk penalty (0..-20)
    fb = listing.seller_feedback
    penalty = 18 if fb < 95 else 10 if fb < 98 else 4 if fb < 99.5 else 0
    if "AUTHENTICITY_RISK" in resolved.flags:
        penalty = min(20, penalty + 10)
    if penalty:
        reasons.append(f"seller/authenticity risk -{penalty} ({fb:.1f}% feedback)")
    if liquidity < 0.2:
        reasons.append("thin liquidity — slow to resell")

    raw_score = (
        25 * discount + 15 * comp_conf + 15 * liquidity +
        15 * max(0.0, min(1.0, catalyst)) + 10 * anomaly +
        10 * grade_up + 5 * scarcity - penalty
    )
    # ---- confidence gate (the critical guardrail) ----------------------
    score = round(max(0.0, raw_score) * resolved.confidence, 1)

    recommended = True
    if resolved.confidence < s.min_identity_confidence:
        recommended = False
        reasons.append(f"LOW CONFIDENCE {resolved.confidence:.2f} < {s.min_identity_confidence:.2f} — do not act")
    if comp.median_sold < s.value_floor:
        recommended = False
        reasons.append(f"too cheap to flip (comp ${comp.median_sold:.0f} < floor ${s.value_floor:.0f})")
    if net < s.min_net_edge:
        recommended = False
        reasons.append(f"edge ${net:.2f} < min ${s.min_net_edge:.2f}")
    if recommended:
        reasons.append(f"net edge ${net:.2f} ({roi*100:.0f}% ROI) vs {comp.n} solds @ median ${comp.median_sold:.0f}")
    if anomaly:
        reasons.append("misspelled listing (naive-seller signal)")

    return Opportunity(resolved, comp, net, roi, score, recommended, reasons)
