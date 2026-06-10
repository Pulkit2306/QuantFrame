"""
CLI for Layer 3 analytics.

Usage:
    python -m layer3_analytics metrics SYMBOL START END
    python -m layer3_analytics all-metrics START END
    python -m layer3_analytics advise SYMBOL START END [--params short=10,long=50]
    python -m layer3_analytics anomalies START END
"""

import argparse
import json
import sys
from datetime import date

import yaml
import pathlib


def load_watchlist() -> list[str]:
    cfg = pathlib.Path(__file__).parent.parent / "layer1_pipeline" / "config.yaml"
    with open(cfg) as f:
        return yaml.safe_load(f)["watchlist"]


def cmd_metrics(args):
    from .metrics import compute_metrics
    result = compute_metrics(args.symbol, date.fromisoformat(args.start), date.fromisoformat(args.end))
    print(json.dumps(result, indent=2))


def cmd_all_metrics(args):
    from .metrics import compute_all_metrics
    symbols = load_watchlist()
    results = compute_all_metrics(symbols, date.fromisoformat(args.start), date.fromisoformat(args.end))
    print(json.dumps(results, indent=2))


def cmd_advise(args):
    from .metrics import compute_metrics
    from .llm_advisor import analyze_backtest

    params = {}
    if args.params:
        for kv in args.params.split(","):
            k, v = kv.split("=")
            params[k.strip()] = int(v.strip())

    metrics = compute_metrics(args.symbol, date.fromisoformat(args.start), date.fromisoformat(args.end))
    mock_backtest = {
        "strategy": "SMA_10_50",
        "total_return_pct": metrics.get("total_return_pct"),
        "sharpe_ratio": metrics.get("sharpe_ratio"),
        "max_drawdown_pct": metrics.get("max_drawdown_pct"),
    }
    result = analyze_backtest(mock_backtest, metrics, params or {"short": 10, "long": 50})
    print(json.dumps(result, indent=2))


def cmd_anomalies(args):
    from .metrics import compute_all_metrics
    from .llm_advisor import detect_anomalies

    symbols = load_watchlist()
    metrics = compute_all_metrics(symbols, date.fromisoformat(args.start), date.fromisoformat(args.end))
    anomalies = detect_anomalies(metrics)
    print(json.dumps(anomalies, indent=2))


def main():
    parser = argparse.ArgumentParser(prog="layer3_analytics")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("metrics")
    p.add_argument("symbol")
    p.add_argument("start")
    p.add_argument("end")
    p.set_defaults(func=cmd_metrics)

    p = sub.add_parser("all-metrics")
    p.add_argument("start")
    p.add_argument("end")
    p.set_defaults(func=cmd_all_metrics)

    p = sub.add_parser("advise")
    p.add_argument("symbol")
    p.add_argument("start")
    p.add_argument("end")
    p.add_argument("--params", help="key=val,key=val e.g. short=5,long=20")
    p.set_defaults(func=cmd_advise)

    p = sub.add_parser("anomalies")
    p.add_argument("start")
    p.add_argument("end")
    p.set_defaults(func=cmd_anomalies)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
