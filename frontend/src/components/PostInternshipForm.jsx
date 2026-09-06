import { useState, useRef } from 'react'
import { Briefcase, MapPin, Clock, DollarSign, Calendar, Tag, Save, Loader2, X, Paperclip, Upload } from 'lucide-react'
import API from '../api/axios'

export default function PostInternshipForm({ existing, onSuccess, onCancel }) {
  const [form, setForm] = useState(() => ({
    title: existing?.title || '',
    description: existing?.description || '',
    required_skills: (existing?.required_skills || []).join(', '),
    location: existing?.location || '',
    duration: existing?.duration || '',
    stipend: existing?.stipend || '',
    deadline: existing?.deadline ? existing.deadline.split('T')[0] : '',
    requires_cover_letter: existing?.requires_cover_letter || false,
    requires_recommendation_letter: existing?.requires_recommendation_letter || false
  }))
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [parsing, setParsing] = useState(false)
  const fileInputRef = useRef(null)

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    setParsing(true)
    setError('')
    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await API.post('/internships/parse', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      const parsed = res.data.parsed || {}

      // Only overwrite fields the parser actually found something for —
      // deadline is deliberately never touched here, and any field the
      // parser couldn't confidently extract stays whatever the employer
      // had already typed rather than getting blanked out.
      setForm(prev => ({
        ...prev,
        title: parsed.title || prev.title,
        description: parsed.description || prev.description,
        required_skills: parsed.required_skills?.length
          ? parsed.required_skills.join(', ')
          : prev.required_skills,
        location: parsed.location || prev.location,
        duration: parsed.duration || prev.duration,
        stipend: parsed.stipend || prev.stipend,
      }))
    } catch (err) {
      setError(err.response?.data?.error || 'Could not parse that file — please fill the form in manually')
    } finally {
      setParsing(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!form.title.trim() || !form.description.trim()) {
      setError('Title and description are required')
      return
    }

    setSaving(true)

    const payload = {
      title: form.title.trim(),
      description: form.description.trim(),
      required_skills: form.required_skills
        .split(',')
        .map(s => s.trim())
        .filter(Boolean),
      location: form.location.trim(),
      duration: form.duration.trim(),
      stipend: form.stipend.trim(),
      deadline: form.deadline || null,
      requires_cover_letter: form.requires_cover_letter,
      requires_recommendation_letter: form.requires_recommendation_letter
    }

    try {
      if (existing) {
        await API.put(`/internships/${existing.id}`, payload)
      } else {
        await API.post('/internships/', payload)
      }
      onSuccess()
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save internship')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-6 max-w-2xl">
      <div className="flex items-center justify-between mb-5">
        <h2 className="font-bold text-gray-800 flex items-center gap-2">
          <Briefcase size={18} className="text-[#1AA29F]" />
          {existing ? 'Edit Internship' : 'Post a New Internship'}
        </h2>
        <button
          onClick={onCancel}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X size={18} />
        </button>
      </div>

      {error && (
        <div className="bg-red-50 text-red-600 px-4 py-2 rounded-lg mb-4 text-sm">{error}</div>
      )}

      <form onSubmit={handleSubmit} className="space-y-3">
        {!existing && (
          <div className="border border-dashed border-gray-200 rounded-xl px-4 py-3 flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-medium text-gray-700">Have a job description file?</p>
              <p className="text-xs text-gray-400">Upload a PDF or DOCX and we'll pre-fill the form below — you can still review and edit everything before posting.</p>
            </div>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={parsing}
              className="flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors disabled:opacity-50 whitespace-nowrap"
            >
              {parsing ? <Loader2 size={13} className="animate-spin" /> : <Upload size={13} />}
              {parsing ? 'Parsing...' : 'Upload file'}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx"
              className="hidden"
              onChange={handleFileUpload}
            />
          </div>
        )}

        <div className="relative border rounded-xl px-3 pt-4 pb-2 focus-within:border-[#1AA29F]">
          <label className="absolute top-1 left-3 text-xs text-[#1AA29F] font-medium">Title *</label>
          <input
            type="text"
            placeholder="Frontend Developer Intern"
            className="w-full outline-none text-sm text-gray-700 bg-transparent"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
          />
        </div>

        <div className="relative border rounded-xl px-3 pt-4 pb-2 focus-within:border-[#1AA29F]">
          <label className="absolute top-1 left-3 text-xs text-[#1AA29F] font-medium">Description *</label>
          <textarea
            rows={4}
            placeholder="Describe the role, responsibilities, and what makes a great candidate..."
            className="w-full outline-none text-sm text-gray-700 bg-transparent resize-none"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
        </div>

        <div className="relative border rounded-xl px-3 pt-4 pb-2 focus-within:border-[#1AA29F]">
          <label className="absolute top-1 left-3 text-xs text-[#1AA29F] font-medium">Required Skills (comma separated)</label>
          <div className="flex items-start gap-2">
            <Tag size={14} className="text-gray-400 mt-1" />
            <input
              type="text"
              placeholder="Python, React, SQL..."
              className="flex-1 outline-none text-sm text-gray-700 bg-transparent"
              value={form.required_skills}
              onChange={(e) => setForm({ ...form, required_skills: e.target.value })}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="relative border rounded-xl px-3 pt-4 pb-2 focus-within:border-[#1AA29F]">
            <label className="absolute top-1 left-3 text-xs text-[#1AA29F] font-medium">Location</label>
            <div className="flex items-center gap-2">
              <MapPin size={14} className="text-gray-400" />
              <input
                type="text"
                placeholder="Accra, Remote..."
                className="flex-1 outline-none text-sm text-gray-700 bg-transparent"
                value={form.location}
                onChange={(e) => setForm({ ...form, location: e.target.value })}
              />
            </div>
          </div>

          <div className="relative border rounded-xl px-3 pt-4 pb-2 focus-within:border-[#1AA29F]">
            <label className="absolute top-1 left-3 text-xs text-[#1AA29F] font-medium">Duration</label>
            <div className="flex items-center gap-2">
              <Clock size={14} className="text-gray-400" />
              <input
                type="text"
                placeholder="3 months"
                className="flex-1 outline-none text-sm text-gray-700 bg-transparent"
                value={form.duration}
                onChange={(e) => setForm({ ...form, duration: e.target.value })}
              />
            </div>
          </div>

          <div className="relative border rounded-xl px-3 pt-4 pb-2 focus-within:border-[#1AA29F]">
            <label className="absolute top-1 left-3 text-xs text-[#1AA29F] font-medium">Stipend</label>
            <div className="flex items-center gap-2">
              <DollarSign size={14} className="text-gray-400" />
              <input
                type="text"
                placeholder="GHS 500/month"
                className="flex-1 outline-none text-sm text-gray-700 bg-transparent"
                value={form.stipend}
                onChange={(e) => setForm({ ...form, stipend: e.target.value })}
              />
            </div>
          </div>

          <div className="relative border rounded-xl px-3 pt-4 pb-2 focus-within:border-[#1AA29F]">
            <label className="absolute top-1 left-3 text-xs text-[#1AA29F] font-medium">Application Deadline</label>
            <div className="flex items-center gap-2">
              <Calendar size={14} className="text-gray-400" />
              <input
                type="date"
                className="flex-1 outline-none text-sm text-gray-700 bg-transparent"
                value={form.deadline}
                onChange={(e) => setForm({ ...form, deadline: e.target.value })}
              />
            </div>
          </div>
        </div>

        <div className="border rounded-xl px-4 py-3">
          <p className="text-xs text-[#1AA29F] font-medium flex items-center gap-1.5 mb-2">
            <Paperclip size={13} />
            Application requirements
          </p>
          <p className="text-xs text-gray-400 mb-3">
            Choose which documents students must attach when they apply. A certificate is always optional — students can attach one if they have it.
          </p>
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
              <input
                type="checkbox"
                className="accent-[#1AA29F]"
                checked={form.requires_cover_letter}
                onChange={(e) => setForm({ ...form, requires_cover_letter: e.target.checked })}
              />
              Require a cover letter
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
              <input
                type="checkbox"
                className="accent-[#1AA29F]"
                checked={form.requires_recommendation_letter}
                onChange={(e) => setForm({ ...form, requires_recommendation_letter: e.target.checked })}
              />
              Require a recommendation letter
            </label>
          </div>
        </div>

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={saving}
            className="flex-1 flex items-center justify-center gap-2 bg-[#1AA29F] hover:bg-[#158a87] text-white py-2.5 rounded-xl font-semibold text-sm disabled:opacity-50 transition-colors"
          >
            {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
            {saving ? 'Saving...' : existing ? 'Update Internship' : 'Post Internship'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="px-5 py-2.5 rounded-xl text-sm font-medium text-gray-500 border border-gray-200 hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}