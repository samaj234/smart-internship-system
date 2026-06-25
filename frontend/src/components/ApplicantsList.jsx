import { useState, useEffect } from 'react'
import { Loader2, AlertCircle, ArrowLeft, TrendingUp, Check, X, Mail, Phone, GraduationCap } from 'lucide-react'
import API from '../api/axios'
import { useToast } from '../context/ToastContext'

export default function ApplicantsList({ internshipId, onBack }) {
  const [applicants, setApplicants] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [updatingId, setUpdatingId] = useState(null)
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

                <p className="text-xs text-gray-400 mt-2">
                  Applied {new Date(a.applied_at).toLocaleDateString()}
                </p>
              </div>

              <div className="flex flex-col gap-2 shrink-0">
                {a.student.cv_path && (
                  
                   <a href={`http://localhost:5000/${a.student.cv_path}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors text-center"
                  >
                    View CV
                  </a>
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