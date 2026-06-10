import type { Metrics } from '../api'

interface Props {
  metrics: Metrics[]
  onSelect: (symbol: string) => void
  selected: string
}

function colored(val: number, good: 'high' | 'low') {
  const isGood = good === 'high' ? val > 0 : val < 10
  return isGood ? 'text-green-400' : 'text-red-400'
}

export default function ComparisonTable({ metrics, onSelect, selected }: Props) {
  const valid = metrics.filter(m => !m.error)

  return (
    <div className="bg-dark-800 border border-dark-600 rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-dark-600">
        <h2 className="text-sm text-slate-400 uppercase tracking-widest">Symbol Comparison</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-slate-500 uppercase tracking-wide border-b border-dark-600">
              <th className="text-left px-4 py-2">Symbol</th>
              <th className="text-right px-4 py-2">Return %</th>
              <th className="text-right px-4 py-2">Sharpe</th>
              <th className="text-right px-4 py-2">Max DD %</th>
              <th className="text-right px-4 py-2">Vol %</th>
              <th className="text-right px-4 py-2">Days</th>
            </tr>
          </thead>
          <tbody>
            {valid.map(m => (
              <tr
                key={m.symbol}
                onClick={() => onSelect(m.symbol)}
                className={`border-b border-dark-700 cursor-pointer transition-colors ${
                  m.symbol === selected
                    ? 'bg-dark-600'
                    : 'hover:bg-dark-700'
                }`}
              >
                <td className="px-4 py-3 font-bold text-accent-blue">{m.symbol}</td>
                <td className={`px-4 py-3 text-right ${colored(m.total_return_pct, 'high')}`}>
                  {m.total_return_pct > 0 ? '+' : ''}{m.total_return_pct?.toFixed(1)}%
                </td>
                <td className={`px-4 py-3 text-right ${colored(m.sharpe_ratio, 'high')}`}>
                  {m.sharpe_ratio?.toFixed(2)}
                </td>
                <td className={`px-4 py-3 text-right ${colored(-m.max_drawdown_pct, 'high')}`}>
                  -{m.max_drawdown_pct?.toFixed(1)}%
                </td>
                <td className="px-4 py-3 text-right text-slate-300">
                  {m.volatility_pct?.toFixed(1)}%
                </td>
                <td className="px-4 py-3 text-right text-slate-500">{m.n_days}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
