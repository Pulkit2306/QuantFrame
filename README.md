# QuantFrame

A low-latency algorithmic trading backtesting and analytics engine. Built to demonstrate production-grade quant engineering across the full stack: systems programming, time-series data pipelines, SQL analytics, LLM integration, and a live web dashboard.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Data pipeline | Python 3.12+, asyncio, httpx, PostgreSQL 16 |
| Backtesting engine | C++20, CMake |
| Analytics + AI | Python, NumPy, Pandas, Anthropic Claude API |
| Dashboard | FastAPI, React 18, Vite, Recharts, Tailwind CSS |
| Infrastructure | Docker, Docker Compose |

---

## Project Structure

```
quantframe/
├── layer1_pipeline/        # Python data ingestion pipeline
├── layer2_engine/          # C++ order book + backtesting engine
├── layer3_analytics/       # SQL performance metrics + LLM advisor
├── layer4_dashboard/
│   ├── backend/            # FastAPI REST API
│   └── frontend/           # React dashboard
├── docker-compose.yml
├── Makefile
└── .env.example
```

---

## Prerequisites

- **Python 3.12+**
- **Node.js 18+** and npm
- **Docker Desktop** (for PostgreSQL)
- **C++ compiler** — GCC 11+ or Clang 14+ with CMake 3.16+ *(Layer 2 only, Linux/macOS/WSL)*
- **API keys** (free):
  - [Alpaca Markets](https://alpaca.markets) — free market data, no trading account needed
  - [Anthropic](https://console.anthropic.com) — for the LLM advisor (Layer 3 only)

---

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/YOUR_USERNAME/quantframe.git
cd quantframe
cp .env.example .env
```

Edit `.env` and fill in your API keys:

```env
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
ANTHROPIC_API_KEY=your_anthropic_key
```

### 2. Start PostgreSQL

Make sure Docker Desktop is running, then:

```bash
docker compose up -d postgres
```

Wait a few seconds for the health check to pass:

```bash
docker compose ps   # STATUS should show (healthy)
```

### 3. Install Python dependencies

```bash
pip install -r layer1_pipeline/requirements.txt \
            -r layer3_analytics/requirements.txt \
            -r layer4_dashboard/backend/requirements.txt
```

### 4. Initialize the database schema

```bash
python -m layer1_pipeline init-db
```

### 5. Ingest market data

```bash
# On Linux/macOS
export ALPACA_API_KEY=your_key
export ALPACA_SECRET_KEY=your_secret

# On Windows (PowerShell)
$env:ALPACA_API_KEY="your_key"
$env:ALPACA_SECRET_KEY="your_secret"

python -m layer1_pipeline ingest
```

This pulls 2 years of daily OHLCV data for the default watchlist (AAPL, MSFT, GOOGL, AMZN, NVDA, SPY, QQQ, TSLA). Takes ~30 seconds. Check the result:

```bash
python -m layer1_pipeline status
```

### 6. Start the API backend

```bash
# Linux/macOS
uvicorn layer4_dashboard.backend.main:app --reload --port 8000

# Windows (PowerShell) — uvicorn is in your user Scripts folder
python -m uvicorn layer4_dashboard.backend.main:app --reload --port 8000
```

### 7. Start the frontend dashboard

```bash
cd layer4_dashboard/frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

> **No API keys?** The dashboard runs in **demo mode** with synthetic data — just skip steps 3–5 and go straight to steps 6–7.

---

## Layer 1 — Data Pipeline CLI

```bash
# Initialize schema
python -m layer1_pipeline init-db

# Ingest all symbols in watchlist
python -m layer1_pipeline ingest

# Ingest specific symbols
python -m layer1_pipeline ingest AAPL TSLA

# Check ingestion status
python -m layer1_pipeline status

# Query bars for a symbol
python -m layer1_pipeline bars AAPL 2024-01-01 2024-12-31
```

Edit `layer1_pipeline/config.yaml` to change the watchlist, lookback period, or timeframe.

---

## Layer 2 — C++ Backtesting Engine

> Requires GCC/Clang + CMake. Use WSL on Windows.

```bash
# Build
cmake -S layer2_engine -B layer2_engine/build -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build layer2_engine/build --parallel

# Run tests
cd layer2_engine/build && ctest --output-on-failure

# Run a backtest (CSV format: timestamp_ns,open,high,low,close,volume)
./layer2_engine/build/quantframe data/bars.csv sma 10 50       # SMA crossover
./layer2_engine/build/quantframe data/bars.csv meanrev 20      # Mean reversion
```

Export bars to CSV from the pipeline:

```bash
python -m layer1_pipeline bars AAPL 2023-01-01 2024-12-31 | \
  python -c "import sys,json; rows=json.load(sys.stdin); \
  print('ts_ns,open,high,low,close,volume'); \
  [print(f'0,{r[\"open\"]},{r[\"high\"]},{r[\"low\"]},{r[\"close\"]},{r[\"volume\"]}') for r in rows]" \
  > data/aapl_bars.csv
```

---

## Layer 3 — Analytics CLI

```bash
# Single symbol metrics (Sharpe, drawdown, return, volatility)
python -m layer3_analytics metrics AAPL 2023-01-01 2024-12-31

# All watchlist symbols
python -m layer3_analytics all-metrics 2023-01-01 2024-12-31

# LLM-powered strategy advisor (requires ANTHROPIC_API_KEY)
python -m layer3_analytics advise AAPL 2023-01-01 2024-12-31 --params short=5,long=20

# Anomaly detection across all symbols (requires ANTHROPIC_API_KEY)
python -m layer3_analytics anomalies 2023-01-01 2024-12-31
```

---

## Layer 4 — Dashboard API

The FastAPI backend exposes these endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/symbols` | List ingested symbols |
| GET | `/api/status` | Bar count and date range per symbol |
| GET | `/api/bars/{symbol}` | OHLCV bars (`?start=YYYY-MM-DD&end=YYYY-MM-DD`) |
| GET | `/api/metrics/{symbol}` | Performance metrics for a symbol |
| GET | `/api/metrics` | Metrics for all symbols |
| POST | `/api/backtest` | Run a backtest |

Interactive docs available at **http://localhost:8000/docs** when the backend is running.

---

## Running Tests

```bash
# Python (Layer 1) — no API keys or database required
python -m pytest layer1_pipeline/test_pipeline.py -v

# C++ (Layer 2) — requires build step above
cd layer2_engine/build && ctest --output-on-failure
```

---

## Docker (Full Stack)

To run the backend and database together in Docker:

```bash
cp .env.example .env   # fill in keys
docker compose up -d postgres backend
```

The frontend is not containerized — run it locally with `npm run dev`.

---

## Watchlist Configuration

Edit `layer1_pipeline/config.yaml`:

```yaml
watchlist:
  - AAPL
  - MSFT
  - NVDA
  - SPY
  # add any US equity ticker here

pipeline:
  bars_timeframe: "1Day"      # 1Min, 5Min, 1Hour, 1Day
  default_lookback_days: 730  # 2 years
  max_concurrent_requests: 5
```

---

## Design Decisions

**Year-partitioned `bars` table** — Time-range queries skip irrelevant partitions entirely. BRIN index on `ts` instead of B-tree: bars are written sequentially so BRIN is ~100× smaller with equivalent scan performance.

**Idempotent ingestion** — `ON CONFLICT DO NOTHING` on all inserts. Re-running after a crash or failed deploy is always safe.

**Bounded concurrency** — `asyncio.Semaphore` caps parallel API requests without threads or a process pool.

**Pluggable strategies** — The C++ `Strategy` base class uses the Template Method pattern. Swapping SMA crossover for mean reversion requires zero engine changes.

**LLM prompt caching** — The Anthropic system prompt uses `cache_control: ephemeral`. Repeated analysis calls across many symbols hit the cache instead of re-tokenizing the full context.




## DEMO
Here is a demo of the frontend of my project: https://pulkit2306.github.io/QuantFrame/
