import { useEffect } from 'react'
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, RadarChart,
  Radar, PolarGrid, PolarAngleAxis, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import { TrendingUp, DollarSign, Star, Package } from 'lucide-react'
import { useAnalysisStore } from '../store/useAnalysisStore'
import LoadingSpinner from '../components/LoadingSpinner'

const COLORS = ['#6366F1', '#0EA5E9', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6']

const fmt = (n: number) =>
  n >= 1_000_000 ? `$${(n / 1_000_000).toFixed(1)}M` : n >= 1_000 ? `$${(n / 1_000).toFixed(0)}K` : `$${n.toFixed(0)}`

function KPICard({ label, value, sub, icon: Icon, color }: { label: string; value: string; sub?: string; icon: React.ElementType; color: string }) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-5 border border-slate-200 dark:border-slate-700 flex items-start gap-4">
      <div className={`p-3 rounded-xl ${color}`}>
        <Icon size={20} className="text-white" />
      </div>
      <div>
        <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">{label}</p>
        <p className="text-2xl font-bold text-slate-800 dark:text-slate-100 mt-0.5">{value}</p>
        {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

function SkeletonCard() {
  return <div className="bg-slate-200 dark:bg-slate-700 rounded-xl h-24 animate-pulse" />
}

function SkeletonChart() {
  return <div className="bg-slate-200 dark:bg-slate-700 rounded-xl h-64 animate-pulse" />
}

export default function Dashboard() {
  const { dashboardData, isDashboardLoading, fetchDashboard } = useAnalysisStore()

  useEffect(() => {
    fetchDashboard()
    const interval = setInterval(fetchDashboard, 60_000)
    return () => clearInterval(interval)
  }, [fetchDashboard])

  if (isDashboardLoading && !dashboardData) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <SkeletonCard key={i} />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {[...Array(4)].map((_, i) => <SkeletonChart key={i} />)}
        </div>
      </div>
    )
  }

  const d = dashboardData
  if (!d) return <div className="p-8 text-center text-slate-400">No data available</div>

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="Total Revenue" value={fmt(d.total_revenue)} icon={DollarSign} color="bg-indigo-600" />
        <KPICard label="Total Profit" value={fmt(d.total_profit)} sub={`${((d.total_profit / d.total_revenue) * 100).toFixed(1)}% margin`} icon={TrendingUp} color="bg-emerald-600" />
        <KPICard label="Avg Rating" value={d.avg_customer_rating.toFixed(2)} sub="out of 5" icon={Star} color="bg-amber-500" />
        <KPICard label="Units Sold" value={d.total_units_sold.toLocaleString()} icon={Package} color="bg-sky-600" />
      </div>

      {/* Revenue Trend + By Category */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 bg-white dark:bg-slate-800 rounded-xl p-5 border border-slate-200 dark:border-slate-700">
          <h3 className="font-semibold text-sm text-slate-700 dark:text-slate-200 mb-4">Revenue & Profit Trend</h3>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={d.monthly_trend}>
              <defs>
                <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366F1" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6366F1" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="profGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={(v) => fmt(v)} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v: number) => fmt(v)} />
              <Legend />
              <Area type="monotone" dataKey="revenue" stroke="#6366F1" fill="url(#revGrad)" name="Revenue" />
              <Area type="monotone" dataKey="profit" stroke="#10B981" fill="url(#profGrad)" name="Profit" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-xl p-5 border border-slate-200 dark:border-slate-700">
          <h3 className="font-semibold text-sm text-slate-700 dark:text-slate-200 mb-4">Revenue by Category</h3>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={d.revenue_by_category} dataKey="revenue" nameKey="category" cx="50%" cy="50%" outerRadius={80} label={({ category }) => category}>
                {d.revenue_by_category.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip formatter={(v: number) => fmt(v)} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Revenue by Product + Region Radar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 bg-white dark:bg-slate-800 rounded-xl p-5 border border-slate-200 dark:border-slate-700">
          <h3 className="font-semibold text-sm text-slate-700 dark:text-slate-200 mb-4">Revenue by Product</h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={[...d.revenue_by_product].sort((a, b) => b.revenue - a.revenue)} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis type="number" tickFormatter={(v) => fmt(v)} tick={{ fontSize: 10 }} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 10 }} width={90} />
              <Tooltip formatter={(v: number) => fmt(v)} />
              <Bar dataKey="revenue" fill="#6366F1" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-xl p-5 border border-slate-200 dark:border-slate-700">
          <h3 className="font-semibold text-sm text-slate-700 dark:text-slate-200 mb-4">Revenue by Region</h3>
          <ResponsiveContainer width="100%" height={240}>
            <RadarChart data={d.revenue_by_region}>
              <PolarGrid />
              <PolarAngleAxis dataKey="region" tick={{ fontSize: 11 }} />
              <Radar name="Revenue" dataKey="revenue" stroke="#6366F1" fill="#6366F1" fillOpacity={0.3} />
              <Tooltip formatter={(v: number) => fmt(v)} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Products Table */}
      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-700">
          <h3 className="font-semibold text-sm text-slate-700 dark:text-slate-200">Top Products</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-slate-50 dark:bg-slate-700">
              <tr>
                {['Product', 'Category', 'Units', 'Revenue', 'Margin', 'Rating', 'Returns'].map((h) => (
                  <th key={h} className="text-left px-4 py-3 font-semibold text-slate-600 dark:text-slate-300">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {d.top_products.map((p: Record<string, unknown>, i) => (
                <tr key={i} className="border-t border-slate-100 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-750">
                  <td className="px-4 py-3 font-medium text-slate-800 dark:text-slate-200">{String(p.name)}</td>
                  <td className="px-4 py-3 text-slate-500">{String(p.category)}</td>
                  <td className="px-4 py-3">{Number(p.units).toLocaleString()}</td>
                  <td className="px-4 py-3">{fmt(Number(p.revenue))}</td>
                  <td className="px-4 py-3">
                    <span className="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300 font-medium">
                      {Number(p.margin_pct).toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="flex items-center gap-1">
                      <Star size={12} className="text-amber-400 fill-amber-400" />
                      {Number(p.rating).toFixed(1)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-500">{Number(p.returns).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
