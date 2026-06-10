"""
Pipeline orchestrator — gap-fill logic ensures we only fetch what's missing.
Re-running after a crash or bad deploy is always safe: idempotent by design.
"""

import asyncio
import logging
import pathlib
from datetime import datetime, timedelta, timezone

import yaml

from . import database as db
from .fetcher import fetch_symbol_bars
from .models import IngestResult

logger = logging.getLogger(__name__)


def load_config() -> dict:
    cfg_path = pathlib.Path(__file__).parent / "config.yaml"
    with open(cfg_path) as f:
        return yaml.safe_load(f)


async def ingest_symbol(
    symbol: str,
    cfg: dict,
    semaphore: asyncio.Semaphore,
) -> IngestResult:
    result = IngestResult(symbol=symbol, bars_inserted=0, quotes_inserted=0, errors=[])

    try:
        latest = db.get_latest_bar_ts(symbol)
        if latest:
            start = latest + timedelta(days=1)
        else:
            lookback = cfg["pipeline"]["default_lookback_days"]
            start = datetime.now(timezone.utc) - timedelta(days=lookback)

        end = datetime.now(timezone.utc) - timedelta(days=1)

        if start >= end:
            logger.info("%s is already up to date", symbol)
            return result

        bars = await fetch_symbol_bars(
            symbol=symbol,
            start=start,
            end=end,
            timeframe=cfg["pipeline"]["bars_timeframe"],
            semaphore=semaphore,
        )

        result.bars_inserted = db.upsert_bars(bars)
        db.log_ingest(symbol, result.bars_inserted, 0)
        logger.info("%s: inserted %d bars", symbol, result.bars_inserted)

    except Exception as exc:
        msg = str(exc)
        result.errors.append(msg)
        db.log_ingest(symbol, 0, 0, status="error", message=msg)
        logger.error("%s: %s", symbol, msg)

    return result


async def run_pipeline(symbols: list[str] | None = None) -> list[IngestResult]:
    cfg = load_config()
    watchlist = symbols or cfg["watchlist"]
    max_concurrent = cfg["pipeline"]["max_concurrent_requests"]

    db.ensure_partitions_for_years(
        list(range(2020, datetime.now().year + 2))
    )

    semaphore = asyncio.Semaphore(max_concurrent)
    tasks = [ingest_symbol(sym, cfg, semaphore) for sym in watchlist]
    results = await asyncio.gather(*tasks)
    return list(results)
