import { useState, useEffect } from 'react'
import { NavLink, Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { LogOut, LayoutDashboard, Briefcase, Star, Menu, X } from 'lucide-react'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10)
    }
    window.addEventListener('scroll', handleScroll)
    handleScroll()
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const handleLogout = () => {
    logout()
    setMenuOpen(false)
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
          <span className="text-xl font-bold text-[#1AA29F]">Smart Internship</span>
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
              <span className="text-sm text-gray-400 max-w-[140px] truncate">{user.email}</span>
              <button
                onClick={handleLogout}
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
              <div className="border-t border-[#1AA29F]/15 my-1" />
              <span className="text-sm text-gray-400 px-3 py-1 truncate">{user.email}</span>
              <button
                onClick={handleLogout}
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
    </nav>
  )
}