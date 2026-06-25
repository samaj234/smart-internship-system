import { useState, useRef } from 'react'
import { Upload, FileText, CheckCircle2, XCircle, Loader2 } from 'lucide-react'
import API from '../api/axios'

const ALLOWED_TYPES = ['.pdf', '.docx']
const MAX_SIZE_MB = 5

export default function CVUpload({ onSuccess }) {
  const [file, setFile] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [parsedData, setParsedData] = useState(null)
  const inputRef = useRef(null)

  const validateFile = (f) => {
    const ext = '.' + f.name.split('.').pop().toLowerCase()
    if (!ALLOWED_TYPES.includes(ext)) {
      return 'Only PDF and DOCX files are allowed'
    }
    if (f.size > MAX_SIZE_MB * 1024 * 1024) {
      return `File must be smaller than ${MAX_SIZE_MB}MB`
    }
    return null
  }

  const handleFile = (f) => {
    const validationError = validateFile(f)
    if (validationError) {
      setError(validationError)
      setFile(null)
      return
    }
    setError('')
    setFile(f)
    setParsedData(null)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragActive(false)
    if (e.dataTransfer.files?.[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setDragActive(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setDragActive(false)
  }

  const handleInputChange = (e) => {
    if (e.target.files?.[0]) {
      handleFile(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!file) return
    setUploading(true)
    setError('')

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await API.post('/students/upload-cv', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setParsedData(res.data.parsed_data)
      onSuccess?.(res.data.profile)
    } catch (err) {
      setError(err.response?.data?.error || 'Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  const reset = () => {
    setFile(null)
    setParsedData(null)
    setError('')
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <div className="w-full">
      {!parsedData ? (
        <>
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => inputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer transition-colors
              ${dragActive ? 'border-[#1AA29F] bg-[#e6f7f7]' : 'border-gray-300 hover:border-[#1AA29F]'}
            `}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.docx"
              onChange={handleInputChange}
              className="hidden"
            />

            {file ? (
              <>
                <FileText size={36} className="text-[#1AA29F] mb-2" />
                <p className="text-sm font-medium text-gray-700">{file.name}</p>
                <p className="text-xs text-gray-400 mt-1">{(file.size / 1024).toFixed(0)} KB</p>
              </>
            ) : (
              <>
                <Upload size={36} className="text-gray-400 mb-2" />
                <p className="text-sm font-medium text-gray-600">
                  Drag & drop your CV here, or click to browse
                </p>
                <p className="text-xs text-gray-400 mt-1">PDF or DOCX, max {MAX_SIZE_MB}MB</p>
              </>
            )}
          </div>

          {error && (
            <div className="flex items-center gap-2 bg-red-50 text-red-600 px-4 py-2 rounded-lg mt-3 text-sm">
              <XCircle size={16} />
              {error}
            </div>
          )}

          <div className="flex gap-3 mt-4">
            <button
              onClick={handleUpload}
              disabled={!file || uploading}
              className="flex-1 bg-[#1AA29F] hover:bg-[#158a87] text-white py-2.5 rounded-xl font-semibold text-sm disabled:opacity-50 transition-colors shadow flex items-center justify-center gap-2"
            >
              {uploading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Parsing CV...
                </>
              ) : (
                'Upload & Parse CV'
              )}
            </button>
            {file && !uploading && (
              <button
                onClick={reset}
                className="px-4 py-2.5 rounded-xl text-sm font-medium text-gray-500 border border-gray-200 hover:bg-gray-50 transition-colors"
              >
                Clear
              </button>
            )}
          </div>
        </>
      ) : (
        <div className="bg-[#e6f7f7] rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle2 size={20} className="text-[#1AA29F]" />
            <h3 className="font-semibold text-[#1AA29F]">CV parsed successfully</h3>
          </div>

          <div className="space-y-2 text-sm">
            {parsedData.name && (
              <p><span className="text-gray-500">Name:</span> <span className="text-gray-800 font-medium">{parsedData.name}</span></p>
            )}
            {parsedData.email && (
              <p><span className="text-gray-500">Email:</span> <span className="text-gray-800 font-medium">{parsedData.email}</span></p>
            )}
            {parsedData.phone && (
              <p><span className="text-gray-500">Phone:</span> <span className="text-gray-800 font-medium">{parsedData.phone}</span></p>
            )}
            {parsedData.skills?.length > 0 && (
              <div>
                <p className="text-gray-500 mb-1.5">Skills detected:</p>
                <div className="flex flex-wrap gap-1.5">
                  {parsedData.skills.map((skill, i) => (
                    <span
                      key={i}
                      className="bg-white text-[#1AA29F] text-xs font-medium px-2.5 py-1 rounded-full border border-[#1AA29F]/30"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <button
            onClick={reset}
            className="mt-4 text-sm text-[#1AA29F] font-medium hover:underline"
          >
            Upload a different CV
          </button>
        </div>
      )}
    </div>
  )
}