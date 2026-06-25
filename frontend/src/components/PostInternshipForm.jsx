import { useState } from 'react'
import { Briefcase, MapPin, Clock, DollarSign, Calendar, Tag, Save, Loader2, X } from 'lucide-react'
import API from '../api/axios'

export default function PostInternshipForm({ existing, onSuccess, onCancel }) {
  const [form, setForm] = useState(() => ({
    title: existing?.title || '',
    description: existing?.description || '',
    required_skills: (existing?.required_skills || []).join(', '),
    location: existing?.location || '',
    duration: existing?.duration || '',
    stipend: existing?.stipend || '',
    deadline: existing?.deadline ? existing.deadline.split('T')[0] : ''
  }))
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

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
      deadline: form.deadline || null
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