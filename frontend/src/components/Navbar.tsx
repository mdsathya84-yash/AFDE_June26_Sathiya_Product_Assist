import { useState, useEffect } from 'react'
import { NavLink } from 'react-router-dom'
import { BarChart3, MessageSquare, FileText, Sun, Moon, Zap } from 'lucide-react'

export default function Navbar() {
  const [dark, setDark] = useState(() => localStorage.getItem('theme') === 'dark')

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }, [dark])

  const navClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-300'
        : 'text-slate-600 hover:text-indigo-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800'
    }`

  return (
    <nav className="border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-14">
        <div className="flex items-center gap-2 font-bold text-indigo-600 dark:text-indigo-400">
          <Zap size={20} />
          <span className="hidden sm:inline">Strategy Assistant</span>
        </div>
        <div className="flex items-center gap-1">
          <NavLink to="/dashboard" className={navClass}>
            <BarChart3 size={16} /> Dashboard
          </NavLink>
          <NavLink to="/chat" className={navClass}>
            <MessageSquare size={16} /> Chat
          </NavLink>
          <NavLink to="/report" className={navClass}>
            <FileText size={16} /> Report
          </NavLink>
        </div>
        <button
          onClick={() => setDark(!dark)}
          className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
        >
          {dark ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>
    </nav>
  )
}
