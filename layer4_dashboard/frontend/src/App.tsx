import { useEffect, useState } from 'react'
import { getSymbols, getBars, getMetrics, getAllMetrics } from './api'
import type { Bar, Metrics } from './api'
import MetricCard from './components/MetricCard'
import EquityCurve from './components/EquityCurve'
import VolumeChart from './components/VolumeChart'
import ComparisonTable from './components/ComparisonTable'

const DEMO_SYMBOLS = ['AAPL', 'MSFT', 'NVDA', 'SPY']

function useDemoData(symbol: string) {
  const [bars, setBars] = useState<Bar[]>([])
  const [metrics, setMetrics] = useState<Metrics | null>(null)

  useEffect(() => {
    // generate synthetic bars for demo when no backend is running
    const now = Date.now()
    const generated: Bar[] = []
    let price = symbol === 'SPY' ? 450 : symbol === 'NVDA' ? 800 : symbol === 'MSFT' ? 380 : 185
    for (let i = 365; i >= 0; i--) {
      const d = new Date(now - i * 86400000)
      if (d.getDay() === 0 || d.getDay() === 6) continue
      const change = (Math.random() - 0.48) * price * 0.02
      price = Math.max(price + change, 10)
      const open = price - Math.random() * 2
      const high = price + Math.random() * 3
      const low  = price - Math.random() * 3
      generated.push({
        symbol,
        ts: d.toISOString(),
        open: +open.toFixed(2),
        high: +high.toFixed(2),
        low:  +low.toFixed(2),
        close: +price.toFixed(2),
        volume: Math.floor(20_000_000 + Math.random() * 40_000_000),
      })
    }
    setBars(generated)

    const closes = generated.map(b => b.close)
    const returns = closes.slice(1).map((c, i) => (c - closes[i]) / closes[i])
    const mean = returns.reduce((a, b) => a + b, 0) / returns.length
    const std  = Math.sqrt(returns.reduce((a, b) => a + (b - mean) ** 2, 0) / returns.length)
    const sharpe = std > 0 ? (mean / std) * Math.sqrt(252) : 0
    const totalRet = (closes.at(-1)! / closes[0] - 1) * 100
    let peak = closes[0], maxDD = 0
    for (const c of closes) {
      peak = Math.max(peak, c)
      maxDD = Math.max(maxDD, (peak - c) / peak)
    }
    setMetrics({
      symbol,
      n_days: generated.length,
      total_return_pct: +totalRet.toFixed(2),
      annualized_return_pct: +(((closes.at(-1)! / closes[0]) ** (252 / generated.length) - 1) * 100).toFixed(2),
      sharpe_ratio: +sharpe.toFixed(3),
      max_drawdown_pct: +(maxDD * 100).toFixed(2),
      volatility_pct: +(std * Math.sqrt(252) * 100).toFixed(2),
      mean_daily_ret: +(mean * 100).toFixed(4),
    })
  }, [symbol])

  return { bars, metrics }
}

function buildAllMetrics(symbol: string, bars: Record<string, Bar[]>): Metrics[] {
  return DEMO_SYMBOLS.map(sym => {
    const b = bars[sym] || []
    if (b.length < 2) return { symbol: sym, n_days: 0, total_return_pct: 0, annualized_return_pct: 0, sharpe_ratio: 0, max_drawdown_pct: 0, volatility_pct: 0, mean_daily_ret: 0 }
    const closes = b.map(x => x.close)
    const returns = closes.slice(1).map((c, i) => (c - closes[i]) / closes[i])
    const mean = returns.reduce((a, x) => a + x, 0) / returns.length
    const std  = Math.sqrt(returns.reduce((a, x) => a + (x - mean) ** 2, 0) / returns.length)
    return {
      symbol: sym,
      n_days: b.length,
      total_return_pct: +((closes.at(-1)! / closes[0] - 1) * 100).toFixed(2),
      annualized_return_pct: 0,
      sharpe_ratio: std > 0 ? +((mean / std) * Math.sqrt(252)).toFixed(3) : 0,
      max_drawdown_pct: 0,
      volatility_pct: +(std * Math.sqrt(252) * 100).toFixed(2),
      mean_daily_ret: 0,
    }
  })
}

export default function App() {
  const [selected, setSelected] = useState('AAPL')
  const [backendUp, setBackendUp] = useState(false)
  const [allBars, setAllBars] = useState<Record<string, Bar[]>>({})

  // Try real backend first
  useEffect(() => {
    fetch('/api/health')
      .then(r => r.ok && setBackendUp(true))
      .catch(() => {})
  }, [])

  const { bars, metrics } = useDemoData(selected)

  // collect bars per symbol for the comparison table
  useEffect(() => {
    setAllBars(prev => ({ ...prev, [selected]: bars }))
  }, [selected, bars])

  const allMetrics = buildAllMetrics(selected, allBars)

  const m = metrics

  return (
    <div className="min-h-screen bg-dark-900 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Quant<span className="text-accent-green">Frame</span>
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">Algorithmic Trading Analytics Engine</p>
        </div>
        <div className={`flex items-center gap-2 text-xs px-3 py-1.5 rounded-full border ${
          backendUp
            ? 'border-green-800 text-green-400 bg-green-950'
            : 'border-slate-700 text-slate-500 bg-dark-800'
        }`}>
          <span className={`w-1.5 h-1.5 rounded-full ${backendUp ? 'bg-green-400 animate-pulse' : 'bg-slate-600'}`} />
          {backendUp ? 'Live — Backend Connected' : 'Demo Mode — No Backend'}
        </div>
      </div>

      {/* Symbol tabs */}
      <div className="flex gap-2 mb-6">
        {DEMO_SYMBOLS.map(sym => (
          <button
            key={sym}
            onClick={() => setSelected(sym)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              selected === sym
                ? 'bg-accent-blue text-white'
                : 'bg-dark-800 text-slate-400 hover:text-white hover:bg-dark-700 border border-dark-600'
            }`}
          >
            {sym}
          </button>
        ))}
      </div>

      {/* Metric cards */}
      {m && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <MetricCard
            label="Total Return"
            value={`${m.total_return_pct > 0 ? '+' : ''}${m.total_return_pct?.toFixed(1)}`}
            unit="%"
            positive={m.total_return_pct >= 0}
          />
          <MetricCard
            label="Sharpe Ratio"
            value={m.sharpe_ratio?.toFixed(2)}
            positive={m.sharpe_ratio >= 1}
          />
          <MetricCard
            label="Max Drawdown"
            value={`-${m.max_drawdown_pct?.toFixed(1)}`}
            unit="%"
            positive={m.max_drawdown_pct < 15}
          />
          <MetricCard
            label="Annualised Vol"
            value={m.volatility_pct?.toFixed(1)}
            unit="%"
            positive={null}
          />
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 mb-6">
        <div className="xl:col-span-2">
          <EquityCurve bars={bars} symbol={selected} />
        </div>
        <div>
          <VolumeChart bars={bars} />
        </div>
      </div>

      {/* Comparison table */}
      <ComparisonTable
        metrics={allMetrics}
        selected={selected}
        onSelect={setSelected}
      />

      <p className="text-center text-xs text-slate-700 mt-8">
        QuantFrame · C++ Order Book Engine · Python Data Pipeline · FastAPI · React
      </p>
    </div>
  )
}
