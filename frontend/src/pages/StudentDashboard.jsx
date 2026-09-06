import { useState, useEffect, useRef } from 'react'
import { User, Phone, GraduationCap, Award, Save, Loader2, Pencil, X, BarChart3 } from 'lucide-react'
import API from '../api/axios'
import CVUpload from '../components/CVUpload'
import CertificateManager from '../components/CertificateManager'
import { useToast } from '../context/ToastContext'
import { Calendar, PartyPopper } from 'lucide-react'

export default function StudentDashboard() {
  const [profile, setProfile] = useState(null)
  const [form, setForm] = useState({
    full_name: '', phone: '', university: '', degree: '', gpa: '', skills: ''
  })
  const [applications, setApplications] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const toast = useToast()

  // Use a ref to store the saved profile for cancel/reset
  // This avoids the stale closure issue that was causing
  // syncFormFromProfile to fire on every keystroke
  const savedProfileRef = useRef(null)

  useEffect(() => {
    let isMounted = true

    const fetchData = async () => {
      try {
        const profileRes = await API.get('/students/profile')
        if (!isMounted) return

        const profileData = profileRes.data
        savedProfileRef.current = profileData
        setProfile(profileData)

        // Only set form once on initial load
        setForm({
          full_name: profileData.full_name || '',
          phone: profileData.phone || '',
          university: profileData.university || '',
          degree: profileData.degree || '',
          gpa: profileData.gpa ?? '',
          skills: (profileData.skills || []).join(', ')
        })
      } catch (err) {
        if (isMounted) toast.error('Could not load profile')
      } finally {
        if (isMounted) setLoading(false)
      }

      try {
        const appsRes = await API.get('/matching/my-applications')
        if (isMounted) {
          // Internships the employer has withdrawn/deactivated come back
          // with status "withdrawn" — filter those out rather than
          // showing a dead-end application in the list.
          const active = (appsRes.data.applications || []).filter(
            (app) => app.status !== 'withdrawn'
          )
          setApplications(active)
        }
      } catch (err) {
        if (isMounted) setApplications([])
      }
    }

    fetchData()

    return () => { isMounted = false }
  }, []) // empty deps — runs once only

  const handleEditClick = () => {
    // Reset form to last saved values from ref
    const saved = savedProfileRef.current
    if (saved) {
      setForm({
        full_name: saved.full_name || '',
        phone: saved.phone || '',
        university: saved.university || '',
        degree: saved.degree || '',
        gpa: saved.gpa ?? '',
        skills: (saved.skills || []).join(', ')
      })
    }
    setIsEditing(true)
  }

  const handleCancel = () => {
    // Reset form to last saved values from ref
    const saved = savedProfileRef.current
    if (saved) {
      setForm({
        full_name: saved.full_name || '',
        phone: saved.phone || '',
        university: saved.university || '',
        degree: saved.degree || '',
        gpa: saved.gpa ?? '',
        skills: (saved.skills || []).join(', ')
      })
    }
    setIsEditing(false)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const skillsArray = form.skills.split(',').map(s => s.trim()).filter(Boolean)
      const res = await API.put('/students/profile', {
        full_name: form.full_name,
        phone: form.phone,
        university: form.university,
        degree: form.degree,
        gpa: form.gpa ? parseFloat(form.gpa) : null,
        skills: skillsArray
      })
      // Update both profile state and the ref
      setProfile(res.data)
      savedProfileRef.current = res.data
      toast.success('Profile updated successfully')
      setIsEditing(false)
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to update profile')
    } finally {
      setSaving(false)
    }
  }

  const handleCvSuccess = (updatedProfile) => {
    // Update profile display and ref
    setProfile(updatedProfile)
    savedProfileRef.current = updatedProfile
    // Only update form if NOT currently editing
    // — this was the original bug source
    if (!isEditing) {
      setForm({
        full_name: updatedProfile.full_name || '',
        phone: updatedProfile.phone || '',
        university: updatedProfile.university || '',
        degree: updatedProfile.degree || '',
        gpa: updatedProfile.gpa ?? '',
        skills: (updatedProfile.skills || []).join(', ')
      })
    }
    toast.success('CV processed — profile updated')
  }

  const statusColor = (status) => {
    if (status === 'accepted') return 'bg-[#e6f7f7] text-[#1AA29F]'
    if (status === 'rejected') return 'bg-red-50 text-red-500'
    return 'bg-amber-50 text-amber-600'
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="animate-spin text-[#1AA29F]" size={32} />
      </div>
    )
  }

  return (
    <div className="p-6 max-w-5xl mx-auto w-full">
      <h1 className="text-2xl font-bold text-gray-800 mb-1">Student Dashboard</h1>
      <p className="text-gray-400 text-sm mb-6">Manage your profile and track your applications</p>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Profile card */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold text-gray-800 flex items-center gap-2">
              <User size={18} className="text-[#1AA29F]" /> Profile
            </h2>
            {!isEditing ? (
              <button
                onClick={handleEditClick}
                className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-[#e6f7f7] text-[#1AA29F] hover:bg-[#d0efef] transition-colors"
              >
                <Pencil size={13} /> Edit Profile
              </button>
            ) : (
              <button
                onClick={handleCancel}
                className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 transition-colors"
              >
                <X size={13} /> Cancel
              </button>
            )}
          </div>

          {!isEditing ? (
            <div className="space-y-3">
              <ProfileField icon={<User size={14} />} label="Full Name" value={profile?.full_name} />
              <ProfileField icon={<Phone size={14} />} label="Phone" value={profile?.phone} />
              <ProfileField icon={<GraduationCap size={14} />} label="University" value={profile?.university} />
              <div className="grid grid-cols-2 gap-3">
                <ProfileField label="Degree" value={profile?.degree} />
                <ProfileField icon={<BarChart3 size={14} />} label="GPA" value={profile?.gpa} />
              </div>
              <div>
                <p className="text-xs text-gray-400 mb-1.5 flex items-center gap-1.5">
                  <Award size={13} /> Skills
                </p>
                {profile?.skills?.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {profile.skills.map((skill, i) => (
                      <span
                        key={i}
                        className="bg-[#e6f7f7] text-[#1AA29F] text-xs font-medium px-2.5 py-1 rounded-full"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-400 italic">No skills added yet</p>
                )}
              </div>
            </div>
          ) : (
            <form onSubmit={handleSave} className="space-y-3">
              <div className="relative border rounded-xl px-3 pt-4 pb-2 focus-within:border-[#1AA29F]">
                <label className="absolute top-1 left-3 text-xs text-[#1AA29F] font-medium">Full Name</label>
                <input
                  type="text"
                  className="w-full outline-none text-sm text-gray-700 bg-transparent"
                  value={form.full_name}
                  onChange={(e) => setForm(prev => ({ ...prev, full_name: e.target.value }))}
                />
              </div>

              <div className="relative border rounded-xl px-3 pt-4 pb-2 focus-within:border-[#1AA29F]">
                <label className="absolute top-1 left-3 text-xs text-[#1AA29F] font-medium">Phone</label>
                <div className="flex items-center gap-2">
                  <Phone size={14} className="text-gray-400" />
                  <input
                    type="text"
                    className="flex-1 outline-none text-sm text-gray-700 bg-transparent"
                    value={form.phone}
                    onChange={(e) => setForm(prev => ({ ...prev, phone: e.target.value }))}
                  />
                </div>
              </div>

              <div className="relative border rounded-xl px-3 pt-4 pb-2 focus-within:border-[#1AA29F]">
                <label className="absolute top-1 left-3 text-xs text-[#1AA29F] font-medium">University</label>
                <div className="flex items-center gap-2">
                  <GraduationCap size={14} className="text-gray-400" />
                  <input
                    type="text"
                    className="flex-1 outline-none text-sm text-gray-700 bg-transparent"
                    value={form.university}
                    onChange={(e) => setForm(prev => ({ ...prev, university: e.target.value }))}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="relative border rounded-xl px-3 pt-4 pb-2 focus-within:border-[#1AA29F]">
                  <label className="absolute top-1 left-3 text-xs text-[#1AA29F] font-medium">Degree</label>
                  <input
                    type="text"
                    className="w-full outline-none text-sm text-gray-700 bg-transparent"
                    value={form.degree}
                    onChange={(e) => setForm(prev => ({ ...prev, degree: e.target.value }))}
                  />
                </div>
                <div className="relative border rounded-xl px-3 pt-4 pb-2 focus-within:border-[#1AA29F]">
                  <label className="absolute top-1 left-3 text-xs text-[#1AA29F] font-medium">GPA</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="4"
                    className="w-full outline-none text-sm text-gray-700 bg-transparent"
                    value={form.gpa}
                    onChange={(e) => setForm(prev => ({ ...prev, gpa: e.target.value }))}
                  />
                </div>
              </div>

              <div className="relative border rounded-xl px-3 pt-4 pb-2 focus-within:border-[#1AA29F]">
                <label className="absolute top-1 left-3 text-xs text-[#1AA29F] font-medium">Skills (comma separated)</label>
                <div className="flex items-start gap-2">
                  <Award size={14} className="text-gray-400 mt-1" />
                  <textarea
                    rows={2}
                    className="flex-1 outline-none text-sm text-gray-700 bg-transparent resize-none"
                    placeholder="Python, React, SQL..."
                    value={form.skills}
                    onChange={(e) => setForm(prev => ({ ...prev, skills: e.target.value }))}
                  />
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 flex items-center justify-center gap-2 bg-[#1AA29F] hover:bg-[#158a87] text-white py-2.5 rounded-xl font-semibold text-sm disabled:opacity-50 transition-colors"
                >
                  {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          )}
        </div>

        {/* CV Upload */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h2 className="font-bold text-gray-800 mb-4">Upload your CV</h2>
          <p className="text-sm text-gray-400 mb-4">
            Uploading auto-fills your profile and generates the SBERT embedding used for matching.
          </p>
          <CVUpload onSuccess={handleCvSuccess} />
        </div>
      </div>

      {/* Certificates — compact, full-width; mainly viewed by employers reviewing applicants */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mt-6">
        <div className="flex items-center justify-between mb-1">
          <h2 className="font-bold text-gray-800">Certificates</h2>
        </div>
        <p className="text-sm text-gray-400 mb-4">
          Employers can view these when reviewing your applications.
        </p>
        <CertificateManager />
      </div>

      {/* Applications */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mt-6">
        <h2 className="font-bold text-gray-800 mb-4">My Applications</h2>

        {applications.length === 0 ? (
          <p className="text-sm text-gray-400">
            You haven't applied to any internships yet. Check your{' '}
            <a href="/student/recommendations" className="text-[#1AA29F] hover:underline">matches</a>{' '}
            to get started.
          </p>
        ) : (
          <div className="space-y-2">
            {applications.map((app) => (
  <div key={app.id} className="border border-gray-100 rounded-xl px-4 py-3">
    <div className="flex items-center justify-between">
      <div>
        <p className="font-medium text-gray-800 text-sm">{app.internship?.title}</p>
        <p className="text-xs text-gray-400">
          Applied {new Date(app.applied_at).toLocaleDateString()}
        </p>
      </div>
      <div className="flex items-center gap-3">
        {app.match_score != null && (
          <span className="text-xs text-gray-500">
            {Math.round(app.match_score * 100)}% match
          </span>
        )}
        <span className={`text-xs font-semibold px-2.5 py-1 rounded-full capitalize ${statusColor(app.status)}`}>
          {app.status}
        </span>
      </div>
    </div>

    {(app.interview_date || app.start_date) && (
      <div className="mt-3 pt-3 border-t border-gray-100 space-y-1.5">
        {app.interview_date && (
          <p className="text-xs text-[#1AA29F] font-medium">
            <Calendar size={13}/> Interview: {new Date(app.interview_date).toLocaleString()}
          </p>
        )}
        {app.start_date && (
          <p className="text-xs text-[#1AA29F] font-medium">
            <PartyPopper size={13} /> Proposed start date: {new Date(app.start_date).toLocaleDateString()}
          </p>
        )}
      </div>
    )}
  </div>
))}
          </div>
        )}
      </div>
    </div>
  )
}

function ProfileField({ icon, label, value }) {
  return (
    <div>
      <p className="text-xs text-gray-400 mb-0.5 flex items-center gap-1.5">
        {icon} {label}
      </p>
      <p className="text-sm text-gray-700">
        {value || <span className="text-gray-300 italic">Not set</span>}
      </p>
    </div>
  )
}