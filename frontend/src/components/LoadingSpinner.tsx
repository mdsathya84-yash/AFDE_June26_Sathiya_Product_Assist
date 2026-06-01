interface Props {
  message?: string
  size?: 'sm' | 'md' | 'lg'
}

export default function LoadingSpinner({ message, size = 'md' }: Props) {
  const sizeClass = { sm: 'w-4 h-4', md: 'w-8 h-8', lg: 'w-12 h-12' }[size]
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-8">
      <div className={`${sizeClass} border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin`} />
      {message && <p className="text-sm text-slate-500">{message}</p>}
    </div>
  )
}
