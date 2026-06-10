"""
Async Alpaca market data fetcher.

Rate-limit safety: asyncio.Semaphore caps concurrent requests at the pipeline
config value (default 5). This gives precise control without threads or a process pool.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import AsyncIterator

import httpx

from .models import Bar, Quote

logger = logging.getLogger(__name__)

BASE_URL = "https://data.alpaca.markets/v2"


def _get_headers() -> dict:
    key = os.environ.get("ALPACA_API_KEY", "")
    secret = os.environ.get("ALPACA_SECRET_KEY", "")
    if not key or not secret:
        raise EnvironmentError(
            "Set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables. "
            "Free data access at https://alpaca.markets — no trading account needed."
        )
    return {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}


async def fetch_bars(
    client: httpx.AsyncClient,
    symbol: str,
    start: datetime,
    end: datetime,
    timeframe: str = "1Day",
) -> AsyncIterator[Bar]:
    """Paginate through Alpaca bars endpoint, yielding Bar objects."""
    params = {
        "symbols": symbol,
        "timeframe": timeframe,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "limit": 1000,
        "adjustment": "all",  # corporate-action adjusted
        "feed": "iex",        # free tier feed
    }
    next_token = None

    while True:
        if next_token:
            params["page_token"] = next_token

        resp = await client.get(f"{BASE_URL}/stocks/bars", params=params)
        resp.raise_for_status()
        data = resp.json()

        for bar_data in data.get("bars", {}).get(symbol, []):
            yield Bar(
                symbol=symbol,
                timestamp=datetime.fromisoformat(bar_data["t"].replace("Z", "+00:00")),
                open=float(bar_data["o"]),
                high=float(bar_data["h"]),
                low=float(bar_data["l"]),
                close=float(bar_data["c"]),
                volume=int(bar_data["v"]),
                vwap=float(bar_data["vw"]) if "vw" in bar_data else None,
                trade_count=int(bar_data["n"]) if "n" in bar_data else None,
            )

        next_token = data.get("next_page_token")
        if not next_token:
            break


async def fetch_latest_quote(
    client: httpx.AsyncClient,
    symbol: str,
) -> Quote | None:
    """Fetch the most recent quote for a symbol."""
    try:
        resp = await client.get(
            f"{BASE_URL}/stocks/quotes/latest",
            params={"symbols": symbol, "feed": "iex"},
        )
        resp.raise_for_status()
        data = resp.json()
        q = data.get("quotes", {}).get(symbol)
        if not q:
            return None
        return Quote(
            symbol=symbol,
            timestamp=datetime.fromisoformat(q["t"].replace("Z", "+00:00")),
            bid_price=float(q["bp"]),
            ask_price=float(q["ap"]),
            bid_size=int(q["bs"]),
            ask_size=int(q["as"]),
        )
    except Exception as exc:
        logger.warning("Quote fetch failed for %s: %s", symbol, exc)
        return None


async def fetch_symbol_bars(
    symbol: str,
    start: datetime,
    end: datetime,
    timeframe: str,
    semaphore: asyncio.Semaphore,
) -> list[Bar]:
    async with semaphore:
        async with httpx.AsyncClient(headers=_get_headers(), timeout=30) as client:
            bars = []
            async for bar in fetch_bars(client, symbol, start, end, timeframe):
                bars.append(bar)
            logger.info("Fetched %d bars for %s", len(bars), symbol)
            return bars
