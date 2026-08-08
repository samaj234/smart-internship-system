import { useState, useRef, useEffect } from 'react'
import { MessageCircle, X, Send, Loader2, Bot, User, Paperclip, FileText, Image, XCircle } from 'lucide-react'
import API from '../api/axios'
import { useAuth } from '../context/AuthContext'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export default function ChatBot() {
  const [isOpen, setIsOpen] = useState(false)
  const [history, setHistory] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const [attachedFile, setAttachedFile] = useState(null)
  const [attachPreview, setAttachPreview] = useState(null)
  const { user } = useAuth()
  const scrollRef = useRef(null)
  const fileInputRef = useRef(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [history, isOpen])

  if (!user) return null

  const handleFile = (file) => {
    if (!file) return
    const allowed = ['pdf', 'docx', 'doc', 'png', 'jpg', 'jpeg', 'webp', 'gif']
    const ext = file.name.split('.').pop().toLowerCase()
    if (!allowed.includes(ext)) {
      setError(`File type .${ext} not supported. Use PDF, DOCX, PNG, JPG, or WEBP.`)
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('File must be under 10MB')
      return
    }
    setAttachedFile(file)
    setError('')

    // Generate preview for images
    if (['png', 'jpg', 'jpeg', 'webp', 'gif'].includes(ext)) {
      const reader = new FileReader()
      reader.onload = (e) => setAttachPreview(e.target.result)
      reader.readAsDataURL(file)
    } else {
      setAttachPreview(null)
    }
  }

  const removeAttachment = () => {
    setAttachedFile(null)
    setAttachPreview(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleSend = async (e) => {
    e.preventDefault()
    if ((!input.trim() && !attachedFile) || sending) return

    const message = input.trim()
    setInput('')
    setError('')
    setSending(true)

    // Optimistic UI
    const optimisticHistory = [
      ...history,
      {
        role: 'user',
        content: message || `[Attached: ${attachedFile?.name}]`,
        hasFile: !!attachedFile,
        fileName: attachedFile?.name,
        filePreview: attachPreview
      }
    ]
    setHistory(optimisticHistory)

    try {
      let response

      if (attachedFile) {
        // Send as multipart form data
        const formData = new FormData()
        if (message) formData.append('message', message)
        formData.append('history', JSON.stringify(history))
        formData.append('file', attachedFile)

        response = await API.post('/chat/message', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
      } else {
        // Send as JSON (existing behavior)
        response = await API.post('/chat/message', {
          message,
          history
        })
      }

      setHistory(response.data.history)
      removeAttachment()
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to send message')
      setHistory(history) // roll back optimistic update
    } finally {
      setSending(false)
    }
  }

  const isImageFile = (filename) => {
    if (!filename) return false
    return ['png', 'jpg', 'jpeg', 'webp', 'gif'].includes(
      filename.split('.').pop().toLowerCase()
    )
  }

  return (
    <>
     {/* Floating toggle button + tooltip wrapper */}
        <div className="fixed bottom-6 right-6 z-50 group">
          <button
            onClick={() => setIsOpen(prev => !prev)}
            className="bg-[#1AA29F] hover:bg-[#158a87] text-white p-3 rounded-full shadow-lg transition-colors"
            aria-label="Open chat assistant"
          >
            {isOpen ? <X size={20} /> : <MessageCircle size={20} />}
          </button>
          {!isOpen && (
            <span className="absolute bottom-14 right-0 bg-gray-800 text-white text-xs font-medium px-2.5 py-1.5 rounded-lg whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
              Career Assistant
            </span>
          )}
        </div>

      {/* Chat window */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 z-50 w-80 sm:w-96 h-[520px] bg-white rounded-2xl shadow-2xl border border-gray-100 flex flex-col overflow-hidden">

          {/* Header */}
          <div className="bg-[#1AA29F] text-white px-4 py-3 flex items-center gap-2">
            <Bot size={18} />
            <div>
              <p className="font-semibold text-sm">Career Assistant</p>
              <p className="text-xs opacity-80">Ask me anything — attach files or images too</p>
            </div>
          </div>

          {/* Messages */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
            {history.length === 0 && (
              <div className="text-center text-gray-400 text-sm mt-8">
                <Bot size={28} className="mx-auto mb-2 text-[#1AA29F]" />
                <p>Hi! Ask me anything about internships.</p>
                <p className="text-xs mt-1 text-gray-300">You can also attach your CV or a job posting image.</p>
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
                <div className={`max-w-[75%] rounded-2xl text-sm whitespace-pre-wrap
                  ${msg.role === 'user'
                    ? 'bg-[#1AA29F] text-white rounded-br-sm px-3 py-2'
                    : 'bg-white border border-gray-100 text-gray-700 rounded-bl-sm px-3 py-2'
                  }`}
                >
                  {/* Show image preview if user sent an image */}
                  {msg.role === 'user' && msg.filePreview && (
                    <img
                      src={msg.filePreview}
                      alt="attached"
                      className="rounded-lg mb-2 max-w-full max-h-32 object-contain"
                    />
                  )}
                  {/* Show file badge for non-image files */}
                  {msg.role === 'user' && msg.hasFile && !msg.filePreview && (
                    <div className="flex items-center gap-1.5 bg-white/20 rounded-lg px-2 py-1 mb-1.5 text-xs">
                      <FileText size={12} />
                      <span className="truncate max-w-[140px]">{msg.fileName}</span>
                    </div>
                  )}
                 {msg.role === 'user' ? (
                    msg.content && msg.content !== `[Attached: ${msg.fileName}]` && msg.content
                  ) : (
                    <div className="prose prose-sm prose-slate max-w-none
                                    prose-p:my-1.5 prose-p:leading-relaxed
                                    prose-ul:my-1.5 prose-ol:my-1.5
                                    prose-headings:mt-2 prose-headings:mb-1
                                    prose-strong:font-semibold
                                    prose-pre:bg-gray-800 prose-pre:text-gray-100 prose-pre:rounded-lg prose-pre:p-2
                                    prose-code:before:content-none prose-code:after:content-none
                                    prose-code:bg-gray-100 prose-code:px-1 prose-code:rounded prose-code:text-[13px]">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                    </div>
)}
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

          {/* File attachment preview */}
          {attachedFile && (
            <div className="px-3 py-2 border-t border-gray-100 bg-gray-50">
              <div className="flex items-center gap-2 bg-white border border-gray-200 rounded-xl px-3 py-2">
                {attachPreview ? (
                  <img src={attachPreview} alt="preview" className="w-8 h-8 rounded object-cover" />
                ) : (
                  <FileText size={16} className="text-[#1AA29F]" />
                )}
                <span className="text-xs text-gray-600 truncate flex-1">{attachedFile.name}</span>
                <button onClick={removeAttachment} className="text-gray-400 hover:text-gray-600">
                  <XCircle size={16} />
                </button>
              </div>
            </div>
          )}

          {/* Input area */}
        <form onSubmit={handleSend} className="flex items-center gap-2 p-3 border-t border-gray-100">
          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.doc,.png,.jpg,.jpeg,.webp,.gif"
            onChange={(e) => handleFile(e.target.files?.[0])}
            className="hidden"
          />

          {/* + button with tooltip */}
          <div className="relative group">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="w-8 h-8 rounded-full border border-gray-300 hover:border-[#1AA29F] hover:text-[#1AA29F] text-gray-500 flex items-center justify-center transition-colors text-lg font-light"
              aria-label="Attach file or image"
            >
              +
            </button>
            <span className="absolute bottom-10 left-0 bg-gray-800 text-white text-xs font-medium px-2.5 py-1.5 rounded-lg whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
              Add files, CV, or images
            </span>
          </div>

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={attachedFile ? "Add a message (optional)..." : "Write a message..."}
            disabled={sending}
            className="flex-1 text-sm outline-none px-3 py-2 rounded-xl bg-gray-50 focus:bg-white border border-transparent focus:border-[#1AA29F] transition-colors"
          />

          <button
            type="submit"
            disabled={sending || (!input.trim() && !attachedFile)}
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

// import { useState, useRef, useEffect } from 'react'
// import { MessageCircle, X, Send, Loader2, Bot, User, FileText, XCircle } from 'lucide-react'
// import ReactMarkdown from 'react-markdown'
// import API from '../api/axios'
// import { useAuth } from '../context/AuthContext'

// export default function ChatBot() {
//   const [isOpen, setIsOpen] = useState(false)
//   const [history, setHistory] = useState([])
//   const [input, setInput] = useState('')
//   const [sending, setSending] = useState(false)
//   const [error, setError] = useState('')
//   const [attachedFile, setAttachedFile] = useState(null)
//   const [attachPreview, setAttachPreview] = useState(null)
//   const { user } = useAuth()
//   const scrollRef = useRef(null)
//   const fileInputRef = useRef(null)

//   useEffect(() => {
//     if (scrollRef.current) {
//       scrollRef.current.scrollTop = scrollRef.current.scrollHeight
//     }
//   }, [history, isOpen])

//   if (!user) return null

//   const handleFile = (file) => {
//     if (!file) return
//     const allowed = ['pdf', 'docx', 'doc', 'png', 'jpg', 'jpeg', 'webp', 'gif']
//     const ext = file.name.split('.').pop().toLowerCase()
//     if (!allowed.includes(ext)) {
//       setError(`File type .${ext} not supported. Use PDF, DOCX, PNG, JPG, or WEBP.`)
//       return
//     }
//     if (file.size > 10 * 1024 * 1024) {
//       setError('File must be under 10MB')
//       return
//     }
//     setAttachedFile(file)
//     setError('')

//     // Generate preview for images
//     if (['png', 'jpg', 'jpeg', 'webp', 'gif'].includes(ext)) {
//       const reader = new FileReader()
//       reader.onload = (e) => setAttachPreview(e.target.result)
//       reader.readAsDataURL(file)
//     } else {
//       setAttachPreview(null)
//     }
//   }

//   const removeAttachment = () => {
//     setAttachedFile(null)
//     setAttachPreview(null)
//     if (fileInputRef.current) fileInputRef.current.value = ''
//   }

//   const handleSend = async (e) => {
//     e.preventDefault()
//     if ((!input.trim() && !attachedFile) || sending) return

//     const message = input.trim()
//     setInput('')
//     setError('')
//     setSending(true)

//     // Optimistic UI
//     const optimisticHistory = [
//       ...history,
//       {
//         role: 'user',
//         content: message || `[Attached: ${attachedFile?.name}]`,
//         hasFile: !!attachedFile,
//         fileName: attachedFile?.name,
//         filePreview: attachPreview
//       }
//     ]
//     setHistory(optimisticHistory)

//     try {
//       let response

//       if (attachedFile) {
//         const formData = new FormData()
//         if (message) formData.append('message', message)
//         formData.append('history', JSON.stringify(history))
//         formData.append('file', attachedFile)

//         response = await API.post('/chat/message', formData, {
//           headers: { 'Content-Type': 'multipart/form-data' }
//         })
//       } else {
//         response = await API.post('/chat/message', {
//           message,
//           history
//         })
//       }

//       setHistory(response.data.history)
//       removeAttachment()
//     } catch (err) {
//       setError(err.response?.data?.error || 'Failed to send message')
//       setHistory(history) // roll back optimistic update
//     } finally {
//       setSending(false)
//     }
//   }

//   return (
//     <>
//       {/* Floating toggle button */}
//       <div className="fixed bottom-6 right-6 z-50 group">
//         <button
//           onClick={() => setIsOpen(prev => !prev)}
//           className="bg-[#1AA29F] hover:bg-[#158a87] text-white p-3 rounded-full shadow-lg transition-colors"
//           aria-label="Open chat assistant"
//         >
//           {isOpen ? <X size={20} /> : <MessageCircle size={20} />}
//         </button>
//         {!isOpen && (
//           <span className="absolute bottom-14 right-0 bg-gray-800 text-white text-xs font-medium px-2.5 py-1.5 rounded-lg whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
//             Career Assistant
//           </span>
//         )}
//       </div>

//       {/* Chat window */}
//       {isOpen && (
//         <div className="fixed bottom-24 right-6 z-50 w-80 sm:w-96 h-[520px] bg-white rounded-2xl shadow-2xl border border-gray-100 flex flex-col overflow-hidden">

//           {/* Header */}
//           <div className="bg-[#1AA29F] text-white px-4 py-3 flex items-center gap-2">
//             <Bot size={18} />
//             <div>
//               <p className="font-semibold text-sm">Career Assistant</p>
//               <p className="text-xs opacity-80">Ask me anything — attach files or images too</p>
//             </div>
//           </div>

//           {/* Messages */}
//           <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
//             {history.length === 0 && (
//               <div className="text-center text-gray-400 text-sm mt-8">
//                 <Bot size={28} className="mx-auto mb-2 text-[#1AA29F]" />
//                 <p>Hi! Ask me anything about internships.</p>
//                 <p className="text-xs mt-1 text-gray-300">You can also attach your CV or a job posting image.</p>
//               </div>
//             )}

//             {history.map((msg, i) => (
//               <div
//                 key={i}
//                 className={`flex gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
//               >
//                 {msg.role !== 'user' && (
//                   <div className="bg-[#e6f7f7] rounded-full p-1.5 h-fit">
//                     <Bot size={14} className="text-[#1AA29F]" />
//                   </div>
//                 )}
                
//                 <div className={`max-w-[80%] rounded-2xl text-sm
//                   ${msg.role === 'user'
//                     ? 'bg-[#1AA29F] text-white rounded-br-sm px-3 py-2 whitespace-pre-wrap'
//                     : 'bg-white border border-gray-100 text-gray-800 rounded-bl-sm px-3.5 py-2.5'
//                   }`}
//                 >
//                   {/* Image preview for user attachments */}
//                   {msg.role === 'user' && msg.filePreview && (
//                     <img
//                       src={msg.filePreview}
//                       alt="attached"
//                       className="rounded-lg mb-2 max-w-full max-h-32 object-contain"
//                     />
//                   )}

//                   {/* Non-image file indicator */}
//                   {msg.role === 'user' && msg.hasFile && !msg.filePreview && (
//                     <div className="flex items-center gap-1.5 bg-white/20 rounded-lg px-2 py-1 mb-1.5 text-xs">
//                       <FileText size={12} />
//                       <span className="truncate max-w-[140px]">{msg.fileName}</span>
//                     </div>
//                   )}

//                   {/* Render Message Content */}
//                   {msg.role === 'user' ? (
//                     msg.content && msg.content !== `[Attached: ${msg.fileName}]` && msg.content
//                   ) : (
//                     /* Assistant Output - Formatted via ReactMarkdown & Tailwind Prose */
//                     <div className="prose prose-sm prose-slate max-w-none dark:prose-invert prose-p:leading-relaxed prose-pre:bg-gray-800 prose-pre:text-white">
//                       <ReactMarkdown>{msg.content}</ReactMarkdown>
//                     </div>
//                   )}
//                 </div>

//                 {msg.role === 'user' && (
//                   <div className="bg-gray-100 rounded-full p-1.5 h-fit">
//                     <User size={14} className="text-gray-500" />
//                   </div>
//                 )}
//               </div>
//             ))}

//             {sending && (
//               <div className="flex gap-2 justify-start">
//                 <div className="bg-[#e6f7f7] rounded-full p-1.5 h-fit">
//                   <Bot size={14} className="text-[#1AA29F]" />
//                 </div>
//                 <div className="bg-white border border-gray-100 px-3 py-2 rounded-2xl rounded-bl-sm">
//                   <Loader2 size={14} className="animate-spin text-[#1AA29F]" />
//                 </div>
//               </div>
//             )}
//           </div>

//           {error && (
//             <div className="px-4 py-2 bg-red-50 text-red-600 text-xs">{error}</div>
//           )}

//           {/* File preview bar */}
//           {attachedFile && (
//             <div className="px-3 py-2 border-t border-gray-100 bg-gray-50">
//               <div className="flex items-center gap-2 bg-white border border-gray-200 rounded-xl px-3 py-2">
//                 {attachPreview ? (
//                   <img src={attachPreview} alt="preview" className="w-8 h-8 rounded object-cover" />
//                 ) : (
//                   <FileText size={16} className="text-[#1AA29F]" />
//                 )}
//                 <span className="text-xs text-gray-600 truncate flex-1">{attachedFile.name}</span>
//                 <button onClick={removeAttachment} className="text-gray-400 hover:text-gray-600">
//                   <XCircle size={16} />
//                 </button>
//               </div>
//             </div>
//           )}

//           {/* Input field */}
//           <form onSubmit={handleSend} className="flex items-center gap-2 p-3 border-t border-gray-100">
//             <input
//               ref={fileInputRef}
//               type="file"
//               accept=".pdf,.docx,.doc,.png,.jpg,.jpeg,.webp,.gif"
//               onChange={(e) => handleFile(e.target.files?.[0])}
//               className="hidden"
//             />

//             <div className="relative group">
//               <button
//                 type="button"
//                 onClick={() => fileInputRef.current?.click()}
//                 className="w-8 h-8 rounded-full border border-gray-300 hover:border-[#1AA29F] hover:text-[#1AA29F] text-gray-500 flex items-center justify-center transition-colors text-lg font-light"
//                 aria-label="Attach file or image"
//               >
//                 +
//               </button>
//               <span className="absolute bottom-10 left-0 bg-gray-800 text-white text-xs font-medium px-2.5 py-1.5 rounded-lg whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
//                 Add files, CV, or images
//               </span>
//             </div>

//             <input
//               type="text"
//               value={input}
//               onChange={(e) => setInput(e.target.value)}
//               placeholder={attachedFile ? "Add a message (optional)..." : "Write a message..."}
//               disabled={sending}
//               className="flex-1 text-sm outline-none px-3 py-2 rounded-xl bg-gray-50 focus:bg-white border border-transparent focus:border-[#1AA29F] transition-colors"
//             />

//             <button
//               type="submit"
//               disabled={sending || (!input.trim() && !attachedFile)}
//               className="bg-[#1AA29F] hover:bg-[#158a87] text-white p-2 rounded-xl disabled:opacity-50 transition-colors"
//             >
//               <Send size={16} />
//             </button>
//           </form>
//         </div>
//       )}
//     </>
//   )
// }