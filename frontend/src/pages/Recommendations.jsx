import { useState, useEffect } from 'react'
import { Loader2, Sparkles, AlertCircle } from 'lucide-react'
import API from '../api/axios'
import MatchCard from '../components/MatchCard'
import { useToast } from '../context/ToastContext'

export default function Recommendations() {
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(true)
  const [bannerError, setBannerError] = useState('')
  const [applyingId, setApplyingId] = useState(null)
  const [appliedIds, setAppliedIds] = useState(new Set())
  const toast = useToast()

  useEffect(() => {
    let isMounted = true

    const fetchRecommendations = async () => {
      try {
        const res = await API.get('/matching/recommendations')
        if (isMounted) {
          setRecommendations(res.data.recommendations || [])
          setBannerError('')
        }
      } catch (err) {
        if (isMounted) {
          setBannerError(err.response?.data?.error || 'Could not load recommendations')
        }
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    fetchRecommendations()

    return () => {
      isMounted = false
    }
  }, [])

  const handleApply = async (internshipId) => {
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

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-6">
        <Loader2 className="animate-spin text-[#1AA29F]" size={32} />
      </div>
    )
  }

  return (
    <div className="p-6 max-w-5xl mx-auto w-full">
      <div className="flex items-center gap-2 mb-1">
        <Sparkles size={22} className="text-[#1AA29F]" />
        <h1 className="text-2xl font-bold text-gray-800">My Matches</h1>
      </div>
      <p className="text-gray-400 text-sm mb-6">
        Internships ranked by how well they match your profile, powered by SBERT similarity.
      </p>

      {bannerError && (
        <div className="flex items-center gap-2 bg-amber-50 text-amber-700 px-4 py-3 rounded-lg mb-4 text-sm">
          <AlertCircle size={16} />
          {bannerError}
        </div>
      )}

      {recommendations.length === 0 && !bannerError ? (
        <div className="bg-white rounded-2xl border border-gray-100 p-8 text-center">
          <p className="text-gray-500 text-sm">
            No matches yet. Make sure you've uploaded your CV and added skills to your profile
            so we can find internships for you.
          </p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-5">
          {recommendations.map((rec) => (
            <MatchCard
              key={rec.internship.id}
              internship={rec.internship}
              matchPercentage={rec.match_percentage}
              onApply={handleApply}
              applying={applyingId === rec.internship.id}
              applied={appliedIds.has(rec.internship.id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}