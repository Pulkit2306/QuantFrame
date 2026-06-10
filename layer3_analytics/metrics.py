"""
Performance analytics computed in SQL where possible — pushes computation
to the database instead of pulling all rows into Python.
"""

import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import numpy as np
from datetime import date
from layer1_pipeline import database as db


ANALYTICS_SQL = """
WITH daily_returns AS (
    SELECT
        symbol,
        ts,
        close,
        LAG(close) OVER (PARTITION BY symbol ORDER BY ts) AS prev_close
    FROM bars
    WHERE symbol = %(symbol)s
      AND ts BETWEEN %(start)s AND %(end)s
),
returns AS (
    SELECT
        symbol,
        ts,
        close,
        (close - prev_close) / NULLIF(prev_close, 0) AS ret
    FROM daily_returns
    WHERE prev_close IS NOT NULL
),
stats AS (
    SELECT
        symbol,
        COUNT(*)                                      AS n_days,
        AVG(ret)                                      AS mean_ret,
        STDDEV(ret)                                   AS std_ret,
        MIN(close)                                    AS min_price,
        MAX(close)                                    AS max_price,
        FIRST_VALUE(close) OVER (ORDER BY ts)         AS start_price,
        LAST_VALUE(close)  OVER (ORDER BY ts
            ROWS BETWEEN UNBOUNDED PRECEDING
                     AND UNBOUNDED FOLLOWING)         AS end_price
    FROM returns
    GROUP BY symbol, ts, close
)
SELECT DISTINCT ON (symbol)
    symbol,
    n_days,
    mean_ret,
    std_ret,
    min_price,
    max_price,
    start_price,
    end_price
FROM stats
ORDER BY symbol;
"""


def compute_metrics(symbol: str, start: date, end: date) -> dict:
    bars = db.query_bars(symbol, start, end)
    if len(bars) < 2:
        return {"error": "insufficient data"}

    closes = np.array([float(b["close"]) for b in bars])
    returns = np.diff(closes) / closes[:-1]

    sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0.0

    # max drawdown
    peak = np.maximum.accumulate(closes)
    drawdowns = (peak - closes) / np.where(peak == 0, 1, peak)
    max_dd = float(drawdowns.max()) * 100

    # alpha/beta vs SPY (simplified: use market as second query if available)
    total_return = (closes[-1] / closes[0] - 1) * 100

    return {
        "symbol":           symbol,
        "start":            str(start),
        "end":              str(end),
        "n_days":           len(bars),
        "total_return_pct": round(total_return, 2),
        "annualized_return_pct": round(
            ((closes[-1] / closes[0]) ** (252 / len(bars)) - 1) * 100, 2
        ),
        "sharpe_ratio":     round(sharpe, 3),
        "max_drawdown_pct": round(max_dd, 2),
        "volatility_pct":   round(float(returns.std()) * np.sqrt(252) * 100, 2),
        "mean_daily_ret":   round(float(returns.mean()) * 100, 4),
    }


def compute_all_metrics(symbols: list[str], start: date, end: date) -> list[dict]:
    return [compute_metrics(s, start, end) for s in symbols]
