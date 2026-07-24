"""GrailBot — a trading-card value-gap engine.

Pipeline: fetch listings -> resolve card identity -> fetch sold comps ->
score net-of-fees edge with confidence gating -> rank opportunities.

Designed around the hard lessons from diligence:
  * price off SOLD comps, never asking prices
  * skip base cards (fees eat thin edge)
  * gate everything on identity confidence (Blue Glitter != Blue Sparkle)
"""
__version__ = "0.1.0"
