interface SWOTData {
  strengths?: string[]
  weaknesses?: string[]
  opportunities?: string[]
  threats?: string[]
  swot_summary?: string
}

interface Props { data: SWOTData }

const Cell = ({ title, items, bg, border, icon }: { title: string; items: string[]; bg: string; border: string; icon: string }) => (
  <div className={`${bg} ${border} border rounded-xl p-4`}>
    <h4 className="font-semibold text-sm mb-3">{icon} {title}</h4>
    <ul className="space-y-1.5">
      {(items || []).map((item, i) => (
        <li key={i} className="text-xs flex gap-2">
          <span className="mt-0.5 text-slate-400">•</span>
          <span>{item}</span>
        </li>
      ))}
    </ul>
  </div>
)

export default function SWOTGrid({ data }: Props) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <Cell title="Strengths" items={data.strengths || []} bg="bg-green-50 dark:bg-green-950" border="border-green-200 dark:border-green-800" icon="💪" />
        <Cell title="Weaknesses" items={data.weaknesses || []} bg="bg-red-50 dark:bg-red-950" border="border-red-200 dark:border-red-800" icon="⚠️" />
        <Cell title="Opportunities" items={data.opportunities || []} bg="bg-blue-50 dark:bg-blue-950" border="border-blue-200 dark:border-blue-800" icon="🚀" />
        <Cell title="Threats" items={data.threats || []} bg="bg-yellow-50 dark:bg-yellow-950" border="border-yellow-200 dark:border-yellow-800" icon="⚡" />
      </div>
      {data.swot_summary && (
        <p className="text-xs text-slate-600 dark:text-slate-400 italic border-l-2 border-indigo-300 pl-3">{data.swot_summary}</p>
      )}
    </div>
  )
}
