import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { Send, Upload, Bot, User, Loader2, ChevronDown } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAnalysisStore } from '../store/useAnalysisStore'
import AgentCard from '../components/AgentCard'
import SWOTGrid from '../components/SWOTGrid'
import RICETable from '../components/RICETable'
import OpportunityCard from '../components/OpportunityCard'
import { apiClient } from '../api/client'

const CATEGORIES = ['Electronics', 'Wearables', 'Accessories', 'Audio', 'Smart Home']
const REGIONS = ['North', 'South', 'East', 'West', 'Central']

const STARTERS = [
  'What are the top performing products by revenue?',
  'Which region has the lowest customer satisfaction?',
  'What features should we prioritize for the next quarter?',
  'Generate a SWOT analysis for our Electronics category',
  'What are our biggest growth opportunities?',
]

export default function Chat() {
  const { chatMessages, isLoading, activeFilters, sendMessage, setFilters } = useAnalysisStore()
  const [input, setInput] = useState('')
  const [uploading, setUploading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages, isLoading])

  const handleSend = async () => {
    const msg = input.trim()
    if (!msg || isLoading) return
    setInput('')
    await sendMessage(msg)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') handleSend()
  }

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    if (!files.length) return
    setUploading(true)
    try {
      const res = await apiClient.ingestFiles(files)
      toast.success(`Uploaded ${res.chunks_ingested} chunks`)
    } catch {
      // error toast handled by axios interceptor
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  const toggleFilter = (type: 'categories' | 'regions', value: string) => {
    const current = activeFilters[type]
    const updated = current.includes(value) ? current.filter((v) => v !== value) : [...current, value]
    setFilters({ [type]: updated })
  }

  return (
    <div className="flex h-[calc(100vh-56px)]">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 border-r border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 flex flex-col p-4 gap-4 overflow-y-auto">
        <div>
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Categories</p>
          <div className="space-y-1">
            {CATEGORIES.map((c) => (
              <label key={c} className="flex items-center gap-2 cursor-pointer text-sm text-slate-700 dark:text-slate-300">
                <input
                  type="checkbox"
                  checked={activeFilters.categories.includes(c)}
                  onChange={() => toggleFilter('categories', c)}
                  className="accent-indigo-600 rounded"
                />
                {c}
              </label>
            ))}
          </div>
        </div>
        <div>
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Regions</p>
          <div className="space-y-1">
            {REGIONS.map((r) => (
              <label key={r} className="flex items-center gap-2 cursor-pointer text-sm text-slate-700 dark:text-slate-300">
                <input
                  type="checkbox"
                  checked={activeFilters.regions.includes(r)}
                  onChange={() => toggleFilter('regions', r)}
                  className="accent-indigo-600 rounded"
                />
                {r}
              </label>
            ))}
          </div>
        </div>
        <div className="mt-auto">
          <input ref={fileRef} type="file" multiple accept=".csv,.txt,.md,.pdf" className="hidden" onChange={handleUpload} />
          <button
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-lg text-xs text-slate-500 hover:border-indigo-400 hover:text-indigo-600 transition-colors disabled:opacity-50"
          >
            {uploading ? <Loader2 size={14} className="animate-spin" /> : <Upload size={14} />}
            Upload Data
          </button>
        </div>
      </aside>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {chatMessages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full gap-6 text-center">
              <div className="w-16 h-16 bg-indigo-100 dark:bg-indigo-900 rounded-2xl flex items-center justify-center">
                <Bot size={32} className="text-indigo-600 dark:text-indigo-400" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-slate-700 dark:text-slate-200 mb-1">Strategy Assistant</h2>
                <p className="text-sm text-slate-400">Ask me about your product portfolio, sales trends, or strategic opportunities.</p>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-xl w-full">
                {STARTERS.map((q) => (
                  <button
                    key={q}
                    onClick={() => { setInput(q); }}
                    className="text-left text-xs px-3 py-2.5 border border-slate-200 dark:border-slate-700 rounded-lg hover:border-indigo-400 hover:text-indigo-600 transition-colors text-slate-600 dark:text-slate-300"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {chatMessages.map((msg) => (
            <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 flex-shrink-0 bg-indigo-100 dark:bg-indigo-900 rounded-full flex items-center justify-center">
                  <Bot size={16} className="text-indigo-600 dark:text-indigo-400" />
                </div>
              )}
              <div className={`max-w-[80%] ${msg.role === 'user' ? 'order-first' : ''}`}>
                <div className={`rounded-2xl px-4 py-3 text-sm ${
                  msg.role === 'user'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200'
                }`}>
                  {msg.role === 'assistant' ? (
                    <ReactMarkdown className="prose prose-sm dark:prose-invert max-w-none">{msg.content}</ReactMarkdown>
                  ) : (
                    msg.content
                  )}
                </div>

                {msg.role === 'assistant' && msg.agentOutputs && (
                  <div className="mt-3 space-y-2">
                    <p className="text-xs text-slate-400 flex items-center gap-1">
                      <ChevronDown size={12} /> Agent Outputs
                    </p>
                    <AgentCard title="Customer Insights" icon="💬">
                      {(() => {
                        const ci = msg.agentOutputs?.customer_insights as Record<string, unknown> | undefined
                        if (!ci) return <p className="text-xs text-slate-400">No data</p>
                        return (
                          <div className="text-xs space-y-2">
                            <p><strong>Sentiment:</strong> {String(ci.overall_sentiment)} | <strong>NPS:</strong> {Number(ci.nps_score || 0).toFixed(1)}</p>
                            {(ci.top_complaints as string[] | undefined)?.length ? (
                              <div><strong>Top Complaints:</strong><ul className="list-disc pl-4 mt-1">{(ci.top_complaints as string[]).map((c, i) => <li key={i}>{c}</li>)}</ul></div>
                            ) : null}
                            {!!ci.key_insight && <p className="italic text-slate-500">{String(ci.key_insight)}</p>}
                          </div>
                        )
                      })()}
                    </AgentCard>

                    <AgentCard title="Sales Analysis" icon="📊">
                      {(() => {
                        const sa = msg.agentOutputs?.sales_analysis as Record<string, unknown> | undefined
                        if (!sa) return <p className="text-xs text-slate-400">No data</p>
                        return (
                          <div className="text-xs space-y-1">
                            <p><strong>Trend:</strong> {String(sa.growth_trend)} | <strong>Best Region:</strong> {String(sa.best_region)}</p>
                            {!!sa.key_insight && <p className="italic text-slate-500">{String(sa.key_insight)}</p>}
                          </div>
                        )
                      })()}
                    </AgentCard>

                    <AgentCard title="SWOT Analysis" icon="🔀">
                      <SWOTGrid data={(msg.agentOutputs?.swot as Record<string, unknown> | undefined) || {}} />
                    </AgentCard>

                    <AgentCard title="Feature Priorities (RICE)" icon="⭐">
                      {(() => {
                        const fp = msg.agentOutputs?.feature_priorities as Record<string, unknown> | undefined
                        const features = fp?.prioritized_features as unknown[] | undefined
                        if (!features?.length) return <p className="text-xs text-slate-400">No features identified</p>
                        return <RICETable features={features as Parameters<typeof RICETable>[0]['features']} />
                      })()}
                    </AgentCard>

                    <AgentCard title="Opportunities" icon="💡">
                      {(() => {
                        const opp = msg.agentOutputs?.opportunities as Record<string, unknown> | undefined
                        const items = opp?.top_opportunities as unknown[] | undefined
                        if (!items?.length) return <p className="text-xs text-slate-400">No opportunities identified</p>
                        return (
                          <div className="space-y-2">
                            {(items as Parameters<typeof OpportunityCard>[0]['opportunity'][]).map((o, i) => (
                              <OpportunityCard key={i} opportunity={o} />
                            ))}
                          </div>
                        )
                      })()}
                    </AgentCard>

                    <AgentCard title="Strategic Recommendations" icon="🎯">
                      {(() => {
                        const strat = msg.agentOutputs?.strategy as Record<string, unknown> | undefined
                        if (!strat) return <p className="text-xs text-slate-400">No strategy data</p>
                        const plan = strat.action_plan as Record<string, unknown> | undefined
                        return (
                          <div className="text-xs space-y-3">
                            {(['90_days', '6_months', '12_months'] as const).map((horizon) => {
                              const actions = (plan?.[horizon] as Array<{ action: string; owner: string; kpi: string }> | undefined) || []
                              return actions.length ? (
                                <div key={horizon}>
                                  <p className="font-semibold text-slate-600 dark:text-slate-300 mb-1">
                                    {horizon === '90_days' ? '90-Day' : horizon === '6_months' ? '6-Month' : '12-Month'} Actions
                                  </p>
                                  {actions.map((a, i) => (
                                    <div key={i} className="flex gap-2 mb-1.5">
                                      <span className="text-indigo-500">•</span>
                                      <div><span className="font-medium">{a.action}</span> <span className="text-slate-400">— KPI: {a.kpi}</span></div>
                                    </div>
                                  ))}
                                </div>
                              ) : null
                            })}
                          </div>
                        )
                      })()}
                    </AgentCard>
                  </div>
                )}
              </div>
              {msg.role === 'user' && (
                <div className="w-8 h-8 flex-shrink-0 bg-slate-100 dark:bg-slate-700 rounded-full flex items-center justify-center">
                  <User size={16} className="text-slate-500" />
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 flex-shrink-0 bg-indigo-100 dark:bg-indigo-900 rounded-full flex items-center justify-center">
                <Bot size={16} className="text-indigo-600" />
              </div>
              <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl px-4 py-3">
                <div className="flex gap-1">
                  {[0, 1, 2].map((i) => (
                    <span key={i} className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
                  ))}
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input Bar */}
        <div className="border-t border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
          <div className="flex gap-2 max-w-4xl mx-auto">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your product strategy… (Ctrl+Enter to send)"
              rows={2}
              className="flex-1 resize-none rounded-xl border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 text-slate-800 dark:text-slate-100 placeholder-slate-400"
            />
            <button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white transition-colors"
            >
              {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
