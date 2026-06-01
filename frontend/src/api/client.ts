import axios from 'axios'
import toast from 'react-hot-toast'

const BASE_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({ baseURL: BASE_URL })

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || 'Request failed'
    toast.error(msg)
    return Promise.reject(err)
  }
)

export interface FilterOptions {
  categories?: string[]
  regions?: string[]
  source_types?: string[]
  date_from?: string
  date_to?: string
  min_rating?: number
}

export interface ChatResponse {
  response: string
  agent_outputs: Record<string, unknown>
  sources: Array<{ document: string; metadata: Record<string, unknown> }>
}

export interface DashboardData {
  total_revenue: number
  total_profit: number
  avg_customer_rating: number
  total_units_sold: number
  revenue_by_product: Array<{ name: string; revenue: number }>
  revenue_by_category: Array<{ category: string; revenue: number }>
  revenue_by_region: Array<{ region: string; revenue: number }>
  monthly_trend: Array<{ month: string; revenue: number; profit: number }>
  top_products: Array<Record<string, unknown>>
  collection_stats: Record<string, unknown>
}

export const apiClient = {
  async getDashboard(): Promise<DashboardData> {
    const res = await api.get('/api/dashboard')
    return res.data
  },

  async chat(message: string, filters?: FilterOptions): Promise<ChatResponse> {
    const res = await api.post('/api/chat', { message, filters })
    return res.data
  },

  async analyze(query: string, filters?: FilterOptions) {
    const res = await api.post('/api/analyze', { query, filters })
    return res.data
  },

  async ingestFiles(files: File[]) {
    const form = new FormData()
    files.forEach((f) => form.append('files', f))
    const res = await api.post('/api/ingest', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return res.data
  },

  getReportUrl(format: 'pdf' | 'json') {
    return `${BASE_URL}/api/report?format=${format}`
  },

  async getHealth() {
    const res = await api.get('/api/health')
    return res.data
  },
}
