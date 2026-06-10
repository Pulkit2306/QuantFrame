import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export interface Bar {
  symbol: string
  ts: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  vwap?: number
}

export interface Metrics {
  symbol: string
  n_days: number
  total_return_pct: number
  annualized_return_pct: number
  sharpe_ratio: number
  max_drawdown_pct: number
  volatility_pct: number
  mean_daily_ret: number
  error?: string
}

export interface SymbolStatus {
  symbol: string
  bar_count: number
  earliest: string
  latest: string
}

export const getSymbols   = ()                          => api.get<{ symbols: string[] }>('/symbols').then(r => r.data.symbols)
export const getStatus    = ()                          => api.get<{ data: SymbolStatus[] }>('/status').then(r => r.data.data)
export const getBars      = (sym: string, days = 365)   => {
  const end   = new Date().toISOString().slice(0, 10)
  const start = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10)
  return api.get<{ bars: Bar[] }>(`/bars/${sym}`, { params: { start, end } }).then(r => r.data.bars)
}
export const getMetrics   = (sym: string)               => api.get<Metrics>(`/metrics/${sym}`).then(r => r.data)
export const getAllMetrics = ()                          => api.get<{ metrics: Metrics[] }>('/metrics').then(r => r.data.metrics)
