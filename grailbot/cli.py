"""Command line interface.

    python -m grailbot scan               # ranked opportunities (mock mode)
    python -m grailbot scan --all         # include rejected, with reasons
    python -m grailbot scan -q cubarsi    # filter the query
"""
from __future__ import annotations

import argparse

from grailbot.config import Settings
from grailbot.pipeline import Pipeline
from grailbot.storage import Store


def _fmt_row(o) -> str:
    mark = "✅" if o.recommended else "· "
    conf = f"{o.resolved.confidence:.2f}"
    edge = f"${o.net_edge:>7.2f}"
    comp = f"${o.comp.median_sold:>6.0f}" if o.comp.n else "   n/a"
    title = o.title[:58]
    return f"{mark} {o.score:5.1f} | edge {edge} | comp {comp} (n={o.comp.n:>2}) | conf {conf} | {title}"


def cmd_scan(args) -> int:
    settings = Settings.load()
    pipe = Pipeline(settings)
    opps = pipe.run(query=args.query, limit=args.limit)

    store = None
    if args.save:
        store = Store(settings.db_path)

    shown = [o for o in opps if o.recommended or args.all]
    print(f"\nGrailBot scan — mode={settings.mode}  vendor={settings.price_vendor}  "
          f"({sum(o.recommended for o in opps)} recommended / {len(opps)} scanned)\n")
    print("  SCORE | EDGE           | COMP (solds)   | CONF | LISTING")
    print("  " + "-" * 92)
    for o in shown:
        print(_fmt_row(o))
        if args.all or o.recommended:
            for r in o.reasons:
                print(f"        └─ {r}")
            if o.resolved.flags:
                print(f"        └─ flags: {', '.join(o.resolved.flags)}")
        if store:
            store.save_opportunity(o)
            store.save_snapshot(o.comp)
    if store:
        store.close()
        print(f"\nSaved to {settings.db_path}")
    print()
    return 0


def cmd_papertrade(args) -> int:
    from grailbot.ledger import PaperBroker
    settings = Settings.load()
    opps = Pipeline(settings).run(query=args.query)
    broker = PaperBroker(settings, starting_cash=args.bankroll)

    for opp in opps:            # broker only opens *recommended*, never overpays
        broker.open(opp)

    # simulate exits (mock: use known later-sold prices; live: fill on real sale)
    exits = {}
    if settings.mode == "mock":
        from grailbot.sample_data import SAMPLE_EXITS
        exits = SAMPLE_EXITS
    for lot in list(broker.open_lots):
        if lot.card_key in exits:
            broker.close(lot, exits[lot.card_key])

    print(f"\nGrailBot paper-trade — bankroll ${args.bankroll:,.0f}  mode={settings.mode}\n")
    print("  SEQ  TYPE    P&L        CASHΔ      | CARD")
    print("  " + "-" * 78)
    for e in broker.entries:
        pnl = f"${e.pnl:+8.2f}" if e.etype == "CLOSE" else "         "
        print(f"  {e.seq:>3}  {e.etype:<6} {pnl}  ${e.cash_delta:+10.2f} | {e.title[:44]}")
    s = broker.summary()
    print("\n  " + "-" * 78)
    print(f"  invested ${s['invested']:,.2f}   realized P&L ${s['realized_pnl']:,.2f}   "
          f"ROI {s['realized_roi']*100:.1f}%   win-rate {s['win_rate']*100:.0f}%")
    print(f"  cash ${s['cash']:,.2f}   opened {s['positions_opened']}   closed {s['positions_closed']}"
          f"   open {s['open_lots']}   ledger integrity: {'OK' if s['chain_valid'] else 'TAMPERED'}")

    if args.save:
        store = Store(settings.db_path)
        for e in broker.entries:
            store.save_ledger_entry(e)
        store.close()
        print(f"\n  Ledger persisted to {settings.db_path}")
    print()
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="grailbot", description="Trading-card value-gap engine")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan", help="scan listings and rank opportunities")
    s.add_argument("-q", "--query", default="", help="filter listings by text")
    s.add_argument("-n", "--limit", type=int, default=50)
    s.add_argument("--all", action="store_true", help="show rejected too, with reasons")
    s.add_argument("--save", action="store_true", help="persist results to SQLite")
    s.set_defaults(func=cmd_scan)

    pt = sub.add_parser("papertrade", help="simulate buying recommended cards on a bankroll")
    pt.add_argument("-b", "--bankroll", type=float, default=25000.0)
    pt.add_argument("-q", "--query", default="")
    pt.add_argument("--save", action="store_true", help="persist the immutable ledger to SQLite")
    pt.set_defaults(func=cmd_papertrade)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
