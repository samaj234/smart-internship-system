import { MapPin, Clock, DollarSign, Calendar, TrendingUp } from 'lucide-react'

export default function MatchCard({ internship, matchPercentage, onApply, applying, applied }) {
  const {
    id,
    title,
    description,
    required_skills,
    location,
    duration,
    stipend,
    deadline,
  } = internship

  const truncatedDescription = description?.length > 140
    ? description.slice(0, 140) + '...'
    : description

  const getScoreColor = (pct) => {
    const num = parseFloat(pct)
    if (num >= 75) return 'text-[#1AA29F] bg-[#e6f7f7]'
    if (num >= 50) return 'text-amber-600 bg-amber-50'
    return 'text-gray-500 bg-gray-100'
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-lg font-bold text-gray-800">{title}</h3>
        {matchPercentage && (
          <span className={`flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full ${getScoreColor(matchPercentage)}`}>
            <TrendingUp size={12} />
            {matchPercentage} match
          </span>
        )}
      </div>

      <p className="text-sm text-gray-500 mb-3">{truncatedDescription}</p>

      <div className="flex flex-wrap gap-3 text-xs text-gray-500 mb-3">
        {location && (
          <span className="flex items-center gap-1">
            <MapPin size={13} /> {location}
          </span>
        )}
        {duration && (
          <span className="flex items-center gap-1">
            <Clock size={13} /> {duration}
          </span>
        )}
        {stipend && (
          <span className="flex items-center gap-1">
            <DollarSign size={13} /> {stipend}
          </span>
        )}
        {deadline && (
          <span className="flex items-center gap-1">
            <Calendar size={13} /> {new Date(deadline).toLocaleDateString()}
          </span>
        )}
      </div>

      {required_skills?.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-4">
          {required_skills.slice(0, 6).map((skill, i) => (
            <span
              key={i}
              className="bg-[#e6f7f7] text-[#1AA29F] text-xs font-medium px-2.5 py-1 rounded-full"
            >
              {skill}
            </span>
          ))}
          {required_skills.length > 6 && (
            <span className="text-xs text-gray-400 px-1 py-1">
              +{required_skills.length - 6} more
            </span>
          )}
        </div>
      )}

      {onApply && (
        <button
          onClick={() => onApply(id)}
          disabled={applying || applied}
          className={`w-full py-2 rounded-xl text-sm font-semibold transition-colors
            ${applied
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'bg-[#1AA29F] hover:bg-[#158a87] text-white disabled:opacity-50'
            }`}
        >
          {applied ? 'Applied ✓' : applying ? 'Applying...' : 'Apply Now'}
        </button>
      )}
    </div>
  )
}