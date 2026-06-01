import { ReactNode, useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

interface Props {
  title: string
  icon?: string
  children: ReactNode
  defaultOpen?: boolean
}

export default function AgentCard({ title, icon, children, defaultOpen = false }: Props) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
      <button
        className="w-full flex items-center justify-between px-4 py-3 bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
        onClick={() => setOpen(!open)}
      >
        <span className="flex items-center gap-2 font-medium text-sm text-slate-700 dark:text-slate-200">
          {icon && <span>{icon}</span>}
          {title}
        </span>
        {open ? <ChevronUp size={16} className="text-slate-400" /> : <ChevronDown size={16} className="text-slate-400" />}
      </button>
      {open && <div className="p-4 bg-white dark:bg-slate-900">{children}</div>}
    </div>
  )
}
