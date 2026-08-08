import { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [authState, setAuthState] = useState({
    user: null,
    token: null,
    loading: true
  })

  useEffect(() => {
    try {
      const savedToken = localStorage.getItem('token')
      const savedUser = localStorage.getItem('user')
      if (savedToken && savedUser) {
        // Single setState call — one re-render instead of two
        setAuthState({
          user: JSON.parse(savedUser),
          token: savedToken,
          loading: false
        })
      } else {
        setAuthState(prev => ({ ...prev, loading: false }))
      }
    } catch (err) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      setAuthState({ user: null, token: null, loading: false })
    }
  }, [])

  const login = (userData, accessToken) => {
    setAuthState({ user: userData, token: accessToken, loading: false })
    localStorage.setItem('token', accessToken)
    localStorage.setItem('user', JSON.stringify(userData))
  }

  const logout = () => {
    setAuthState({ user: null, token: null, loading: false })
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return (
    <AuthContext.Provider value={{
      user: authState.user,
      token: authState.token,
      loading: authState.loading,
      login,
      logout
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}