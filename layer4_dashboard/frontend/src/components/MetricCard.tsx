interface Props {
  label: string
  value: string | number
  unit?: string
  positive?: boolean | null  // null = neutral
}

export default function MetricCard({ label, value, unit = '', positive = null }: Props) {
  const color =
    positive === null ? 'text-slate-200' :
    positive          ? 'text-green-400'  : 'text-red-400'

  return (
    <div className="bg-dark-800 border border-dark-600 rounded-lg p-4">
      <p className="text-xs text-slate-500 uppercase tracking-widest mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>
        {value}{unit}
      </p>
    </div>
  )
}
