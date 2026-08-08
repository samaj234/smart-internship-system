import { useState } from 'react'
import { MapPin, Clock, DollarSign, Calendar, TrendingUp, ChevronDown, ChevronUp, CheckCircle2, XCircle, BookOpen, ExternalLink, FileText, GraduationCap } from 'lucide-react'
import { FaYoutube } from 'react-icons/fa'

export default function MatchCard({ internship, matchPercentage, scoreBreakdown, explanation, learningRecommendations, onApply, applying, applied }) {
  const [showDetails, setShowDetails] = useState(false)
  
  const resourceIcon = (type) => {
  if (type === 'video') return <FaYoutube size={13} className="text-red-500" />
  if (type === 'pdf') return <FileText size={13} className="text-amber-600" />
  if (type === 'course') return <GraduationCap size={13} className="text-[#1AA29F]" />
  return <BookOpen size={13} className="text-amber-500" />
}
const {
  id,
  title,
  description,
  required_skills,
  location,
  duration,
  stipend,
  deadline,
  company_name,
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

  const hasDetails = explanation && (
    explanation.matched_skills?.length > 0 ||
    explanation.missing_skills?.length > 0
  )

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex justify-between items-start mb-2">
      <div>
        <h3 className="text-lg font-bold text-gray-800">{title}</h3>
        {company_name && (
          <p className="text-sm text-gray-500">{company_name}</p>
        )}
      </div>
      {matchPercentage && (
        <span className={`flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full ${getScoreColor(matchPercentage)}`}>
          <TrendingUp size={12} />
          {matchPercentage} match
        </span>
      )}
</div>

      <p className="text-sm text-gray-500 mb-3">{truncatedDescription}</p>

      {/* Meta info */}
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

      {/* Skills */}
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

      {/* Action buttons */}
      <div className="flex gap-2">
        {onApply && (
          <button
            onClick={() => onApply(id)}
            disabled={applying || applied}
            className={`flex-1 py-2 rounded-xl text-sm font-semibold transition-colors
              ${applied
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-[#1AA29F] hover:bg-[#158a87] text-white disabled:opacity-50'
              }`}
          >
            {applied ? 'Applied ✓' : applying ? 'Applying...' : 'Apply Now'}
          </button>
        )}

        {hasDetails && (
          <button
            onClick={() => setShowDetails(prev => !prev)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
          >
            {showDetails ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            {showDetails ? 'Hide details' : 'See details'}
          </button>
        )}
      </div>

      {/* Expandable XAI + Skill Gap + Learning section */}
      {showDetails && hasDetails && (
        <div className="mt-4 pt-4 border-t border-gray-100 space-y-4">

         

          {/* Matched skills */}
          {explanation?.matched_skills?.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-500 mb-2 flex items-center gap-1.5">
                <CheckCircle2 size={13} className="text-[#1AA29F]" />
                Skills you have ({explanation.matched_skills.length} matched)
              </p>
              <div className="flex flex-wrap gap-1.5">
                {explanation.matched_skills.map((skill, i) => (
                  <span
                    key={i}
                    className="bg-[#e6f7f7] text-[#1AA29F] text-xs font-medium px-2.5 py-1 rounded-full border border-[#1AA29F]/20"
                  >
                    ✓ {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Missing skills */}
          {explanation?.missing_skills?.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-500 mb-2 flex items-center gap-1.5">
                <XCircle size={13} className="text-red-400" />
                Skills to develop ({explanation.missing_skills.length} gaps)
              </p>
              <div className="flex flex-wrap gap-1.5">
                {explanation.missing_skills.map((skill, i) => (
                  <span
                    key={i}
                    className="bg-red-50 text-red-500 text-xs font-medium px-2.5 py-1 rounded-full border border-red-200"
                  >
                    ✗ {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Skill match bar */}
          {explanation?.skill_match_percentage !== undefined && (
            <div>
              <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span>Skill coverage</span>
                <span>{explanation.skill_match_percentage}%</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2">
                <div
                  className="bg-[#1AA29F] h-2 rounded-full transition-all"
                  style={{ width: `${explanation.skill_match_percentage}%` }}
                />
              </div>
            </div>
          )}

          {/* Learning recommendations */}
          {learningRecommendations?.length > 0 && (
  <div>
    <p className="text-xs font-semibold text-gray-500 mb-2 flex items-center gap-1.5">
      <BookOpen size={13} className="text-amber-500" />
      Recommended learning resources
    </p>
    <div className="space-y-2">
      {learningRecommendations.slice(0, 3).map((rec, i) => (
        <a
          key={i}
          href={rec.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-start justify-between gap-2 bg-amber-50 hover:bg-amber-100 border border-amber-100 rounded-lg px-3 py-2 transition-colors group"
        >
          <div className="flex items-start gap-2">
            {resourceIcon(rec.type)}
            <div>
              <p className="text-xs font-semibold text-gray-700 group-hover:text-amber-700">
                {rec.skill}
              </p>
              <p className="text-xs text-gray-500">{rec.resource}</p>
              <p className="text-xs text-amber-600">{rec.provider}</p>
            </div>
          </div>
          <ExternalLink size={12} className="text-gray-400 shrink-0 mt-0.5" />
        </a>
      ))}
      {learningRecommendations.length > 3 && (
        <p className="text-xs text-gray-400 text-center">
          +{learningRecommendations.length - 3} more resources
        </p>
      )}
    </div>
  </div>
)}
        </div>
      )}
    </div>
  )
}