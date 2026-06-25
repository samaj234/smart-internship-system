import { useState, useRef, useEffect } from 'react'
import { MessageCircle, X, Send, Loader2, Bot, User } from 'lucide-react'
import API from '../api/axios'
import { useAuth } from '../context/AuthContext'

export default function ChatBot() {
  const [isOpen, setIsOpen] = useState(false)
  const [history, setHistory] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const { user } = useAuth()
  const scrollRef = useRef(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [history, isOpen])

  if (!user) return null

  const handleSend = async (e) => {
    e.preventDefault()
    const message = input.trim()
    if (!message || sending) return

    setInput('')
    setError('')
    setSending(true)

    const optimisticHistory = [...history, { role: 'user', content: message }]
    setHistory(optimisticHistory)

    try {
      const res = await API.post('/chat/message', {
        message,
        history
      })
      setHistory(res.data.history)
    } catch (err) {
      setError(err.response?.data?.error || 'Chatbot is unavailable right now')
      setHistory(history) // roll back optimistic update
    } finally {
      setSending(false)
    }
  }

  return (
    <>
      {/* Floating toggle button */}
      <button
        onClick={() => setIsOpen(prev => !prev)}
        className="fixed bottom-6 right-6 z-50 bg-[#1AA29F] hover:bg-[#158a87] text-white p-4 rounded-full shadow-lg transition-colors"
        aria-label="Open chat assistant"
      >
        {isOpen ? <X size={22} /> : <MessageCircle size={22} />}
      </button>

      {/* Chat window */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 z-50 w-80 sm:w-96 h-[480px] bg-white rounded-2xl shadow-2xl border border-gray-100 flex flex-col overflow-hidden">
          {/* Header */}
          <div className="bg-[#1AA29F] text-white px-4 py-3 flex items-center gap-2">
            <Bot size={18} />
            <div>
              <p className="font-semibold text-sm">Career Assistant</p>
              <p className="text-xs opacity-80">Ask me about internships, your profile, or applications</p>
            </div>
          </div>

          {/* Messages */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
            {history.length === 0 && (
              <div className="text-center text-gray-400 text-sm mt-8">
                <Bot size={28} className="mx-auto mb-2 text-[#1AA29F]" />
                Hi {user.role === 'student' ? 'there' : 'there'}! Ask me anything about{' '}
                {user.role === 'student' ? 'internships or your applications' : 'writing job posts or finding candidates'}.
              </div>
            )}

            {history.map((msg, i) => (
              <div
                key={i}
                className={`flex gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role !== 'user' && (
                  <div className="bg-[#e6f7f7] rounded-full p-1.5 h-fit">
                    <Bot size={14} className="text-[#1AA29F]" />
                  </div>
                )}
                <div
                  className={`max-w-[75%] px-3 py-2 rounded-2xl text-sm whitespace-pre-wrap
                    ${msg.role === 'user'
                      ? 'bg-[#1AA29F] text-white rounded-br-sm'
                      : 'bg-white border border-gray-100 text-gray-700 rounded-bl-sm'
                    }`}
                >
                  {msg.content}
                </div>
                {msg.role === 'user' && (
                  <div className="bg-gray-100 rounded-full p-1.5 h-fit">
                    <User size={14} className="text-gray-500" />
                  </div>
                )}
              </div>
            ))}

            {sending && (
              <div className="flex gap-2 justify-start">
                <div className="bg-[#e6f7f7] rounded-full p-1.5 h-fit">
                  <Bot size={14} className="text-[#1AA29F]" />
                </div>
                <div className="bg-white border border-gray-100 px-3 py-2 rounded-2xl rounded-bl-sm">
                  <Loader2 size={14} className="animate-spin text-[#1AA29F]" />
                </div>
              </div>
            )}
          </div>

          {error && (
            <div className="px-4 py-2 bg-red-50 text-red-600 text-xs">{error}</div>
          )}

          {/* Input */}
          <form onSubmit={handleSend} className="flex items-center gap-2 p-3 border-t border-gray-100">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message..."
              disabled={sending}
              className="flex-1 text-sm outline-none px-3 py-2 rounded-xl bg-gray-50 focus:bg-white border border-transparent focus:border-[#1AA29F] transition-colors"
            />
            <button
              type="submit"
              disabled={sending || !input.trim()}
              className="bg-[#1AA29F] hover:bg-[#158a87] text-white p-2 rounded-xl disabled:opacity-50 transition-colors"
            >
              <Send size={16} />
            </button>
          </form>
        </div>
      )}
    </>
  )
}