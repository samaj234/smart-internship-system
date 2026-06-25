import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import API from '../api/axios'
import { Mail, Lock, GraduationCap, Briefcase } from 'lucide-react'
import studentImg from '../assets/student.png'
import employerImg from '../assets/employer.png'

export default function Login() {
  const [role, setRole] = useState('student')
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()
  const toast = useToast()

  const handleSubmit = async (e) => {
  e.preventDefault()
  setLoading(true)
  try {
    const res = await API.post('/auth/login', { ...form, role })
    login(res.data.user, res.data.access_token)
    toast.success('Welcome back!')
    navigate(res.data.user.role === 'student' ? '/student/dashboard' : '/employer/dashboard')
  } catch (err) {
    toast.error(err.response?.data?.error || 'Login failed')
  } finally {
    setLoading(false)
  }
}

  return (
    <div className="flex-1 flex items-center justify-center bg-[#e6f7f7] py-12 px-4 ">
      <div className="bg-white rounded-2xl shadow-lg w-full max-w-md p-8">

        <h2 className="text-2xl font-bold text-[#1AA29F] text-center mb-6">
          Choose Account Type
        </h2>

        {/* Role selector cards */}
        <div className="flex gap-4 justify-center mb-6">

          {/* Student Card */}
          <div
            onClick={() => setRole('student')}
            className={`cursor-pointer border-2 rounded-xl p-4 flex flex-col items-center w-36 transition-all
              ${role === 'student'
                ? 'border-[#1AA29F] bg-[#e6f7f7] shadow-md'
                : 'border-gray-200 hover:border-[#1AA29F]'
              }`}
          >
            <img src={studentImg} alt="Student" className="h-16 w-16 object-contain mb-2" />
            <span className="text-sm font-medium text-gray-700">Student</span>
            {role === 'student' && (
              <span className="mt-2 bg-[#1AA29F] text-white rounded-full w-5 h-5 flex items-center justify-center text-xs">
                ✓
              </span>
            )}
          </div>

          {/* Employer Card */}
          <div
            onClick={() => setRole('employer')}
            className={`cursor-pointer border-2 rounded-xl p-4 flex flex-col items-center w-36 transition-all
              ${role === 'employer'
                ? 'border-[#1AA29F] bg-[#e6f7f7] shadow-md'
                : 'border-gray-200 hover:border-[#1AA29F]'
              }`}
          >
            <img src={employerImg} alt="Employer" className="h-16 w-16 object-contain mb-2" />
            <span className="text-sm font-medium text-gray-700">Employer</span>
            {role === 'employer' && (
              <span className="mt-2 bg-[#1AA29F] text-white rounded-full w-5 h-5 flex items-center justify-center text-xs">
                ✓
              </span>
            )}
          </div>
        </div>

        <p className="text-center text-gray-500 text-sm mb-6">
          Hello {role === 'student' ? 'student' : 'employer'}! <br />
          Please fill out the form below to get started.
        </p>

        {error && (
          <div className="bg-red-100 text-red-700 px-4 py-2 rounded-lg mb-4 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">

          {/* Email */}
          <div className="relative border rounded-xl px-3 pt-4 pb-2 focus-within:border-[#1AA29F] transition-colors">
            <label className="absolute top-1 left-3 text-xs text-[#1AA29F] font-medium">
              Email
            </label>
            <div className="flex items-center gap-2">
              <Mail size={16} className="text-gray-600" />
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

          {/* Password */}
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

          {/* Forgot password */}
          <div className="text-right">
            <Link to="/forgot-password" className="text-xs text-[#1AA29F] hover:underline">
              Forgot password?
            </Link>
          </div>

          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-500">
              No account?{' '}
              <Link to="/register" className="text-[#1AA29F] hover:underline font-medium">
                Signup
              </Link>
            </p>
            <button
              type="submit"
              disabled={loading}
              className="bg-[#1AA29F] text-white px-6 py-2 rounded-lg hover:bg-[#158a87] disabled:opacity-50 font-medium transition-colors"
            >
              {loading ? '...' : 'Login'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}