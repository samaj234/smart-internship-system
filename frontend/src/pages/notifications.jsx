import { useState, useEffect } from 'react'
import { Bell, Loader2, AlertCircle, CheckCircle2, XCircle, MessageSquare, X } from 'lucide-react'
import API from '../api/axios'
import { useToast } from '../context/ToastContext'

export default function Notifications() {
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [markingAll, setMarkingAll] = useState(false)
  const [deletingId, setDeletingId] = useState(null)
  const [clearingAll, setClearingAll] = useState(false)
  const toast = useToast()

  useEffect(() => {
    let isMounted = true

    const fetchNotifications = async () => {
      try {
        const res = await API.get('/notifications/')
        if (isMounted) setNotifications(res.data.notifications || [])
      } catch (err) {
        if (isMounted) setError(err.response?.data?.error || 'Could not load notifications')
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    fetchNotifications()
    return () => { isMounted = false }
  }, [])

  const handleMarkRead = async (id) => {
    // Optimistic — no need to block the click on the round trip
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n))
    try {
      await API.patch(`/notifications/${id}/read`)
      window.dispatchEvent(new Event('notifications:changed'))
    } catch (err) {
      toast.error('Could not mark as read')
    }
  }

  const handleMarkAllRead = async () => {
    setMarkingAll(true)
    const previous = notifications
    setNotifications(prev => prev.map(n => ({ ...n, is_read: true })))
    try {
      await API.patch('/notifications/read-all')
      window.dispatchEvent(new Event('notifications:changed'))
      toast.success('All notifications marked as read')
    } catch (err) {
      setNotifications(previous)
      toast.error('Could not mark all as read')
    } finally {
      setMarkingAll(false)
    }
  }

  const handleDelete = async (id) => {
    setDeletingId(id)
    const previous = notifications
    setNotifications(prev => prev.filter(n => n.id !== id))
    try {
      await API.delete(`/notifications/${id}`)
      window.dispatchEvent(new Event('notifications:changed'))
    } catch (err) {
      setNotifications(previous)
      toast.error('Could not delete notification')
    } finally {
      setDeletingId(null)
    }
  }

  const handleClearAll = async () => {
    setClearingAll(true)
    const previous = notifications
    setNotifications([])
    try {
      await API.delete('/notifications/')
      window.dispatchEvent(new Event('notifications:changed'))
      toast.success('Notifications cleared')
    } catch (err) {
      setNotifications(previous)
      toast.error('Could not clear notifications')
    } finally {
      setClearingAll(false)
    }
  }

  const icon = (type) => {
    if (type === 'status') return <CheckCircle2 size={16} className="text-[#1AA29F]" />
    return <MessageSquare size={16} className="text-amber-500" />
  }

  const unreadCount = notifications.filter(n => !n.is_read).length

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-6">
        <Loader2 className="animate-spin text-[#1AA29F]" size={32} />
      </div>
    )
  }

  return (
    <div className="p-6 max-w-2xl mx-auto w-full">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <Bell size={22} className="text-[#1AA29F]" />
          <h1 className="text-2xl font-bold text-gray-800">Notifications</h1>
        </div>
        <div className="flex items-center gap-3">
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllRead}
              disabled={markingAll}
              className="text-xs font-semibold text-[#1AA29F] hover:underline disabled:opacity-50"
            >
              {markingAll ? 'Marking...' : 'Mark all as read'}
            </button>
          )}
          {notifications.length > 0 && (
            <button
              onClick={handleClearAll}
              disabled={clearingAll}
              className="text-xs font-semibold text-gray-400 hover:text-red-500 hover:underline disabled:opacity-50"
            >
              {clearingAll ? 'Clearing...' : 'Clear all'}
            </button>
          )}
        </div>
      </div>
      <p className="text-gray-400 text-sm mb-6">
        Updates from employers on your applications.
      </p>

      {error && (
        <div className="flex items-center gap-2 bg-red-50 text-red-600 px-4 py-3 rounded-lg mb-4 text-sm">
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {notifications.length === 0 && !error ? (
        <div className="bg-white rounded-2xl border border-gray-100 p-8 text-center">
          <p className="text-gray-500 text-sm">No notifications yet.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {notifications.map((n) => (
            <div
              key={n.id}
              className={`flex items-start gap-3 p-4 rounded-xl border transition-colors ${
                n.is_read
                  ? 'bg-white border-gray-100'
                  : 'bg-[#e6f7f7]/50 border-[#1AA29F]/20'
              }`}
            >
              <button
                onClick={() => !n.is_read && handleMarkRead(n.id)}
                className={`flex-1 flex items-start gap-3 text-left min-w-0 ${n.is_read ? '' : 'hover:opacity-80'}`}
              >
                <div className="mt-0.5 shrink-0">{icon(n.type)}</div>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm ${n.is_read ? 'text-gray-600' : 'text-gray-800 font-medium'}`}>
                    {n.message}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    {new Date(n.created_at).toLocaleString()}
                  </p>
                </div>
                {!n.is_read && (
                  <span className="w-2 h-2 rounded-full bg-[#1AA29F] shrink-0 mt-1.5" />
                )}
              </button>
              <button
                onClick={() => handleDelete(n.id)}
                disabled={deletingId === n.id}
                aria-label="Delete notification"
                className="p-1 rounded-full text-gray-300 hover:text-red-500 hover:bg-red-50 transition-colors disabled:opacity-50 shrink-0"
              >
                {deletingId === n.id ? <Loader2 size={14} className="animate-spin" /> : <X size={14} />}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}