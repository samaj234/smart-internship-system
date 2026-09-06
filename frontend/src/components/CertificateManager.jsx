import { useState, useEffect, useRef } from 'react'
import { Plus, Trash2, Loader2, FileText, Eye } from 'lucide-react'
import API from '../api/axios'
import { useToast } from '../context/ToastContext'

const ALLOWED_TYPES = ['.pdf', '.docx', '.jpg', '.jpeg', '.png']
const MAX_SIZE_MB = 5

export default function CertificateManager() {
  const [certificates, setCertificates] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [deletingId, setDeletingId] = useState(null)
  const [viewingId, setViewingId] = useState(null)
  const inputRef = useRef(null)
  const toast = useToast()

  useEffect(() => {
    let isMounted = true
    const fetchCertificates = async () => {
      try {
        const res = await API.get('/students/certificates')
        if (isMounted) setCertificates(res.data.certificates || [])
      } catch (err) {
        if (isMounted) toast.error('Could not load certificates')
      } finally {
        if (isMounted) setLoading(false)
      }
    }
    fetchCertificates()
    return () => { isMounted = false }
  }, [])

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    const ext = '.' + file.name.split('.').pop().toLowerCase()
    if (!ALLOWED_TYPES.includes(ext)) {
      toast.error('Only PDF, DOCX, JPG, and PNG files allowed')
      return
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      toast.error(`File must be smaller than ${MAX_SIZE_MB}MB`)
      return
    }

    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await API.post('/students/certificates', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setCertificates(prev => [res.data.certificate, ...prev])
      toast.success('Certificate uploaded')
    } catch (err) {
      toast.error(err.response?.data?.error || 'Upload failed')
    } finally {
      setUploading(false)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  const handleDelete = async (certificateId) => {
    setDeletingId(certificateId)
    try {
      await API.delete(`/students/certificates/${certificateId}`)
      setCertificates(prev => prev.filter(c => c.id !== certificateId))
      toast.success('Certificate removed')
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to delete certificate')
    } finally {
      setDeletingId(null)
    }
  }

  // Opens the certificate in a new tab instead of forcing a download.
  // PDFs, JPGs, and PNGs render inline in the browser; DOCX files will
  // still prompt a download since browsers can't preview that format —
  // that's a browser limitation, not something fixable client-side.
  const handleView = async (certificateId) => {
    setViewingId(certificateId)
    try {
      const res = await API.get(`/students/certificates/${certificateId}/file`, {
        responseType: 'blob'
      })
      const blobUrl = window.URL.createObjectURL(res.data)
      window.open(blobUrl, '_blank')
      // Revoke after a delay rather than immediately — the new tab needs
      // the URL to still be valid while it loads the content.
      setTimeout(() => window.URL.revokeObjectURL(blobUrl), 60000)
    } catch (err) {
      toast.error('Could not open certificate')
    } finally {
      setViewingId(null)
    }
  }

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx,.jpg,.jpeg,.png"
        onChange={handleFileSelect}
        className="hidden"
      />

      <div className="flex flex-wrap items-center gap-2">
        {loading ? (
          <Loader2 className="animate-spin text-[#1AA29F]" size={16} />
        ) : (
          <>
            {certificates.map((cert) => (
              <div
                key={cert.id}
                className="group flex items-center gap-1.5 bg-[#e6f7f7] text-[#1AA29F] text-xs font-medium pl-2.5 pr-1 py-1 rounded-full"
              >
                <FileText size={12} className="shrink-0" />
                <button
                  onClick={() => handleView(cert.id)}
                  disabled={viewingId === cert.id}
                  className="max-w-[140px] truncate hover:underline flex items-center gap-1 disabled:opacity-50"
                  title="View"
                >
                  {viewingId === cert.id ? <Loader2 size={11} className="animate-spin shrink-0" /> : <Eye size={11} className="shrink-0" />}
                  {cert.original_filename}
                </button>
                <button
                  onClick={() => handleDelete(cert.id)}
                  disabled={deletingId === cert.id}
                  className="p-0.5 rounded-full text-[#1AA29F]/60 hover:text-red-500 hover:bg-white/60 transition-colors disabled:opacity-50"
                  aria-label="Delete certificate"
                >
                  {deletingId === cert.id ? <Loader2 size={11} className="animate-spin" /> : <Trash2 size={11} />}
                </button>
              </div>
            ))}

            <button
              onClick={() => inputRef.current?.click()}
              disabled={uploading}
              className="flex items-center gap-1 text-xs font-semibold px-2.5 py-1.5 rounded-full border border-dashed border-gray-300 text-gray-500 hover:border-[#1AA29F] hover:text-[#1AA29F] transition-colors disabled:opacity-50"
            >
              {uploading ? <Loader2 size={12} className="animate-spin" /> : <Plus size={12} />}
              {uploading ? 'Uploading...' : 'Add certificate'}
            </button>
          </>
        )}
      </div>

      {!loading && certificates.length === 0 && (
        <p className="text-xs text-gray-400 italic mt-1">No certificates uploaded yet</p>
      )}
    </div>
  )
}