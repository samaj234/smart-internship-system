import { useState } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { Lock, ShieldCheck } from 'lucide-react'
import API from '../api/axios'

export default function ResetPassword() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match')
      return
    }
    setLoading(true)
    setError('')
    try {
      await API.post('/auth/reset-password', {
        reset_token: token,
        new_password: newPassword
      })
      setSuccess(true)
      setTimeout(() => navigate('/login'), 3000)
    } catch (err) {
      setError(err.response?.data?.error || 'Reset failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex-1 flex items-center justify-center bg-[#e6f7f7] relative overflow-hidden py-10 px-4">
      <div className="absolute bottom-0 left-0 right-0 h-32 opacity-10">
        <svg viewBox="0 0 800 120" className="w-full h-full" fill="#1AA29F">
          <rect x="0" y="60" width="40" height="60" />
          <rect x="90" y="30" width="25" height="90" />
          <rect x="175" y="65" width="35" height="55" />
          <rect x="290" y="60" width="50" height="60" />
          <rect x="385" y="35" width="40" height="85" />
          <rect x="515" y="60" width="45" height="60" />
          <rect x="640" y="55" width="40" height="65" />
          <rect x="730" y="60" width="35" height="60" />
        </svg>
      </div>

      <div className="bg-white rounded-3xl shadow-xl w-full max-w-sm p-8 relative z-10">
        {!success ? (
          <>
            <div className="text-center mb-6">
              <div className="flex justify-center mb-3">
                <div className="bg-[#e6f7f7] p-4 rounded-full">
                  <Lock size={32} className="text-[#1AA29F]" />
                </div>
              </div>
              <h2 className="text-2xl font-bold text-[#1AA29F]">Reset Password</h2>
              <p className="text-gray-400 text-sm mt-2">Enter your new password below.</p>
            </div>

            {!token && (
              <div className="bg-red-50 text-red-600 px-4 py-2 rounded-lg mb-4 text-sm text-center">
                Invalid reset link. Please request a new one.
              </div>
            )}

            {error && (
              <div className="bg-red-50 text-red-600 px-4 py-2 rounded-lg mb-4 text-sm text-center">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="relative border rounded-xl px-3 pt-4 pb-2 focus-within:border-[#1AA29F] transition-colors">
                <label className="absolute top-1 left-3 text-xs text-[#1AA29F] font-medium">
                  New Password
                </label>
                <div className="flex items-center gap-2">
                  <Lock size={16} className="text-gray-400" />
                  <input
                    type="password"
                    placeholder="••••••••"
                    className="flex-1 outline-none text-sm text-gray-700 bg-transparent"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="relative border rounded-xl px-3 pt-4 pb-2 focus-within:border-[#1AA29F] transition-colors">
                <label className="absolute top-1 left-3 text-xs text-[#1AA29F] font-medium">
                  Confirm Password
                </label>
                <div className="flex items-center gap-2">
                  <Lock size={16} className="text-gray-400" />
                  <input
                    type="password"
                    placeholder="••••••••"
                    className="flex-1 outline-none text-sm text-gray-700 bg-transparent"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading || !token}
                className="w-full bg-[#1AA29F] hover:bg-[#158a87] text-white py-2.5 rounded-xl font-semibold text-sm disabled:opacity-50 transition-colors shadow"
              >
                {loading ? 'Resetting...' : 'Reset Password'}
              </button>
            </form>

            <p className="text-center text-sm text-gray-400 mt-4">
              Remember your password?{' '}
              <Link to="/login" className="text-[#1AA29F] font-semibold hover:underline">
                Login
              </Link>
            </p>
          </>
        ) : (
          <div className="text-center py-6">
            <div className="flex justify-center mb-4">
              <div className="bg-[#e6f7f7] p-4 rounded-full">
                <ShieldCheck size={36} className="text-[#1AA29F]" />
              </div>
            </div>
            <h2 className="text-2xl font-bold text-[#1AA29F]">Password Reset!</h2>
            <p className="text-gray-400 text-sm mt-2 mb-6">
              Your password has been reset successfully.<br />
              Redirecting to login...
            </p>
            <Link
              to="/login"
              className="bg-[#1AA29F] hover:bg-[#158a87] text-white px-8 py-2.5 rounded-xl font-semibold text-sm transition-colors shadow"
            >
              Go to Login
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}