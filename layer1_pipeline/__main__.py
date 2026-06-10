"""
CLI entry point.

Usage:
    python -m layer1_pipeline ingest [SYMBOL ...]
    python -m layer1_pipeline status
    python -m layer1_pipeline bars SYMBOL START END
    python -m layer1_pipeline init-db
"""

import argparse
import asyncio
import json
import sys
from datetime import date


def cmd_init_db(args):
    from . import database as db
    db.init_schema()
    print("Schema initialized.")


def cmd_ingest(args):
    from .orchestrator import run_pipeline
    symbols = args.symbols or None
    results = asyncio.run(run_pipeline(symbols))
    total_bars = sum(r.bars_inserted for r in results)
    errors = [(r.symbol, r.errors) for r in results if r.errors]
    print(f"Ingested {total_bars} bars across {len(results)} symbols.")
    if errors:
        print("Errors:")
        for sym, errs in errors:
            for e in errs:
                print(f"  {sym}: {e}")
        sys.exit(1)


def cmd_status(args):
    from . import database as db
    rows = db.get_status()
    if not rows:
        print("No data yet. Run: python -m layer1_pipeline ingest")
        return
    fmt = "{:<8} {:>10} {:<24} {:<24}"
    print(fmt.format("SYMBOL", "BARS", "EARLIEST", "LATEST"))
    print("-" * 68)
    for r in rows:
        print(fmt.format(
            r["symbol"],
            r["bar_count"],
            str(r["earliest"])[:19],
            str(r["latest"])[:19],
        ))


def cmd_bars(args):
    from . import database as db
    rows = db.query_bars(args.symbol, date.fromisoformat(args.start), date.fromisoformat(args.end))
    print(json.dumps(rows, default=str, indent=2))


def main():
    parser = argparse.ArgumentParser(prog="layer1_pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init-db", help="Create database schema")
    p_init.set_defaults(func=cmd_init_db)

    p_ingest = sub.add_parser("ingest", help="Fetch and store market data")
    p_ingest.add_argument("symbols", nargs="*", help="Symbols to ingest (default: watchlist)")
    p_ingest.set_defaults(func=cmd_ingest)

    p_status = sub.add_parser("status", help="Show ingestion status per symbol")
    p_status.set_defaults(func=cmd_status)

    p_bars = sub.add_parser("bars", help="Query bars for a symbol")
    p_bars.add_argument("symbol")
    p_bars.add_argument("start", help="YYYY-MM-DD")
    p_bars.add_argument("end",   help="YYYY-MM-DD")
    p_bars.set_defaults(func=cmd_bars)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
