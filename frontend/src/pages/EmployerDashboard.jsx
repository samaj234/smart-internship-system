import { useState, useEffect } from 'react'
import { Building2, Plus, Loader2, AlertCircle, Users, MapPin, Clock, DollarSign, Power } from 'lucide-react'
import API from '../api/axios'
import PostInternshipForm from '../components/PostInternshipForm'
import ApplicantsList from '../components/ApplicantsList'
import Pagination from '../components/Pagination'

export default function EmployerDashboard() {
  const [internships, setInternships] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [view, setView] = useState('list')
  const [editingInternship, setEditingInternship] = useState(null)
  const [selectedInternshipId, setSelectedInternshipId] = useState(null)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)

  useEffect(() => {
    let isMounted = true

    const fetchInternships = async () => {
      setLoading(true)
      try {
        const res = await API.get('/internships/my-internships', {
          params: { page, limit: 12 }
        })
        if (isMounted) {
          setInternships(res.data.internships || [])
          setTotalPages(res.data.total_pages || 1)
        }
      } catch (err) {
        if (isMounted) setError('Could not load your internships')
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    fetchInternships()

    return () => {
      isMounted = false
    }
  }, [page])

  const refreshInternships = async () => {
    try {
      const res = await API.get('/internships/my-internships', {
        params: { page, limit: 12 }
      })
      setInternships(res.data.internships || [])
      setTotalPages(res.data.total_pages || 1)
    } catch (err) {
      setError('Could not refresh internships')
    }
  }
  const handlePostSuccess = () => {
    setView('list')
    setEditingInternship(null)
    refreshInternships()
  }

  const handleEdit = (internship) => {
    setEditingInternship(internship)
    setView('post')
  }

  const handleDeactivate = async (internshipId) => {
    try {
      await API.delete(`/internships/${internshipId}`)
      refreshInternships()
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to deactivate internship')
    }
  }

  const handleViewApplicants = (internshipId) => {
    setSelectedInternshipId(internshipId)
    setView('applicants')
  }

  const handleNewPost = () => {
    setEditingInternship(null)
    setView('post')
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-6">
        <Loader2 className="animate-spin text-[#1AA29F]" size={32} />
      </div>
    )
  }

  return (
    <div className="p-6 max-w-5xl mx-auto w-full">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <Building2 size={22} className="text-[#1AA29F]" />
          <h1 className="text-2xl font-bold text-gray-800">Employer Dashboard</h1>
        </div>

        {view === 'list' && (
          <button
            onClick={handleNewPost}
            className="flex items-center gap-1.5 bg-[#1AA29F] hover:bg-[#158a87] text-white px-4 py-2 rounded-xl text-sm font-semibold transition-colors"
          >
            <Plus size={16} /> Post Internship
          </button>
        )}

        {view !== 'list' && (
          <button
            onClick={() => { setView('list'); setEditingInternship(null) }}
            className="text-sm text-[#1AA29F] font-medium hover:underline"
          >
            ← Back to listings
          </button>
        )}
      </div>
      <p className="text-gray-400 text-sm mb-6">
        Post internships, manage listings, and review applicants ranked by SBERT match score.
      </p>

      {error && (
        <div className="flex items-center gap-2 bg-red-50 text-red-600 px-4 py-3 rounded-lg mb-4 text-sm">
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {view === 'post' && (
        <PostInternshipForm
          key={editingInternship?.id || 'new'}
          existing={editingInternship}
          onSuccess={handlePostSuccess}
          onCancel={() => { setView('list'); setEditingInternship(null) }}
        />
      )}

      {view === 'applicants' && selectedInternshipId && (
        <ApplicantsList
          internshipId={selectedInternshipId}
          onBack={() => setView('list')}
        />
      )}
       
      {view === 'list' && (
        internships.length === 0 ? (
          <div className="bg-white rounded-2xl border border-gray-100 p-8 text-center">
            <p className="text-gray-500 text-sm mb-4">You haven't posted any internships yet.</p>
            <button
              onClick={handleNewPost}
              className="bg-[#1AA29F] hover:bg-[#158a87] text-white px-5 py-2 rounded-xl text-sm font-semibold transition-colors"
            >
              Post your first internship
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {internships.map((job) => (
              <div
                key={job.id}
                className="bg-white rounded-2xl border border-gray-100 p-5 flex items-start justify-between gap-4"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-bold text-gray-800">{job.title}</h3>
                    {!job.is_active && (
                      <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-400">
                        Inactive
                      </span>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-3 text-xs text-gray-500 mb-2">
                    {job.location && (
                      <span className="flex items-center gap-1"><MapPin size={12} /> {job.location}</span>
                    )}
                    {job.duration && (
                      <span className="flex items-center gap-1"><Clock size={12} /> {job.duration}</span>
                    )}
                    {job.stipend && (
                      <span className="flex items-center gap-1"><DollarSign size={12} /> {job.stipend}</span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 line-clamp-2">{job.description}</p>
                </div>

                <div className="flex flex-col gap-2 shrink-0">
                  <button
                    onClick={() => handleViewApplicants(job.id)}
                    className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-[#e6f7f7] text-[#1AA29F] hover:bg-[#d0efef] transition-colors"
                  >
                    <Users size={14} /> Applicants
                  </button>
                  <button
                    onClick={() => handleEdit(job)}
                    className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
                  >
                    Edit
                  </button>
                  {job.is_active && (
                    <button
                      onClick={() => handleDeactivate(job.id)}
                      className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg border border-red-200 text-red-500 hover:bg-red-50 transition-colors"
                    >
                      <Power size={14} /> Deactivate
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )
      )}
    </div>
  )
}