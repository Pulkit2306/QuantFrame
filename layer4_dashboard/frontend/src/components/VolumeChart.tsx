import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'
import type { Bar as BarData } from '../api'

interface Props {
  bars: BarData[]
}

export default function VolumeChart({ bars }: Props) {
  const data = bars.slice(-90).map(b => ({
    date:   b.ts.slice(0, 10),
    volume: +(b.volume / 1_000_000).toFixed(2),
  }))

  return (
    <div className="bg-dark-800 border border-dark-600 rounded-lg p-4">
      <h2 className="text-sm text-slate-400 uppercase tracking-widest mb-4">
        Volume (M shares, last 90 days)
      </h2>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} margin={{ top: 4, right: 8, left: 8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#22222f" vertical={false} />
          <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 9 }} tickFormatter={d => d.slice(5)} interval={14} />
          <YAxis tick={{ fill: '#64748b', fontSize: 10 }} tickFormatter={v => `${v}M`} />
          <Tooltip
            contentStyle={{ background: '#111118', border: '1px solid #22222f', borderRadius: 6 }}
            labelStyle={{ color: '#94a3b8' }}
            formatter={(v: number) => [`${v}M`, 'Volume']}
          />
          <Bar dataKey="volume" fill="#4488ff" opacity={0.7} radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
