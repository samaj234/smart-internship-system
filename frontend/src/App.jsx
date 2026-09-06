import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { Loader2 } from 'lucide-react'
import { useAuth } from './context/AuthContext'
import Login from './pages/Login'
import Register from './pages/Register'
import StudentDashboard from './pages/StudentDashboard'
import EmployerDashboard from './pages/EmployerDashboard'
import Internships from './pages/Internships'
import Recommendations from './pages/Recommendations'
import Navbar from './components/Navbar'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
import ChatBot from './components/ChatBot'
import Landing from './pages/Landing'
import Notifications from './pages/Notifications'


function ProtectedRoute({ children, role }) {
  const { user, loading } = useAuth()

  // Wait for auth state to load from localStorage
  // before deciding whether to redirect or render
  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="animate-spin text-[#1AA29F]" size={32} />
      </div>
    )
  }

  if (!user) return <Navigate to="/login" />
  if (role && user.role !== role) return <Navigate to="/login" />
  return children
}

function PageWrapper({ children }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.15, ease: 'easeInOut' }}
      className="flex-1 flex flex-col"
    >
      {children}
    </motion.div>
  )
}

function AnimatedRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} /> 
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route path="/student/dashboard" element={
        <ProtectedRoute role="student">
          <StudentDashboard />
        </ProtectedRoute>
      } />

      <Route path="/student/recommendations" element={
        <ProtectedRoute role="student">
          <Recommendations />
        </ProtectedRoute>
      } />

      <Route path="/employer/dashboard" element={
        <ProtectedRoute role="employer">
          <EmployerDashboard />
        </ProtectedRoute>
      } />

      <Route path="/notifications" element={
        <ProtectedRoute>
          <Notifications />
        </ProtectedRoute>
      } />

      <Route path="/internships" element={<Internships />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
    </Routes>
  )
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col bg-gradient-to-b from-[#e6f7f7] to-white">
        <Navbar />
        <main className="flex-1 flex flex-col pt-16">
          <AnimatedRoutes />
        </main>
        <ChatBot />
      </div>
    </BrowserRouter>
  )
}

export default App