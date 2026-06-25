import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
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

function ProtectedRoute({ children, role }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" />
  if (role && user.role !== role) return <Navigate to="/login" />
  return children
}

function PageWrapper({ children }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.2, ease: 'easeInOut' }}
      className=" flex-1 flex flex-col"
    >
      {children}
    </motion.div>
  )
}

function AnimatedRoutes() {
  const location = useLocation()

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<Navigate to="/login" />} />
        <Route path="/login" element={<PageWrapper><Login /></PageWrapper>} />
        <Route path="/register" element={<PageWrapper><Register /></PageWrapper>} />

        <Route path="/student/dashboard" element={
          <ProtectedRoute role="student">
            <PageWrapper><StudentDashboard /></PageWrapper>
          </ProtectedRoute>
        } />

        <Route path="/student/recommendations" element={
          <ProtectedRoute role="student">
            <PageWrapper><Recommendations /></PageWrapper>
          </ProtectedRoute>
        } />

        <Route path="/employer/dashboard" element={
          <ProtectedRoute role="employer">
            <PageWrapper><EmployerDashboard /></PageWrapper>
          </ProtectedRoute>
        } />

        <Route path="/internships" element={<PageWrapper><Internships /></PageWrapper>} />

        <Route path="/forgot-password" element={<PageWrapper><ForgotPassword /></PageWrapper>} />
        <Route path="/reset-password" element={<PageWrapper><ResetPassword /></PageWrapper>} />
      </Routes>
    </AnimatePresence>
  )
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col  bg-[#748d92]">
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