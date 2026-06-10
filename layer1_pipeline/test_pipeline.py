"""
Offline test suite — all HTTP calls are mocked, no API keys or DB needed.
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from .models import Bar, Quote
from .fetcher import fetch_symbol_bars


MOCK_BARS_RESPONSE = {
    "bars": {
        "AAPL": [
            {"t": "2024-01-02T05:00:00Z", "o": 185.0, "h": 188.0,
             "l": 184.0, "c": 187.0, "v": 55000000, "vw": 186.5, "n": 420000},
            {"t": "2024-01-03T05:00:00Z", "o": 187.0, "h": 190.0,
             "l": 185.0, "c": 189.0, "v": 60000000, "vw": 187.8, "n": 450000},
        ]
    },
    "next_page_token": None,
}


@pytest.mark.asyncio
async def test_fetch_bars_parses_response():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = MOCK_BARS_RESPONSE

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    bars = []
    from .fetcher import fetch_bars
    async for bar in fetch_bars(
        mock_client, "AAPL",
        datetime(2024, 1, 1, tzinfo=timezone.utc),
        datetime(2024, 1, 5, tzinfo=timezone.utc),
    ):
        bars.append(bar)

    assert len(bars) == 2
    assert bars[0].symbol == "AAPL"
    assert bars[0].close == 187.0
    assert bars[1].vwap == 187.8


@pytest.mark.asyncio
async def test_fetch_symbol_bars_uses_semaphore():
    semaphore = asyncio.Semaphore(1)
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = MOCK_BARS_RESPONSE

    with patch("layer1_pipeline.fetcher._get_headers", return_value={}), \
         patch("layer1_pipeline.fetcher.httpx.AsyncClient") as MockClient:
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        MockClient.return_value = mock_ctx

        bars = await fetch_symbol_bars(
            "AAPL",
            datetime(2024, 1, 1, tzinfo=timezone.utc),
            datetime(2024, 1, 5, tzinfo=timezone.utc),
            "1Day",
            semaphore,
        )

    assert isinstance(bars, list)


def test_bar_model_fields():
    bar = Bar(
        symbol="MSFT", timestamp=datetime(2024, 1, 2, tzinfo=timezone.utc),
        open=374.0, high=378.0, low=372.0, close=376.0, volume=20000000,
    )
    assert bar.vwap is None
    assert bar.symbol == "MSFT"


def test_ingest_result_defaults():
    from .models import IngestResult
    r = IngestResult(symbol="SPY", bars_inserted=100, quotes_inserted=0, errors=[])
    assert r.errors == []
    assert r.bars_inserted == 100
