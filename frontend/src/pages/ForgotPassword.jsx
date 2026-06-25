import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Mail, KeyRound } from 'lucide-react'
import API from '../api/axios'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await API.post('/auth/forgot-password', { email })
      setSent(true)
    } catch (err) {
      setError(err.response?.data?.error || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex-1 flex items-center justify-center bg-[#e6f7f7] relative overflow-hidden py-10 px-4">
      <div className="absolute bottom-0 left-0 right-0 h-32 opacity-10">
        <svg viewBox="0 0 800 120" className="w-full h-full" fill="#1AA29F">
          <rect x="0" y="60" width="40" height="60" />
          <rect x="50" y="70" width="30" height="50" />
          <rect x="90" y="30" width="25" height="90" />
          <rect x="120" y="55" width="45" height="65" />
          <rect x="175" y="65" width="35" height="55" />
          <rect x="250" y="25" width="30" height="95" />
          <rect x="290" y="60" width="50" height="60" />
          <rect x="385" y="35" width="40" height="85" />
          <rect x="480" y="40" width="25" height="80" />
          <rect x="570" y="50" width="30" height="70" />
          <rect x="640" y="55" width="40" height="65" />
          <rect x="730" y="60" width="35" height="60" />
        </svg>
      </div>

      <div className="bg-white rounded-3xl shadow-xl w-full max-w-sm p-8 relative z-10">
        {!sent ? (
          <>
            <div className="text-center mb-6">
              <div className="flex justify-center mb-3">
                <div className="bg-[#e6f7f7] p-4 rounded-full">
                  <KeyRound size={32} className="text-[#1AA29F]" />
                </div>
              </div>
              <h2 className="text-2xl font-bold text-[#1AA29F]">Forgot Password</h2>
              <p className="text-gray-400 text-sm mt-2">
                Enter your email and we'll send you a reset link.
              </p>
            </div>

            {error && (
              <div className="bg-red-50 text-red-600 px-4 py-2 rounded-lg mb-4 text-sm text-center">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
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
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-[#1AA29F] hover:bg-[#158a87] text-white py-2.5 rounded-xl font-semibold text-sm disabled:opacity-50 transition-colors shadow"
              >
                {loading ? 'Sending...' : 'Send Reset Link'}
              </button>
            </form>
          </>
        ) : (
          <div className="text-center py-6">
            <div className="flex justify-center mb-4">
              <div className="bg-[#e6f7f7] p-4 rounded-full">
                <Mail size={36} className="text-[#1AA29F]" />
              </div>
            </div>
            <h2 className="text-2xl font-bold text-[#1AA29F]">Check Your Email</h2>
            <p className="text-gray-400 text-sm mt-2 mb-2">
              We sent a password reset link to:
            </p>
            <p className="text-[#1AA29F] font-semibold mb-6">{email}</p>
            <p className="text-gray-400 text-xs mb-6">
              Click the link in the email to reset your password.
              Check your spam folder if you don't see it.
            </p>
            <Link
              to="/login"
              className="bg-[#1AA29F] hover:bg-[#158a87] text-white px-8 py-2.5 rounded-xl font-semibold text-sm transition-colors shadow"
            >
              Back to Login
            </Link>
          </div>
        )}

        {!sent && (
          <p className="text-center text-sm text-gray-400 mt-4">
            Remember your password?{' '}
            <Link to="/login" className="text-[#1AA29F] font-semibold hover:underline">
              Login
            </Link>
          </p>
        )}
      </div>
    </div>
  )
}