interface Opportunity {
  opportunity: string
  score: number
  category: string
  region: string
  rationale: string
  investment_required: string
  expected_return: string
}

interface Props { opportunity: Opportunity }

const tag = (label: string, level: string) => {
  const color = level === 'low' ? 'bg-green-100 text-green-700' : level === 'medium' ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'
  return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${color}`}>{label}: {level}</span>
}

export default function OpportunityCard({ opportunity: opp }: Props) {
  const pct = Math.min(100, Math.max(0, opp.score))
  const color = pct >= 70 ? '#10B981' : pct >= 50 ? '#F59E0B' : '#EF4444'

  return (
    <div className="flex gap-4 p-3 border border-slate-200 dark:border-slate-700 rounded-xl hover:shadow-sm transition-shadow">
      <div className="flex flex-col items-center justify-center min-w-[52px]">
        <div className="text-2xl font-bold" style={{ color }}>{Math.round(pct)}</div>
        <div className="text-xs text-slate-400">score</div>
      </div>
      <div className="flex-1 min-w-0">
        <div className="font-semibold text-sm text-slate-800 dark:text-slate-200 truncate">{opp.opportunity}</div>
        <div className="text-xs text-slate-400 mb-2">{opp.category} · {opp.region}</div>
        <div className="flex flex-wrap gap-1.5 mb-2">
          {tag('Investment', opp.investment_required)}
          {tag('Return', opp.expected_return)}
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2">{opp.rationale}</p>
      </div>
    </div>
  )
}
