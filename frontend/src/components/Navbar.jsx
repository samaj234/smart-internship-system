import { useState, useEffect } from 'react'
import { NavLink, Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { LogOut, LayoutDashboard, Briefcase, Star, Menu, X, Bell } from 'lucide-react'
import API from '../api/axios'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10)
    }
    window.addEventListener('scroll', handleScroll)
    handleScroll()
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  useEffect(() => {
    // No setState here — the bell/badge only renders inside the
    // logged-in branch of the JSX below, so a stale unreadCount value
    // is simply never shown once user is null. Calling setState
    // synchronously in the effect body for this was unnecessary and
    // is what React's cascading-render warning was flagging.
    if (!user) return

    let isMounted = true
    const fetchUnreadCount = async () => {
      try {
        const res = await API.get('/notifications/unread-count')
        if (isMounted) setUnreadCount(res.data.unread_count || 0)
      } catch (err) {
        // Silent — a failed unread count shouldn't disrupt the rest of the nav.
      }
    }

    fetchUnreadCount()
    // Poll periodically so the badge updates even without any action —
    // but also listen for an explicit signal so reading/deleting a
    // notification on the /notifications page updates the badge
    // instantly instead of waiting up to 30s for the next poll.
    const interval = setInterval(fetchUnreadCount, 1000)
    window.addEventListener('notifications:changed', fetchUnreadCount)
    return () => {
      isMounted = false
      clearInterval(interval)
      window.removeEventListener('notifications:changed', fetchUnreadCount)
    }
  }, [user])

  const handleLogout = () => {
    logout()
    setMenuOpen(false)
    setShowLogoutConfirm(false)
    navigate('/login')
  }

  const handleNavClick = () => {
    setMenuOpen(false)
  }

  const linkClass = ({ isActive }) =>
    `flex items-center gap-1.5 text-sm font-medium px-3 py-1.5 rounded-lg transition-colors ${
      isActive
        ? 'bg-[#1AA29F] text-white'
        : 'text-[#1AA29F] hover:bg-[#1AA29F]/10'
    }`

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 px-2 sm:px-4 py-1.5 transition-all duration-300 ${
        scrolled
          ? 'bg-[#e6f7f7]/60 backdrop-blur-md shadow-sm'
          : 'bg-transparent'
      }`}
    >
      <div className="flex justify-between items-center h-10">
        <Link to="/" className="flex items-center gap-2" onClick={handleNavClick}>
          <span className="text-xl font-bold text-[#1AA29F]">InternLink</span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex gap-3 items-center">
          <NavLink to="/internships" className={linkClass}>
            <Briefcase size={16} />
            <span>Internships</span>
          </NavLink>

          {user ? (
            <>
              {user.role === 'student' && (
                <>
                  <NavLink to="/student/dashboard" className={linkClass}>
                    <LayoutDashboard size={16} />
                    <span>Dashboard</span>
                  </NavLink>
                  <NavLink to="/student/recommendations" className={linkClass}>
                    <Star size={16} />
                    <span>Matches</span>
                  </NavLink>
                </>
              )}
              {user.role === 'employer' && (
                <NavLink to="/employer/dashboard" className={linkClass}>
                  <LayoutDashboard size={16} />
                  <span>Dashboard</span>
                </NavLink>
              )}

              <NavLink to="/notifications" className={linkClass} aria-label="Notifications">
                <span className="relative">
                  <Bell size={16} />
                  {unreadCount > 0 && (
                    <span className="absolute -top-1.5 -right-1.5 bg-red-500 text-white text-[10px] font-bold rounded-full min-w-[15px] h-[15px] flex items-center justify-center px-0.5">
                      {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                  )}
                </span>
              </NavLink>

              <span className="text-sm text-gray-400 max-w-[140px] truncate">{user.email}</span>
              <button
                onClick={() => setShowLogoutConfirm(true)}
                className="flex items-center gap-1 border border-[#1AA29F] text-[#1AA29F] px-3 py-1 rounded-lg hover:bg-[#1AA29F] hover:text-white text-sm font-medium transition-colors"
              >
                <LogOut size={16} />
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="text-[#1AA29F] hover:opacity-70 text-sm font-medium">
                Login
              </Link>
              <Link
                to="/register"
                className="bg-[#1AA29F] text-white px-4 py-1.5 rounded-lg hover:bg-[#158a87] text-sm font-medium transition-colors"
              >
                Register
              </Link>
            </>
          )}
        </div>

        {/* Mobile hamburger toggle */}
        <button
          onClick={() => setMenuOpen(prev => !prev)}
          className="md:hidden text-[#1AA29F] p-1"
          aria-label="Toggle menu"
        >
          {menuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Mobile dropdown panel */}
      {menuOpen && (
        <div className="md:hidden absolute top-full left-0 right-0 bg-[#e6f7f7]/90 backdrop-blur-md border-t border-[#1AA29F]/15 shadow-lg flex flex-col gap-1 p-4">
          <NavLink to="/internships" className={linkClass} onClick={handleNavClick}>
            <Briefcase size={16} />
            <span>Internships</span>
          </NavLink>

          {user ? (
            <>
              {user.role === 'student' && (
                <>
                  <NavLink to="/student/dashboard" className={linkClass} onClick={handleNavClick}>
                    <LayoutDashboard size={16} />
                    <span>Dashboard</span>
                  </NavLink>
                  <NavLink to="/student/recommendations" className={linkClass} onClick={handleNavClick}>
                    <Star size={16} />
                    <span>Matches</span>
                  </NavLink>
                </>
              )}
              {user.role === 'employer' && (
                <NavLink to="/employer/dashboard" className={linkClass} onClick={handleNavClick}>
                  <LayoutDashboard size={16} />
                  <span>Dashboard</span>
                </NavLink>
              )}

              <NavLink to="/notifications" className={linkClass} onClick={handleNavClick}>
                <span className="relative">
                  <Bell size={16} />
                  {unreadCount > 0 && (
                    <span className="absolute -top-1.5 -right-1.5 bg-red-500 text-white text-[10px] font-bold rounded-full min-w-[15px] h-[15px] flex items-center justify-center px-0.5">
                      {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                  )}
                </span>
                <span>Notifications</span>
              </NavLink>

              <div className="border-t border-[#1AA29F]/15 my-1" />
              <span className="text-sm text-gray-400 px-3 py-1 truncate">{user.email}</span>
              <button
                onClick={() => setShowLogoutConfirm(true)}
                className="flex items-center gap-1.5 border border-[#1AA29F] text-[#1AA29F] px-3 py-2 rounded-lg hover:bg-[#1AA29F] hover:text-white text-sm font-medium transition-colors"
              >
                <LogOut size={16} />
                Logout
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                onClick={handleNavClick}
                className="text-[#1AA29F] text-sm font-medium px-3 py-2 rounded-lg hover:bg-[#1AA29F]/10"
              >
                Login
              </Link>
              <Link
                to="/register"
                onClick={handleNavClick}
                className="bg-[#1AA29F] text-white px-3 py-2 rounded-lg hover:bg-[#158a87] text-sm font-medium text-center transition-colors"
              >
                Register
              </Link>
            </>
          )}
        </div>
      )}

      {/* Logout confirmation modal */}
      {showLogoutConfirm && (
        <div
          className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40 px-4"
          onClick={() => setShowLogoutConfirm(false)}
        >
          <div
            className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-bold text-gray-800 mb-1">Log out?</h3>
            <p className="text-sm text-gray-500 mb-6">
              You'll need to log in again to access your account.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowLogoutConfirm(false)}
                className="flex-1 px-4 py-2 rounded-xl text-sm font-medium text-gray-600 border border-gray-200 hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleLogout}
                className="flex-1 px-4 py-2 rounded-xl text-sm font-semibold bg-[#1AA29F] text-white hover:bg-[#158a87] transition-colors"
              >
                Log out
              </button>
            </div>
          </div>
        </div>
      )}
    </nav>
  )
}