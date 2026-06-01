import { Component, ReactNode } from 'react'
import { AlertTriangle } from 'lucide-react'

interface Props { children: ReactNode }
interface State { hasError: boolean; message: string }

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: '' }

  static getDerivedStateFromError(err: Error): State {
    return { hasError: true, message: err.message }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-64 gap-4 text-center p-8">
          <AlertTriangle size={48} className="text-red-500" />
          <h2 className="text-xl font-semibold text-slate-700 dark:text-slate-300">Something went wrong</h2>
          <p className="text-sm text-slate-500 max-w-md">{this.state.message}</p>
          <button
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm"
            onClick={() => this.setState({ hasError: false, message: '' })}
          >
            Try Again
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
