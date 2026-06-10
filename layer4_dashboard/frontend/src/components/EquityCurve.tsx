import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'
import type { Bar } from '../api'

interface Props {
  bars: Bar[]
  symbol: string
}

export default function EquityCurve({ bars, symbol }: Props) {
  // Compute equity curve: $100k invested in this symbol
  const initial = bars.length > 0 ? bars[0].close : 1
  const data = bars.map(b => ({
    date:   b.ts.slice(0, 10),
    equity: +(100000 * (b.close / initial)).toFixed(2),
    close:  +b.close,
  }))

  const last   = data.at(-1)?.equity ?? 0
  const first  = data.at(0)?.equity  ?? 0
  const up     = last >= first

  return (
    <div className="bg-dark-800 border border-dark-600 rounded-lg p-4">
      <h2 className="text-sm text-slate-400 uppercase tracking-widest mb-4">
        {symbol} — Equity Curve ($100k invested)
      </h2>
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={data} margin={{ top: 4, right: 8, left: 8, bottom: 0 }}>
          <defs>
            <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor={up ? '#00ff88' : '#ff4466'} stopOpacity={0.25} />
              <stop offset="95%" stopColor={up ? '#00ff88' : '#ff4466'} stopOpacity={0}    />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#22222f" />
          <XAxis
            dataKey="date"
            tick={{ fill: '#64748b', fontSize: 10 }}
            tickFormatter={d => d.slice(0, 7)}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fill: '#64748b', fontSize: 10 }}
            tickFormatter={v => `$${(v / 1000).toFixed(0)}k`}
            domain={['auto', 'auto']}
          />
          <Tooltip
            contentStyle={{ background: '#111118', border: '1px solid #22222f', borderRadius: 6 }}
            labelStyle={{ color: '#94a3b8' }}
            itemStyle={{ color: up ? '#00ff88' : '#ff4466' }}
            formatter={(v: number) => [`$${v.toLocaleString()}`, 'Equity']}
          />
          <Area
            type="monotone"
            dataKey="equity"
            stroke={up ? '#00ff88' : '#ff4466'}
            strokeWidth={2}
            fill="url(#equityGrad)"
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
