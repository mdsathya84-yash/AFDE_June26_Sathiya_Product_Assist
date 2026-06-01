import { useState } from 'react'
import { ArrowUpDown } from 'lucide-react'

interface Feature {
  feature: string
  category: string
  reach_score: number
  impact_score: number
  confidence_pct: number
  effort_weeks: number
  rice_score: number
  rationale?: string
}

interface Props { features: Feature[] }

export default function RICETable({ features }: Props) {
  const [sort, setSort] = useState<'rice_score' | 'impact_score'>('rice_score')

  const sorted = [...(features || [])].sort((a, b) => b[sort] - a[sort])

  const scoreColor = (score: number) => {
    if (score > 200) return 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
    if (score > 100) return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'
    return 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-slate-200 dark:border-slate-700">
            <th className="text-left py-2 px-2 font-semibold text-slate-600 dark:text-slate-300">Feature</th>
            <th className="text-center py-2 px-2 font-semibold text-slate-600 dark:text-slate-300">Reach</th>
            <th className="text-center py-2 px-2 font-semibold text-slate-600 dark:text-slate-300">Impact</th>
            <th className="text-center py-2 px-2 font-semibold text-slate-600 dark:text-slate-300">Conf%</th>
            <th className="text-center py-2 px-2 font-semibold text-slate-600 dark:text-slate-300">Effort</th>
            <th
              className="text-center py-2 px-2 font-semibold text-slate-600 dark:text-slate-300 cursor-pointer hover:text-indigo-600"
              onClick={() => setSort('rice_score')}
            >
              <span className="flex items-center gap-1 justify-center">RICE <ArrowUpDown size={10} /></span>
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((f, i) => (
            <tr key={i} className="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800">
              <td className="py-2 px-2">
                <div className="font-medium text-slate-800 dark:text-slate-200">{f.feature}</div>
                <div className="text-slate-400 text-xs">{f.category}</div>
              </td>
              <td className="text-center py-2 px-2">{f.reach_score}</td>
              <td className="text-center py-2 px-2">{f.impact_score}</td>
              <td className="text-center py-2 px-2">{f.confidence_pct}%</td>
              <td className="text-center py-2 px-2">{f.effort_weeks}w</td>
              <td className="text-center py-2 px-2">
                <span className={`px-2 py-0.5 rounded-full font-bold ${scoreColor(f.rice_score)}`}>
                  {Math.round(f.rice_score)}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
