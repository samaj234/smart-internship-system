import { useState, useEffect } from 'react'
import { Loader2, Briefcase, AlertCircle, Search } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import API from '../api/axios'
import MatchCard from '../components/MatchCard'
import Pagination from '../components/Pagination'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

export default function Internships() {
  const [internships, setInternships] = useState([])
  const [loading, setLoading] = useState(true)
  const [bannerError, setBannerError] = useState('')
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalResults, setTotalResults] = useState(0)
  const [applyingId, setApplyingId] = useState(null)
  const [appliedIds, setAppliedIds] = useState(new Set())
  const { user } = useAuth()
  const navigate = useNavigate()
  const toast = useToast()

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search)
      setPage(1)
    }, 400)
    return () => clearTimeout(timer)
  }, [search])

  useEffect(() => {
    let isMounted = true

    const fetchInternships = async () => {
      setLoading(true)
      try {
        const res = await API.get('/internships/', {
          params: { page, limit: 12, search: debouncedSearch }
        })
        if (isMounted) {
          setInternships(res.data.internships || [])
          setTotalPages(res.data.total_pages || 1)
          setTotalResults(res.data.total_results || 0)
          setBannerError('')
        }
      } catch (err) {
        if (isMounted) setBannerError('Could not load internships')
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    fetchInternships()

    return () => {
      isMounted = false
    }
  }, [page, debouncedSearch])

  const handleApply = async (internshipId) => {
    if (!user) {
      navigate('/login')
      return
    }
    if (user.role !== 'student') {
      setBannerError('Only students can apply to internships')
      return
    }

    setApplyingId(internshipId)
    try {
      await API.post(`/matching/apply/${internshipId}`)
      setAppliedIds(prev => new Set(prev).add(internshipId))
      toast.success('Application submitted!')
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to apply')
    } finally {
      setApplyingId(null)
    }
  }

  const handlePageChange = (newPage) => {
    setPage(newPage)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="p-6 max-w-5xl mx-auto w-full">
      <div className="flex items-center gap-2 mb-1">
        <Briefcase size={22} className="text-[#1AA29F]" />
        <h1 className="text-2xl font-bold text-gray-800">Internships</h1>
      </div>
      <p className="text-gray-400 text-sm mb-5">
        Browse all open internships{user?.role === 'student' ? ' or check your personalized matches instead' : ''}.
      </p>

      <div className="relative mb-2 max-w-md">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Search by title..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full border border-gray-200 rounded-xl pl-9 pr-4 py-2.5 text-sm outline-none focus:border-[#1AA29F] transition-colors"
        />
      </div>

      {!loading && (
        <p className="text-xs text-gray-400 mb-4">
          {totalResults} internship{totalResults !== 1 ? 's' : ''} found
        </p>
      )}

      {bannerError && (
        <div className="flex items-center gap-2 bg-amber-50 text-amber-700 px-4 py-3 rounded-lg mb-4 text-sm">
          <AlertCircle size={16} />
          {bannerError}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center p-10">
          <Loader2 className="animate-spin text-[#1AA29F]" size={32} />
        </div>
      ) : internships.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-100 p-8 text-center">
          <p className="text-gray-500 text-sm">
            {debouncedSearch ? 'No internships match your search.' : 'No internships are currently posted.'}
          </p>
        </div>
      ) : (
        <>
          <div className="grid md:grid-cols-2 gap-5">
            {internships.map((job) => (
              <MatchCard
                key={job.id}
                internship={job}
                onApply={handleApply}
                applying={applyingId === job.id}
                applied={appliedIds.has(job.id)}
              />
            ))}
          </div>
          <Pagination page={page} totalPages={totalPages} onPageChange={handlePageChange} />
        </>
      )}
    </div>
  )
}