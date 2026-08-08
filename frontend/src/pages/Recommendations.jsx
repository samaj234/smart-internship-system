import { useState, useEffect } from 'react'
import { Loader2, Sparkles, AlertCircle, CheckCircle2 } from 'lucide-react'
import API from '../api/axios'
import MatchCard from '../components/MatchCard'
import { useToast } from '../context/ToastContext'

export default function Recommendations() {
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setBannerError] = useState('')
  const [applyingId, setApplyingId] = useState(null)
  const [appliedIds, setAppliedIds] = useState(new Set())
  const toast = useToast()

  useEffect(() => {
    let isMounted = true

    const fetchData = async () => {
      try {
        // Fetch recommendations and existing applications in parallel
        const [recRes, appsRes] = await Promise.all([
          API.get('/matching/recommendations'),
          API.get('/matching/my-applications')
        ])

        if (!isMounted) return

        setRecommendations(recRes.data.recommendations || [])

        // Pre-populate appliedIds from existing applications
        const existingIds = new Set(
          (appsRes.data.applications || [])
            .map(app => app.internship?.id)
            .filter(Boolean)
        )
        setAppliedIds(existingIds)

      } catch (err) {
        if (isMounted) {
          setBannerError(
            err.response?.data?.error || 'Could not load recommendations'
          )
        }
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    fetchData()

    return () => { isMounted = false }
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

  // Split recommendations into applied and not applied
  const notApplied = recommendations.filter(rec => !appliedIds.has(rec.internship.id))
  const applied = recommendations.filter(rec => appliedIds.has(rec.internship.id))

  return (
    <div className="p-6 max-w-5xl mx-auto w-full">
      <div className="flex items-center gap-2 mb-1">
        <Sparkles size={22} className="text-[#1AA29F]" />
        <h1 className="text-2xl font-bold text-gray-800">My Matches</h1>
      </div>
      <p className="text-gray-400 text-sm mb-6">
        Internships ranked by how well they match your profile, powered by hybrid SBERT + TF-IDF matching.
      </p>

      {error && (
        <div className="flex items-center gap-2 bg-amber-50 text-amber-700 px-4 py-3 rounded-lg mb-4 text-sm">
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {recommendations.length === 0 && !error ? (
        <div className="bg-white rounded-2xl border border-gray-100 p-8 text-center">
          <p className="text-gray-500 text-sm">
            No matches yet. Make sure you've uploaded your CV and added skills to your profile.
          </p>
        </div>
      ) : (
        <div className="space-y-8">

          {/* Not yet applied section */}
          {notApplied.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-4">
                <h2 className="text-lg font-bold text-gray-700">
                  Available Matches
                </h2>
                <span className="bg-[#e6f7f7] text-[#1AA29F] text-xs font-semibold px-2.5 py-1 rounded-full">
                  {notApplied.length}
                </span>
              </div>
              <div className="grid md:grid-cols-2 gap-5 items-start">
                {notApplied.map((rec) => (
                  <MatchCard
                    key={rec.internship.id}
                    internship={rec.internship}
                    matchPercentage={rec.match_percentage}
                    scoreBreakdown={rec.score_breakdown}
                    explanation={rec.explanation}
                    learningRecommendations={rec.learning_recommendations}
                    onApply={handleApply}
                    applying={applyingId === rec.internship.id}
                    applied={false}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Already applied section */}
          {applied.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-4">
                <CheckCircle2 size={18} className="text-[#1AA29F]" />
                <h2 className="text-lg font-bold text-gray-700">
                  Already Applied
                </h2>
                <span className="bg-gray-100 text-gray-500 text-xs font-semibold px-2.5 py-1 rounded-full">
                  {applied.length}
                </span>
              </div>
              <div className="grid md:grid-cols-2 gap-5 items-start">
                {applied.map((rec) => (
                  <MatchCard
                    key={rec.internship.id}
                    internship={rec.internship}
                    matchPercentage={rec.match_percentage}
                    scoreBreakdown={rec.score_breakdown}
                    explanation={rec.explanation}
                    learningRecommendations={rec.learning_recommendations}
                    onApply={handleApply}
                    applying={false}
                    applied={true}
                  />
                ))}
              </div>
            </div>
          )}

        </div>
      )}
    </div>
  )
}