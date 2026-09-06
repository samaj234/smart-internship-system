import { useState, useEffect } from 'react'
import { Loader2, AlertCircle, ArrowLeft, TrendingUp, Check, X, Mail, Phone, GraduationCap } from 'lucide-react'
import API from '../api/axios'
import { useToast } from '../context/ToastContext'
import { Calendar, PartyPopper } from 'lucide-react'
import { Award } from "lucide-react";

// ── Date formatting helpers for feedback form pre-fill ──
const toDatetimeLocal = (isoString) => {
  if (!isoString) return ''
  const d = new Date(isoString)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const toDateInput = (isoString) => {
  if (!isoString) return ''
  return isoString.split('T')[0]
}

export default function ApplicantsList({ internshipId, onBack }) {
  const [applicants, setApplicants] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [updatingId, setUpdatingId] = useState(null)
  const [feedbackDraft, setFeedbackDraft] = useState({})
  const [expandedId, setExpandedId] = useState(null)
  const [viewingDoc, setViewingDoc] = useState(null)
  const toast = useToast()

  useEffect(() => {
    let isMounted = true

    const fetchApplicants = async () => {
      try {
        const res = await API.get(`/matching/applicants/${internshipId}`)
        if (isMounted) setApplicants(res.data.applicants || [])
      } catch (err) {
        if (isMounted) setError(err.response?.data?.error || 'Could not load applicants')
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    fetchApplicants()

    return () => {
      isMounted = false
    }
  }, [internshipId])

 const handleStatusUpdate = async (applicationId, status) => {
  setUpdatingId(applicationId)
  try {
    await API.patch(`/matching/applications/${applicationId}/status`, { status })
    setApplicants(prev =>
      prev.map(a => a.application_id === applicationId ? { ...a, status } : a)
    )
    toast.success(`Application ${status}`)
  } catch (err) {
    toast.error(err.response?.data?.error || 'Failed to update status')
  } finally {
    setUpdatingId(null)
  }
}

  const handleSendFeedback = async (applicationId) => {
  setUpdatingId(applicationId)
  const draft = feedbackDraft[applicationId] || {}
  try {
    const res = await API.patch(`/matching/applications/${applicationId}/feedback`, {
      feedback_message: draft.message || null,
      interview_date: draft.interviewDate || null,
      start_date: draft.startDate || null,
    })
    setApplicants(prev =>
      prev.map(a => a.application_id === applicationId
        ? {
            ...a,
            feedback_message: res.data.application?.feedback_message,
            interview_date: res.data.application?.interview_date,
            start_date: res.data.application?.start_date,
          }
        : a
      )
    )
    toast.success('Feedback sent')
    setExpandedId(null)
  } catch (err) {
    toast.error(err.response?.data?.error || 'Failed to send feedback')
  } finally {
    setUpdatingId(null)
  }
} 

  const getScoreColor = (pct) => {
    const num = parseFloat(pct)
    if (num >= 75) return 'text-[#1AA29F] bg-[#e6f7f7]'
    if (num >= 50) return 'text-amber-600 bg-amber-50'
    return 'text-gray-500 bg-gray-100'
  }

  const statusBadge = (status) => {
    if (status === 'accepted') return 'bg-[#e6f7f7] text-[#1AA29F]'
    if (status === 'rejected') return 'bg-red-50 text-red-500'
    return 'bg-amber-50 text-amber-600'
  }

  // Certificate/cover-letter/recommendation-letter routes require a JWT,
  // so a plain <a href> won't work — the browser doesn't attach the auth
  // header on a normal navigation. Fetch via axios (which does attach it)
  // and open the result as a blob URL instead, same pattern used in
  // CertificateManager for the student's own certificate view.
  const handleViewDocument = async (path, key) => {
    setViewingDoc(key)
    try {
      const res = await API.get(path, { responseType: 'blob' })
      const blobUrl = window.URL.createObjectURL(res.data)
      window.open(blobUrl, '_blank')
      setTimeout(() => window.URL.revokeObjectURL(blobUrl), 60000)
    } catch (err) {
      toast.error('Could not open document')
    } finally {
      setViewingDoc(null)
    }
  }

  const filenameFromPath = (filepath) => filepath ? filepath.split(/[\\/]/).pop() : null

  if (loading) {
    return (
      <div className="flex items-center justify-center p-10">
        <Loader2 className="animate-spin text-[#1AA29F]" size={28} />
      </div>
    )
  }

  return (
    <div>
      <button
        onClick={onBack}
        className="flex items-center gap-1.5 text-sm text-[#1AA29F] font-medium hover:underline mb-4"
      >
        <ArrowLeft size={15} /> Back to listings
      </button>

      <h2 className="font-bold text-gray-800 mb-1">Applicants</h2>
      <p className="text-gray-400 text-sm mb-5">
        Ranked by SBERT match score — highest compatibility first.
      </p>

      {error && (
        <div className="flex items-center gap-2 bg-red-50 text-red-600 px-4 py-3 rounded-lg mb-4 text-sm">
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {applicants.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-100 p-8 text-center">
          <p className="text-gray-500 text-sm">No applicants yet for this internship.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {applicants.map((a) => (
            <div
              key={a.application_id}
              className="bg-white rounded-2xl border border-gray-100 p-5 flex items-start justify-between gap-4"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1.5">
                  <h3 className="font-bold text-gray-800">{a.student.full_name || 'Unnamed Applicant'}</h3>
                  <span className={`flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full ${getScoreColor(a.match_percentage)}`}>
                    <TrendingUp size={12} />
                    {a.match_percentage} match
                  </span>
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-full capitalize ${statusBadge(a.status)}`}>
                    {a.status}
                  </span>
                </div>

                <div className="flex flex-wrap gap-3 text-xs text-gray-500 mb-2">
                  {a.student.university && (
                    <span className="flex items-center gap-1"><GraduationCap size={12} /> {a.student.university}</span>
                  )}
                  {a.student.phone && (
                    <span className="flex items-center gap-1"><Phone size={12} /> {a.student.phone}</span>
                  )}
                </div>

                {a.student.skills?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {a.student.skills.slice(0, 6).map((skill, i) => (
                      <span
                        key={i}
                        className="bg-[#e6f7f7] text-[#1AA29F] text-xs font-medium px-2.5 py-1 rounded-full"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                )}

                {/* Documents — CV, cover letter, recommendation letter,
                    and any certificates from the student's profile
                    library. All fetched with the auth header attached
                    and opened as a blob in a new tab, since these routes
                    require a JWT that a plain <a href> can't send. */}
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {a.student.cv_path && (
                    <button
                      onClick={() => handleViewDocument(`/students/cv/${filenameFromPath(a.student.cv_path)}`, `cv-${a.application_id}`)}
                      disabled={viewingDoc === `cv-${a.application_id}`}
                      className="text-xs font-medium px-2.5 py-1 rounded-full border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors disabled:opacity-50"
                    >
                      {viewingDoc === `cv-${a.application_id}` ? 'Opening...' : 'View CV'}
                    </button>
                  )}
                  {a.cover_letter_path && (
                    <button
                      onClick={() => handleViewDocument(`/matching/applications/documents/${filenameFromPath(a.cover_letter_path)}`, `cover-${a.application_id}`)}
                      disabled={viewingDoc === `cover-${a.application_id}`}
                      className="text-xs font-medium px-2.5 py-1 rounded-full border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors disabled:opacity-50"
                    >
                      {viewingDoc === `cover-${a.application_id}` ? 'Opening...' : 'View cover letter'}
                    </button>
                  )}
                  {a.recommendation_letter_path && (
                    <button
                      onClick={() => handleViewDocument(`/matching/applications/documents/${filenameFromPath(a.recommendation_letter_path)}`, `rec-${a.application_id}`)}
                      disabled={viewingDoc === `rec-${a.application_id}`}
                      className="text-xs font-medium px-2.5 py-1 rounded-full border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors disabled:opacity-50"
                    >
                      {viewingDoc === `rec-${a.application_id}` ? 'Opening...' : 'View recommendation letter'}
                    </button>
                  )}
                  {a.certificates?.map((cert) => (
                    <button
                      key={cert.id}
                      onClick={() => handleViewDocument(`/students/certificates/${cert.id}/file`, `cert-${cert.id}`)}
                      disabled={viewingDoc === `cert-${cert.id}`}
                      title={cert.original_filename}
                      className="text-xs font-medium px-2.5 py-1 rounded-full border border-amber-200 text-amber-700 bg-amber-50 hover:bg-amber-100 transition-colors truncate max-w-[160px] disabled:opacity-50"
                    >
                      {viewingDoc === `cert-${cert.id}` ? 'Opening...' : cert.original_filename}
                    </button>
                  ))}
                </div>

                <p className="text-xs text-gray-400 mt-2">
                  Applied {new Date(a.applied_at).toLocaleDateString()}
                </p>

                {/* Existing feedback summary, shown even when form is collapsed */}
                {(a.feedback_message || a.interview_date || a.start_date) && (
                  <div className="mt-3 pt-3 border-t border-gray-100 space-y-1">
                    {a.feedback_message && (
                      <p className="text-xs text-gray-600">{a.feedback_message}</p>
                    )}
                    {a.interview_date && (
                      <p className="text-xs text-[#1AA29F] font-medium">
                         <Calendar size={13} />Interview: {new Date(a.interview_date).toLocaleString()}
                      </p>
                    )}
                    {a.start_date && (
                      <p className="text-xs text-[#1AA29F] font-medium">
                        <PartyPopper size={13} /> Start date: {new Date(a.start_date).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                )}

                {/* Expandable feedback form */}
                {expandedId === a.application_id && (
                  <div className="mt-3 p-3 bg-gray-50 rounded-xl space-y-2 max-w-sm">
                    <div>
                      <label className="text-xs text-gray-500">Message to candidate</label>
                      <textarea
                        rows={2}
                        placeholder="Optional message..."
                        className="w-full text-xs border border-gray-200 rounded-lg p-2 mt-1 outline-none focus:border-[#1AA29F] bg-white"
                        value={feedbackDraft[a.application_id]?.message || ''}
                        onChange={(e) => setFeedbackDraft(prev => ({
                          ...prev,
                          [a.application_id]: { ...prev[a.application_id], message: e.target.value }
                        }))}
                      />
                    </div>
                    <div>
                      <label className="text-xs text-gray-500">Interview date & time</label>
                      <input
                        type="datetime-local"
                        className="w-full text-xs border border-gray-200 rounded-lg p-2 mt-1 outline-none focus:border-[#1AA29F] bg-white"
                        value={feedbackDraft[a.application_id]?.interviewDate || ''}
                        onChange={(e) => setFeedbackDraft(prev => ({
                          ...prev,
                          [a.application_id]: { ...prev[a.application_id], interviewDate: e.target.value }
                        }))}
                      />
                    </div>
                    <div>
                      <label className="text-xs text-gray-500">Proposed start date</label>
                      <input
                        type="date"
                        className="w-full text-xs border border-gray-200 rounded-lg p-2 mt-1 outline-none focus:border-[#1AA29F] bg-white"
                        value={feedbackDraft[a.application_id]?.startDate || ''}
                        onChange={(e) => setFeedbackDraft(prev => ({
                          ...prev,
                          [a.application_id]: { ...prev[a.application_id], startDate: e.target.value }
                        }))}
                      />
                    </div>
                  </div>
                )}
              </div>

              <div className="flex flex-col gap-2 shrink-0">
                <button
                  onClick={() => {
                    const nextId = expandedId === a.application_id ? null : a.application_id
                    setExpandedId(nextId)

                    if (nextId && !feedbackDraft[a.application_id]) {
                      setFeedbackDraft(prev => ({
                        ...prev,
                        [a.application_id]: {
                          message: a.feedback_message || '',
                          interviewDate: toDatetimeLocal(a.interview_date),
                          startDate: toDateInput(a.start_date),
                        }
                      }))
                    }
                  }}
                  className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
                >
                  {expandedId === a.application_id ? 'Hide' : 'Add'} feedback
                </button>

                {a.status !== 'pending' && expandedId === a.application_id && (
                    <button
                      onClick={() => handleSendFeedback(a.application_id)}
                      disabled={updatingId === a.application_id}
                      className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-[#1AA29F] text-white hover:bg-[#158a87] disabled:opacity-50 transition-colors"
                    >
                      {updatingId === a.application_id ? 'Sending...' : 'Send Feedback'}
                    </button>
                  )}
                                  <button
                  onClick={() => handleStatusUpdate(a.application_id, 'accepted')}
                  disabled={updatingId === a.application_id || a.status === 'accepted'}
                  className="flex items-center justify-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-[#e6f7f7] text-[#1AA29F] hover:bg-[#d0efef] disabled:opacity-50 transition-colors"
                >
                  <Check size={14} /> Accept
                </button>
                <button
                  onClick={() => handleStatusUpdate(a.application_id, 'rejected')}
                  disabled={updatingId === a.application_id || a.status === 'rejected'}
                  className="flex items-center justify-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg border border-red-200 text-red-500 hover:bg-red-50 disabled:opacity-50 transition-colors"
                >
                  <X size={14} /> Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}