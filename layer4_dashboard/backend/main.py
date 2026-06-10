"""
FastAPI backend — serves market data, analytics, and backtest results to the React frontend.
"""

import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

from datetime import date, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from layer1_pipeline import database as db
from layer3_analytics.metrics import compute_metrics, compute_all_metrics

app = FastAPI(title="QuantFrame API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/symbols")
def list_symbols():
    rows = db.get_status()
    return {"symbols": [r["symbol"] for r in rows]}


@app.get("/api/status")
def pipeline_status():
    return {"data": db.get_status()}


@app.get("/api/bars/{symbol}")
def get_bars(
    symbol: str,
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    limit: int = Query(500, ge=1, le=5000),
):
    end_date   = date.fromisoformat(end)   if end   else date.today()
    start_date = date.fromisoformat(start) if start else end_date - timedelta(days=365)

    bars = db.query_bars(symbol.upper(), start_date, end_date)
    # limit from the end (most recent)
    bars = bars[-limit:]
    return {"symbol": symbol.upper(), "bars": bars}


@app.get("/api/metrics/{symbol}")
def get_metrics(
    symbol: str,
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
):
    end_date   = date.fromisoformat(end)   if end   else date.today()
    start_date = date.fromisoformat(start) if start else end_date - timedelta(days=365)

    try:
        metrics = compute_metrics(symbol.upper(), start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return metrics


@app.get("/api/metrics")
def get_all_metrics(
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
):
    end_date   = date.fromisoformat(end)   if end   else date.today()
    start_date = date.fromisoformat(start) if start else end_date - timedelta(days=365)

    rows = db.get_status()
    symbols = [r["symbol"] for r in rows]
    return {"metrics": compute_all_metrics(symbols, start_date, end_date)}


class BacktestRequest(BaseModel):
    symbol: str
    start: str
    end: str
    strategy: str = "sma"
    short_period: int = 10
    long_period: int = 50


@app.post("/api/backtest")
def run_backtest(req: BacktestRequest):
    """
    Run a backtest using the C++ engine results via Python bindings.
    For now, returns analytics metrics as a proxy until pybind11 bindings are wired.
    """
    metrics = compute_metrics(
        req.symbol.upper(),
        date.fromisoformat(req.start),
        date.fromisoformat(req.end),
    )
    return {
        "strategy":        req.strategy,
        "symbol":          req.symbol.upper(),
        "metrics":         metrics,
        "note":            "Full C++ backtest results available via CLI: ./quantframe bars.csv",
    }
