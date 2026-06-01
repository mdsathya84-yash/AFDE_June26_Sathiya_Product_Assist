import { useState } from 'react'
import { FileText, Download, RefreshCw, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAnalysisStore } from '../store/useAnalysisStore'
import SWOTGrid from '../components/SWOTGrid'
import RICETable from '../components/RICETable'
import OpportunityCard from '../components/OpportunityCard'
import { apiClient } from '../api/client'

const COMPREHENSIVE_QUERY =
  'Generate a complete strategic analysis including SWOT, feature priorities, growth opportunities, and a 12-month action plan based on all available sales data.'

export default function Report() {
  const { analysisResult, isLoading, runAnalysis } = useAnalysisStore()
  const [downloading, setDownloading] = useState(false)

  const handleGenerate = () => runAnalysis(COMPREHENSIVE_QUERY)

  const handleDownload = async (format: 'pdf' | 'json') => {
    setDownloading(true)
    try {
      const url = apiClient.getReportUrl(format)
      const response = await fetch(url)
      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Download failed')
      }
      const blob = await response.blob()
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `strategy_report.${format}`
      link.click()
      URL.revokeObjectURL(link.href)
      toast.success(`Report downloaded as ${format.toUpperCase()}`)
    } catch (e: unknown) {
      toast.error((e as Error).message)
    } finally {
      setDownloading(false)
    }
  }

  const r = analysisResult as Record<string, unknown> | null

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
      {/* Actions */}
      <div className="flex flex-wrap gap-3">
        <button
          onClick={handleGenerate}
          disabled={isLoading}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-xl text-sm font-medium transition-colors"
        >
          {isLoading ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}
          {isLoading ? 'Analyzing…' : 'Generate Full Report'}
        </button>
        <button
          onClick={() => handleDownload('pdf')}
          disabled={!r || downloading}
          className="flex items-center gap-2 px-4 py-2 bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white rounded-xl text-sm font-medium transition-colors"
        >
          {downloading ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
          Download PDF
        </button>
        <button
          onClick={() => handleDownload('json')}
          disabled={!r || downloading}
          className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded-xl text-sm font-medium transition-colors"
        >
          <FileText size={16} />
          Download JSON
        </button>
      </div>

      {!r && !isLoading && (
        <div className="flex flex-col items-center justify-center py-24 gap-4 text-center">
          <FileText size={48} className="text-slate-300" />
          <p className="text-slate-400 text-sm">Click "Generate Full Report" to run a comprehensive analysis.</p>
        </div>
      )}

      {isLoading && (
        <div className="flex flex-col items-center justify-center py-24 gap-4">
          <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
          <p className="text-sm text-slate-500">Running 6 parallel agents…</p>
        </div>
      )}

      {r && !isLoading && (
        <div className="space-y-8">
          {/* Executive Summary */}
          {r.executive_summary && (
            <section>
              <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-3 flex items-center gap-2">
                <span className="text-indigo-600">#</span> Executive Summary
              </h2>
              <div className="bg-indigo-50 dark:bg-indigo-950 border-l-4 border-indigo-500 rounded-r-xl p-5 text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                {String(r.executive_summary)}
              </div>
            </section>
          )}

          {/* SWOT */}
          {r.swot && (
            <section>
              <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-3 flex items-center gap-2">
                <span className="text-indigo-600">#</span> SWOT Analysis
              </h2>
              <SWOTGrid data={r.swot as Record<string, unknown>} />
            </section>
          )}

          {/* Feature Priorities */}
          {r.feature_priorities && (
            <section>
              <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-3 flex items-center gap-2">
                <span className="text-indigo-600">#</span> Feature Prioritization
              </h2>
              <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
                <RICETable
                  features={((r.feature_priorities as Record<string, unknown>).prioritized_features as Parameters<typeof RICETable>[0]['features'] | undefined) || []}
                />
              </div>
            </section>
          )}

          {/* Opportunities */}
          {r.opportunities && (
            <section>
              <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-3 flex items-center gap-2">
                <span className="text-indigo-600">#</span> Opportunity Scoring
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {(((r.opportunities as Record<string, unknown>).top_opportunities as unknown[] | undefined) || []).map((opp, i) => (
                  <OpportunityCard key={i} opportunity={opp as Parameters<typeof OpportunityCard>[0]['opportunity']} />
                ))}
              </div>
            </section>
          )}

          {/* Action Plan */}
          {r.strategy && (
            <section>
              <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-3 flex items-center gap-2">
                <span className="text-indigo-600">#</span> Strategic Action Plan
              </h2>
              <div className="space-y-4">
                {(['90_days', '6_months', '12_months'] as const).map((horizon) => {
                  const plan = (r.strategy as Record<string, unknown>).action_plan as Record<string, unknown> | undefined
                  const actions = (plan?.[horizon] as Array<{ action: string; owner: string; kpi: string }> | undefined) || []
                  const labels: Record<string, string> = { '90_days': '⏱ 90-Day', '6_months': '📅 6-Month', '12_months': '🎯 12-Month' }
                  return actions.length ? (
                    <div key={horizon} className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
                      <h3 className="font-semibold text-sm text-slate-700 dark:text-slate-200 mb-3">{labels[horizon]} Actions</h3>
                      <div className="space-y-2">
                        {actions.map((a, i) => (
                          <div key={i} className="flex gap-3 text-sm">
                            <span className="flex-shrink-0 w-6 h-6 bg-indigo-100 dark:bg-indigo-900 rounded-full flex items-center justify-center text-xs font-bold text-indigo-600 dark:text-indigo-300">{i + 1}</span>
                            <div>
                              <p className="font-medium text-slate-800 dark:text-slate-200">{a.action}</p>
                              <p className="text-xs text-slate-400 mt-0.5">Owner: {a.owner} · KPI: {a.kpi}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : null
                })}
              </div>
            </section>
          )}

          {/* Product Roadmap */}
          {r.strategy && (
            <section>
              <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-3 flex items-center gap-2">
                <span className="text-indigo-600">#</span> Product Roadmap
              </h2>
              <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50 dark:bg-slate-700">
                    <tr>
                      {['Quarter', 'Product', 'Initiative', 'Priority'].map((h) => (
                        <th key={h} className="text-left px-4 py-3 font-semibold text-slate-600 dark:text-slate-300 text-xs">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(((r.strategy as Record<string, unknown>).product_roadmap as Array<{ quarter: string; product: string; initiative: string; priority: string }> | undefined) || []).map((item, i) => (
                      <tr key={i} className="border-t border-slate-100 dark:border-slate-700">
                        <td className="px-4 py-3 text-xs font-medium">{item.quarter}</td>
                        <td className="px-4 py-3 text-xs">{item.product}</td>
                        <td className="px-4 py-3 text-xs">{item.initiative}</td>
                        <td className="px-4 py-3 text-xs">
                          <span className={`px-2 py-0.5 rounded-full font-bold text-xs ${
                            item.priority === 'P0' ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300' :
                            item.priority === 'P1' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300' :
                            'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                          }`}>{item.priority}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  )
}
