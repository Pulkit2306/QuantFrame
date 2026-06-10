from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Bar:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None
    trade_count: Optional[int] = None


@dataclass
class Quote:
    symbol: str
    timestamp: datetime
    bid_price: float
    ask_price: float
    bid_size: int
    ask_size: int


@dataclass
class IngestResult:
    symbol: str
    bars_inserted: int
    quotes_inserted: int
    errors: list[str]
