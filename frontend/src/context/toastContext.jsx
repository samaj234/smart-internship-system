import { createContext, useContext, useState, useCallback } from 'react'
import { CheckCircle2, XCircle, AlertTriangle, Info, X } from 'lucide-react'

const ToastContext = createContext()

let idCounter = 0

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  const showToast = useCallback((message, type = 'info', duration = 4000) => {
    const id = ++idCounter
    setToasts(prev => [...prev, { id, message, type }])

    if (duration > 0) {
      setTimeout(() => removeToast(id), duration)
    }
    return id
  }, [removeToast])

  const toast = {
    success: (msg, duration) => showToast(msg, 'success', duration),
    error: (msg, duration) => showToast(msg, 'error', duration),
    warning: (msg, duration) => showToast(msg, 'warning', duration),
    info: (msg, duration) => showToast(msg, 'info', duration),
  }

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={removeToast} />
    </ToastContext.Provider>
  )
}

export function useToast() {
  return useContext(ToastContext)
}

function ToastContainer({ toasts, onDismiss }) {
  if (toasts.length === 0) return null

  const iconFor = (type) => {
    if (type === 'success') return <CheckCircle2 size={18} className="text-[#1AA29F]" />
    if (type === 'error') return <XCircle size={18} className="text-red-500" />
    if (type === 'warning') return <AlertTriangle size={18} className="text-amber-500" />
    return <Info size={18} className="text-blue-500" />
  }

  const borderFor = (type) => {
    if (type === 'success') return 'border-l-[#1AA29F]'
    if (type === 'error') return 'border-l-red-500'
    if (type === 'warning') return 'border-l-amber-500'
    return 'border-l-blue-500'
  }

  return (
    <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 w-80">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`bg-white shadow-lg rounded-xl border border-gray-100 border-l-4 ${borderFor(t.type)} px-4 py-3 flex items-start gap-2.5 animate-in`}
          role="alert"
        >
          <div className="shrink-0 mt-0.5">{iconFor(t.type)}</div>
          <p className="text-sm text-gray-700 flex-1">{t.message}</p>
          <button
            onClick={() => onDismiss(t.id)}
            className="text-gray-300 hover:text-gray-500 transition-colors shrink-0"
            aria-label="Dismiss"
          >
            <X size={15} />
          </button>
        </div>
      ))}
    </div>
  )
}