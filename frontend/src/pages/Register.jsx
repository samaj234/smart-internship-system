import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import API from '../api/axios'
import { Mail, Lock, User, Building2 } from 'lucide-react'
import studentImg from '../assets/student.png'
import employerImg from '../assets/employer.png'

export default function Register() {
  const [role, setRole] = useState('student')
  const [form, setForm] = useState({
    email: '', password: '', full_name: '', company_name: ''
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()
  const toast = useToast()

  const handleSubmit = async (e) => {
  e.preventDefault()
  setLoading(true)
  try {
    await API.post('/auth/register', { ...form, role })
    const res = await API.post('/auth/login', { email: form.email, password: form.password })
    login(res.data.user, res.data.access_token)
    toast.success('Account created successfully!')
    navigate(res.data.user.role === 'student' ? '/student/dashboard' : '/employer/dashboard')
  } catch (err) {
    const data = err.response?.data
    if (data?.details) {
      // marshmallow validation errors — show the first specific field error
      const firstField = Object.keys(data.details)[0]
      toast.error(data.details[firstField][0])
    } else {
      toast.error(data?.error || 'Registration failed')
    }
  } finally {
    setLoading(false)
  }
}


  return (
    <div className="flex-1 flex items-center justify-center bg-[#e6f7f7]  py-10 px-4">

      {/* City skyline */}
      <div className="absolute bottom-0 left-0 right-0 h-32 opacity-10">
        <svg viewBox="0 0 800 120" className="w-full h-full" fill="#1AA29F">
          <rect x="0" y="60" width="40" height="60" />
          <rect x="10" y="40" width="20" height="80" />
          <rect x="50" y="70" width="30" height="50" />
          <rect x="90" y="30" width="25" height="90" />
          <rect x="120" y="55" width="45" height="65" />
          <rect x="175" y="65" width="35" height="55" />
          <rect x="220" y="45" width="20" height="75" />
          <rect x="250" y="25" width="30" height="95" />
          <rect x="290" y="60" width="50" height="60" />
          <rect x="350" y="50" width="25" height="70" />
          <rect x="385" y="35" width="40" height="85" />
          <rect x="480" y="40" width="25" height="80" />
          <rect x="515" y="60" width="45" height="60" />
          <rect x="570" y="50" width="30" height="70" />
          <rect x="640" y="55" width="40" height="65" />
          <rect x="730" y="60" width="35" height="60" />
        </svg>
      </div>

      <div className="bg-white rounded-3xl shadow-xl w-full max-w-sm p-8 relative z-10">

        <h2 className="text-2xl font-bold text-[#1AA29F] text-center mb-6">
          Create Account
        </h2>

        {/* Role Cards */}
        <div className="flex gap-4 justify-center mb-4">
          <div
            onClick={() => setRole('student')}
            className={`relative cursor-pointer border-2 rounded-2xl p-4 flex flex-col items-center w-32 transition-all duration-200
              ${role === 'student'
                ? 'border-[#1AA29F] bg-[#e6f7f7] shadow-md'
                : 'border-gray-200 bg-white hover:border-[#1AA29F]'
              }`}
          >
            <img src={studentImg} alt="Student" className="h-16 w-16 object-contain mb-2" />
            <span className="text-sm font-medium text-gray-600">Student</span>
            {role === 'student' && (
              <div className="absolute -bottom-3 left-1/2 -translate-x-1/2 bg-[#1AA29F] rounded-full w-6 h-6 flex items-center justify-center shadow">
                <span className="text-white text-xs">✓</span>
              </div>
            )}
          </div>

          <div
            onClick={() => setRole('employer')}
            className={`relative cursor-pointer border-2 rounded-2xl p-4 flex flex-col items-center w-32 transition-all duration-200
              ${role === 'employer'
                ? 'border-[#1AA29F] bg-[#e6f7f7] shadow-md'
                : 'border-gray-200 bg-white hover:border-[#1AA29F]'
              }`}
          >
            <img src={employerImg} alt="Employer" className="h-16 w-16 object-contain mb-2" />
            <span className="text-sm font-medium text-gray-600">Employer</span>
            {role === 'employer' && (
              <div className="absolute -bottom-3 left-1/2 -translate-x-1/2 bg-[#1AA29F] rounded-full w-6 h-6 flex items-center justify-center shadow">
                <span className="text-white text-xs">✓</span>
              </div>
            )}
          </div>
        </div>

        <p className="text-center text-gray-400 text-sm mt-6 mb-5">
          Joining as a {role}!<br />
          Fill out the form below to get started.
        </p>

        {error && (
          <div className="bg-red-50 text-red-600 px-4 py-2 rounded-lg mb-4 text-sm text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">

          {role === 'student' && (
            <div className="relative border rounded-xl px-3 pt-4 pb-2 focus-within:border-[#1AA29F] transition-colors">
              <label className="absolute top-1 left-3 text-xs text-[#1AA29F] font-medium">
                Full Name
              </label>
              <div className="flex items-center gap-2">
                <User size={16} className="text-gray-400" />
                <input
                  type="text"
                  placeholder="John Doe"
                  className="flex-1 outline-none text-sm text-gray-700 bg-transparent"
                  value={form.full_name}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                />
              </div>
            </div>
          )}

          {role === 'employer' && (
            <div className="relative border rounded-xl px-3 pt-4 pb-2 focus-within:border-[#1AA29F] transition-colors">
              <label className="absolute top-1 left-3 text-xs text-[#1AA29F] font-medium">
                Company Name
              </label>
              <div className="flex items-center gap-2">
                <Building2 size={16} className="text-gray-600" />
                <input
                  type="text"
                  placeholder="Company Ltd"
                  className="flex-1 outline-none text-sm text-gray-700 bg-transparent"
                  value={form.company_name}
                  onChange={(e) => setForm({ ...form, company_name: e.target.value })}
                />
              </div>
            </div>
          )}

          <div className="relative border rounded-xl px-3 pt-4 pb-2 focus-within:border-[#1AA29F] transition-colors">
            <label className="absolute top-1 left-3 text-xs text-[#1AA29F] font-medium">
              Email
            </label>
            <div className="flex items-center gap-2">
              <Mail size={16} className="text-gray-400" />
              <input
                type="email"
                placeholder="your@email.com"
                className="flex-1 outline-none text-sm text-gray-700 bg-transparent"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                required
              />
            </div>
          </div>

          <div className="relative border rounded-xl px-3 pt-4 pb-2 focus-within:border-[#1AA29F] transition-colors">
            <label className="absolute top-1 left-3 text-xs text-[#1AA29F] font-medium">
              Password
            </label>
            <div className="flex items-center gap-2">
              <Lock size={16} className="text-gray-600" />
              <input
                type="password"
                placeholder="••••••••"
                className="flex-1 outline-none text-sm text-gray-700 bg-transparent"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                required
              />
            </div>
          </div>

          <div className="flex justify-between items-center pt-1">
            <p className="text-sm text-gray-400">
              Have an account?{' '}
              <Link to="/login" className="text-[#1AA29F] font-semibold hover:underline">
                Login
              </Link>
            </p>
            <button
              type="submit"
              disabled={loading}
              className="bg-[#1AA29F] hover:bg-[#158a87] text-white px-7 py-2 rounded-xl font-semibold text-sm disabled:opacity-50 transition-colors shadow"
            >
              {loading ? '...' : 'Register'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}