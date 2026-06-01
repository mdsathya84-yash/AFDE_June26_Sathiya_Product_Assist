import { create } from 'zustand'
import { apiClient, ChatResponse, DashboardData, FilterOptions } from '../api/client'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  agentOutputs?: Record<string, unknown>
  sources?: Array<{ document: string; metadata: Record<string, unknown> }>
  timestamp: Date
}

interface FilterState {
  categories: string[]
  regions: string[]
}

interface AnalysisStore {
  analysisResult: Record<string, unknown> | null
  dashboardData: DashboardData | null
  isLoading: boolean
  isDashboardLoading: boolean
  error: string | null
  chatMessages: Message[]
  activeFilters: FilterState

  fetchDashboard: () => Promise<void>
  sendMessage: (message: string) => Promise<void>
  runAnalysis: (query: string) => Promise<void>
  setFilters: (filters: Partial<FilterState>) => void
  clearMessages: () => void
}

export const useAnalysisStore = create<AnalysisStore>((set, get) => ({
  analysisResult: null,
  dashboardData: null,
  isLoading: false,
  isDashboardLoading: false,
  error: null,
  chatMessages: [],
  activeFilters: { categories: [], regions: [] },

  fetchDashboard: async () => {
    set({ isDashboardLoading: true, error: null })
    try {
      const data = await apiClient.getDashboard()
      set({ dashboardData: data })
    } catch (e: unknown) {
      set({ error: (e as Error).message })
    } finally {
      set({ isDashboardLoading: false })
    }
  },

  sendMessage: async (message: string) => {
    const { activeFilters } = get()
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: message,
      timestamp: new Date(),
    }
    set((s) => ({ chatMessages: [...s.chatMessages, userMsg], isLoading: true }))

    try {
      const filters: FilterOptions = {}
      if (activeFilters.categories.length) filters.categories = activeFilters.categories
      if (activeFilters.regions.length) filters.regions = activeFilters.regions

      const res: ChatResponse = await apiClient.chat(message, Object.keys(filters).length ? filters : undefined)
      const assistantMsg: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: res.response,
        agentOutputs: res.agent_outputs,
        sources: res.sources,
        timestamp: new Date(),
      }
      set((s) => ({
        chatMessages: [...s.chatMessages, assistantMsg],
        analysisResult: res.agent_outputs,
      }))
    } catch {
      const errMsg: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'Sorry, the analysis failed. Please try again.',
        timestamp: new Date(),
      }
      set((s) => ({ chatMessages: [...s.chatMessages, errMsg] }))
    } finally {
      set({ isLoading: false })
    }
  },

  runAnalysis: async (query: string) => {
    set({ isLoading: true, error: null })
    try {
      const result = await apiClient.analyze(query)
      set({ analysisResult: result })
    } catch (e: unknown) {
      set({ error: (e as Error).message })
    } finally {
      set({ isLoading: false })
    }
  },

  setFilters: (filters) =>
    set((s) => ({ activeFilters: { ...s.activeFilters, ...filters } })),

  clearMessages: () => set({ chatMessages: [] }),
}))
