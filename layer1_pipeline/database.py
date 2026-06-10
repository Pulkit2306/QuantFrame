"""
PostgreSQL schema and data access layer.

Schema design decisions:
- bars is range-partitioned by year so time-range queries skip irrelevant partitions
- BRIN index on timestamp instead of B-tree: bars are written in time order,
  BRIN is ~100x smaller with equivalent scan performance for sequential data
- ON CONFLICT DO NOTHING makes all inserts idempotent — safe to re-run after crashes
"""

import os
import logging
from contextlib import contextmanager
from datetime import datetime, date
from typing import Iterator

import psycopg2
import psycopg2.extras
from psycopg2.extensions import connection as PGConnection

from .models import Bar, Quote

logger = logging.getLogger(__name__)

DDL = """
CREATE TABLE IF NOT EXISTS symbols (
    id          SERIAL PRIMARY KEY,
    ticker      TEXT NOT NULL UNIQUE,
    name        TEXT,
    asset_class TEXT NOT NULL DEFAULT 'us_equity',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bars (
    symbol      TEXT        NOT NULL,
    ts          TIMESTAMPTZ NOT NULL,
    open        NUMERIC(18,6) NOT NULL,
    high        NUMERIC(18,6) NOT NULL,
    low         NUMERIC(18,6) NOT NULL,
    close       NUMERIC(18,6) NOT NULL,
    volume      BIGINT      NOT NULL,
    vwap        NUMERIC(18,6),
    trade_count INT,
    PRIMARY KEY (symbol, ts)
) PARTITION BY RANGE (ts);

CREATE TABLE IF NOT EXISTS quotes (
    symbol      TEXT        NOT NULL,
    ts          TIMESTAMPTZ NOT NULL,
    bid_price   NUMERIC(18,6) NOT NULL,
    ask_price   NUMERIC(18,6) NOT NULL,
    bid_size    INT         NOT NULL,
    ask_size    INT         NOT NULL,
    PRIMARY KEY (symbol, ts)
) PARTITION BY RANGE (ts);

CREATE TABLE IF NOT EXISTS ingest_log (
    id          SERIAL PRIMARY KEY,
    symbol      TEXT        NOT NULL,
    run_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    bars_count  INT         NOT NULL DEFAULT 0,
    quotes_count INT        NOT NULL DEFAULT 0,
    status      TEXT        NOT NULL DEFAULT 'ok',
    message     TEXT
);
"""

PARTITION_TEMPLATE = """
CREATE TABLE IF NOT EXISTS {table}_{year} PARTITION OF {table}
    FOR VALUES FROM ('{year}-01-01') TO ('{next_year}-01-01');
CREATE INDEX IF NOT EXISTS idx_{table}_{year}_ts
    ON {table}_{year} USING BRIN (ts);
"""


def get_connection_string() -> str:
    if url := os.environ.get("DATABASE_URL"):
        return url
    import yaml, pathlib
    cfg_path = pathlib.Path(__file__).parent / "config.yaml"
    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)["database"]
    return (
        f"host={cfg['host']} port={cfg['port']} dbname={cfg['name']} "
        f"user={cfg['user']} password={cfg['password']}"
    )


@contextmanager
def get_conn() -> Iterator[PGConnection]:
    conn = psycopg2.connect(get_connection_string())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_schema() -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(DDL)
    ensure_partitions_for_years(list(range(2020, datetime.now().year + 2)))
    logger.info("Schema initialized")


def ensure_partitions_for_years(years: list[int]) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            for year in years:
                for table in ("bars", "quotes"):
                    sql = PARTITION_TEMPLATE.format(
                        table=table, year=year, next_year=year + 1
                    )
                    cur.execute(sql)


def upsert_bars(bars: list[Bar]) -> int:
    if not bars:
        return 0
    sql = """
        INSERT INTO bars (symbol, ts, open, high, low, close, volume, vwap, trade_count)
        VALUES %s
        ON CONFLICT (symbol, ts) DO NOTHING
    """
    rows = [
        (b.symbol, b.timestamp, b.open, b.high, b.low, b.close,
         b.volume, b.vwap, b.trade_count)
        for b in bars
    ]
    with get_conn() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(cur, sql, rows)
            return cur.rowcount


def upsert_quotes(quotes: list[Quote]) -> int:
    if not quotes:
        return 0
    sql = """
        INSERT INTO quotes (symbol, ts, bid_price, ask_price, bid_size, ask_size)
        VALUES %s
        ON CONFLICT (symbol, ts) DO NOTHING
    """
    rows = [
        (q.symbol, q.timestamp, q.bid_price, q.ask_price, q.bid_size, q.ask_size)
        for q in quotes
    ]
    with get_conn() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(cur, sql, rows)
            return cur.rowcount


def get_latest_bar_ts(symbol: str) -> datetime | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT MAX(ts) FROM bars WHERE symbol = %s", (symbol,)
            )
            row = cur.fetchone()
            return row[0] if row and row[0] else None


def log_ingest(symbol: str, bars: int, quotes: int, status: str = "ok", message: str = "") -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO ingest_log (symbol, bars_count, quotes_count, status, message) "
                "VALUES (%s, %s, %s, %s, %s)",
                (symbol, bars, quotes, status, message),
            )


def query_bars(symbol: str, start: date, end: date) -> list[dict]:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM bars WHERE symbol = %s AND ts BETWEEN %s AND %s ORDER BY ts",
                (symbol, start, end),
            )
            return [dict(r) for r in cur.fetchall()]


def get_status() -> list[dict]:
    sql = """
        SELECT
            symbol,
            COUNT(*) AS bar_count,
            MIN(ts)  AS earliest,
            MAX(ts)  AS latest
        FROM bars
        GROUP BY symbol
        ORDER BY symbol
    """
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            return [dict(r) for r in cur.fetchall()]
