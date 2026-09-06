import { useState } from 'react'
import { MapPin, Clock, DollarSign, Calendar, ChevronDown, ChevronUp, CheckCircle2, XCircle, BookOpen, ExternalLink, FileText, GraduationCap, Upload, X, Paperclip } from 'lucide-react'
import { FaYoutube } from 'react-icons/fa'

export default function MatchCard({ internship, matchPercentage, scoreBreakdown, explanation, learningRecommendations, onApply, onUnapply, applying, unapplying, applied, isAuthenticated = true, onLoginRequired }) {
  const [showDetails, setShowDetails] = useState(false)
  const [showApplyModal, setShowApplyModal] = useState(false)
  const [confirmingWithdraw, setConfirmingWithdraw] = useState(false)
  const [documents, setDocuments] = useState({ coverLetter: null, recommendationLetter: null })
  const [docErrors, setDocErrors] = useState({})
  
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
  company_industry,
  company_website,
  requires_cover_letter,
  requires_recommendation_letter,
} = internship

  const truncatedDescription = description?.length > 140
    ? description.slice(0, 160) + '...'
    : description

  const getScoreColor = (pct) => {
    const num = parseFloat(pct)
    if (num >= 75) return 'text-[#1AA29F]'
    if (num >= 50) return 'text-amber-600'
    return 'text-gray-500'
  }

  const hasDetails = explanation && (
    explanation.matched_skills?.length > 0 ||
    explanation.missing_skills?.length > 0
  )

  // "View details" is now always available — it used to only appear
  // when there was a match score, which left the plain browsing page
  // (no matchPercentage/explanation) with no way to see the full
  // description, complete skill list, or company info at all.
  const showDetailsButton = true

  const docFields = [
    { key: 'coverLetter', label: 'Cover letter', required: !!requires_cover_letter },
    { key: 'recommendationLetter', label: 'Recommendation letter', required: !!requires_recommendation_letter },
  ]

  const handleFileChange = (key, e) => {
    const file = e.target.files?.[0] || null
    setDocuments(prev => ({ ...prev, [key]: file }))
    if (file) setDocErrors(prev => ({ ...prev, [key]: undefined }))
  }

  const handleRemoveFile = (key) => {
    setDocuments(prev => ({ ...prev, [key]: null }))
  }

  const handleSubmitApplication = () => {
    const errors = {}
    docFields.forEach(({ key, label, required }) => {
      if (required && !documents[key]) errors[key] = `Upload your ${label.toLowerCase()} to continue`
    })
    if (Object.keys(errors).length > 0) {
      setDocErrors(errors)
      return
    }
    onApply(id, documents)
    setShowApplyModal(false)
    setDocuments({ coverLetter: null, recommendationLetter: null })
    setDocErrors({})
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 hover:shadow-md transition-shadow h-full flex flex-col">
      {/* Header */}
      <div className="mb-2">
        <h3 className="text-lg font-bold text-gray-800">{title}</h3>
        {company_name && (
          <p className="text-sm text-gray-500">{company_name}</p>
        )}
      </div>

      <p className="text-sm text-gray-500 mb-3">{truncatedDescription}</p>

      {(requires_cover_letter || requires_recommendation_letter) && (
        <div className="flex items-center gap-1.5 text-xs text-amber-700 bg-amber-50 border border-amber-100 rounded-lg px-2.5 py-1.5 mb-3">
          <Paperclip size={12} className="shrink-0" />
          <span>
            Requires{' '}
            {[requires_cover_letter && 'cover letter', requires_recommendation_letter && 'recommendation letter']
              .filter(Boolean)
              .join(' and ')}
          </span>
        </div>
      )}

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

      {/* Action buttons — mt-auto pins this row to the bottom so cards of
          different content length still line up along the same baseline */}
      <div className="flex gap-2 mt-auto pt-2">
        {onApply && !applied && (
          <button
            onClick={() => {
              if (!isAuthenticated) {
                onLoginRequired?.()
                return
              }
              setShowApplyModal(true)
            }}
            disabled={applying}
            className="flex-1 py-2 rounded-xl text-sm font-semibold transition-colors bg-[#1AA29F] hover:bg-[#158a87] text-white disabled:opacity-50"
          >
            {applying ? 'Applying...' : 'Apply Now'}
          </button>
        )}

        {applied && onUnapply && (
          confirmingWithdraw ? (
            <>
              <button
                onClick={() => { onUnapply(id); setConfirmingWithdraw(false) }}
                disabled={unapplying}
                className="flex-1 py-2 rounded-xl text-sm font-semibold bg-red-500 hover:bg-red-600 text-white disabled:opacity-50 transition-colors"
              >
                {unapplying ? 'Withdrawing...' : 'Confirm withdraw'}
              </button>
              <button
                onClick={() => setConfirmingWithdraw(false)}
                className="px-3 py-2 rounded-xl text-xs font-semibold border border-gray-200 text-gray-500 hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
            </>
          ) : (
            <button
              onClick={() => setConfirmingWithdraw(true)}
              className="flex-1 py-2 rounded-xl text-sm font-semibold border border-red-200 text-red-500 hover:bg-red-50 transition-colors"
            >
              Withdraw application
            </button>
          )
        )}

        {applied && !onUnapply && (
          <button
            disabled
            className="flex-1 py-2 rounded-xl text-sm font-semibold bg-gray-100 text-gray-400 cursor-not-allowed"
          >
            Applied ✓
          </button>
        )}

        {showDetailsButton && (
          <button
            onClick={() => setShowDetails(true)}
            className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors whitespace-nowrap"
          >
            {matchPercentage && (
              <>
                <span className={`font-semibold ${getScoreColor(matchPercentage)}`}>
                  {matchPercentage} match
                </span>
                <span className="w-px h-3.5 bg-gray-200" />
              </>
            )}
            <span className="flex items-center gap-1">
              <ChevronDown size={14} />
              {hasDetails ? 'See details' : 'View details'}
            </span>
          </button>
        )}
      </div>

      {/* Details modal — kept out of the card's normal flow so opening it on
          one card can't stretch the equal-height row it shares with its
          neighbor (see MatchCard grid: h-full + grid stretch ties sibling
          heights to the tallest card in the row).

          Always shows general internship/company info (description,
          full skill list, location/duration/stipend/deadline); the
          match-specific sections (matched/missing skills, skill bar,
          learning resources) only render when explanation data exists,
          i.e. on the student recommendations page. */}
      {showDetails && (
        <div
          className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50"
          onClick={() => setShowDetails(false)}
        >
          <div
            className="bg-white rounded-2xl shadow-lg w-full max-w-md p-5 max-h-[85vh] overflow-y-auto scrollbar-hide"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between mb-1">
              <h4 className="text-base font-bold text-gray-800">{title}</h4>
              <button onClick={() => setShowDetails(false)} className="text-gray-400 hover:text-gray-600">
                <X size={18} />
              </button>
            </div>
            <p className="text-xs text-gray-500 mb-1">
              {company_name}
              {company_industry && <span className="text-gray-400"> · {company_industry}</span>}
            </p>
            {company_website && (
              <a
                href={company_website}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-[#1AA29F] hover:underline"
              >
                {company_website}
              </a>
            )}

            <div className="space-y-4 mt-4">
              {/* Full description — untruncated, unlike the card's preview */}
              {description && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 mb-1.5">About this role</p>
                  <p className="text-sm text-gray-700 whitespace-pre-line">{description}</p>
                </div>
              )}

              {/* Meta info */}
              <div className="flex flex-wrap gap-3 text-xs text-gray-500">
                {location && (
                  <span className="flex items-center gap-1"><MapPin size={13} /> {location}</span>
                )}
                {duration && (
                  <span className="flex items-center gap-1"><Clock size={13} /> {duration}</span>
                )}
                {stipend && (
                  <span className="flex items-center gap-1"><DollarSign size={13} /> {stipend}</span>
                )}
                {deadline && (
                  <span className="flex items-center gap-1"><Calendar size={13} /> Apply by {new Date(deadline).toLocaleDateString()}</span>
                )}
              </div>

              {(requires_cover_letter || requires_recommendation_letter) && (
                <div className="flex items-center gap-1.5 text-xs text-amber-700 bg-amber-50 border border-amber-100 rounded-lg px-2.5 py-1.5">
                  <Paperclip size={12} className="shrink-0" />
                  <span>
                    Requires{' '}
                    {[requires_cover_letter && 'cover letter', requires_recommendation_letter && 'recommendation letter']
                      .filter(Boolean)
                      .join(' and ')}
                  </span>
                </div>
              )}

              {/* Full required skills list — not truncated to 6 like the card */}
              {required_skills?.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 mb-2">Required skills</p>
                  <div className="flex flex-wrap gap-1.5">
                    {required_skills.map((skill, i) => (
                      <span
                        key={i}
                        className="bg-[#e6f7f7] text-[#1AA29F] text-xs font-medium px-2.5 py-1 rounded-full"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

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
          </div>
        </div>
      )}

      {/* Apply modal — collects cover letter and recommendation letter
          before submitting. Certificate isn't collected here: the
          student's profile-level certificate library already surfaces
          to employers on every application, so asking again per-application
          would just create duplicate, possibly inconsistent copies. */}
      {showApplyModal && (
        <div
          className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50"
          onClick={() => setShowApplyModal(false)}
        >
          <div
            className="bg-white rounded-2xl shadow-lg w-full max-w-md p-5 max-h-[85vh] overflow-y-auto scrollbar-hide"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between mb-1">
              <h4 className="text-base font-bold text-gray-800">Apply to {title}</h4>
              <button onClick={() => setShowApplyModal(false)} className="text-gray-400 hover:text-gray-600">
                <X size={18} />
              </button>
            </div>
            <p className="text-xs text-gray-500 mb-4">{company_name}</p>

            <div className="space-y-3">
              {docFields.map(({ key, label, required }) => (
                <div key={key}>
                  <label className="text-xs font-semibold text-gray-600 mb-1 flex items-center gap-1">
                    {label}
                    {required
                      ? <span className="text-red-400">*</span>
                      : <span className="text-gray-400 font-normal">(optional)</span>}
                  </label>

                  {documents[key] ? (
                    <div className="flex items-center justify-between text-xs bg-[#e6f7f7] border border-[#1AA29F]/20 rounded-lg px-3 py-2">
                      <span className="flex items-center gap-1.5 text-gray-700 truncate">
                        <Paperclip size={12} className="shrink-0 text-[#1AA29F]" />
                        <span className="truncate">{documents[key].name}</span>
                      </span>
                      <button onClick={() => handleRemoveFile(key)} className="text-gray-400 hover:text-red-500 shrink-0 ml-2">
                        <X size={14} />
                      </button>
                    </div>
                  ) : (
                    <label className="flex items-center gap-2 text-xs text-gray-500 border border-dashed border-gray-300 rounded-lg px-3 py-2 cursor-pointer hover:bg-gray-50">
                      <Upload size={13} />
                      Choose file
                      <input
                        type="file"
                        accept=".pdf,.doc,.docx"
                        className="hidden"
                        onChange={(e) => handleFileChange(key, e)}
                      />
                    </label>
                  )}

                  {docErrors[key] && (
                    <p className="text-xs text-red-500 mt-1">{docErrors[key]}</p>
                  )}
                </div>
              ))}
            </div>

            <div className="flex gap-2 mt-5">
              <button
                onClick={() => setShowApplyModal(false)}
                className="flex-1 py-2 rounded-xl text-sm font-semibold border border-gray-200 text-gray-600 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitApplication}
                disabled={applying}
                className="flex-1 py-2 rounded-xl text-sm font-semibold bg-[#1AA29F] hover:bg-[#158a87] text-white disabled:opacity-50"
              >
                {applying ? 'Submitting...' : 'Submit application'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}