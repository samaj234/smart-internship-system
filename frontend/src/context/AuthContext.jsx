import { createContext, useContext, useState } from "react"

export const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const storedUser = localStorage.getItem("user")
    return storedUser ? JSON.parse(storedUser) : null
  })

  const [token, setToken] = useState(() => {
    return localStorage.getItem("token") || null
  })

  const login = (userData, accessToken) => {
    setUser(userData)
    setToken(accessToken)
    localStorage.setItem("token", accessToken)
    localStorage.setItem("user", JSON.stringify(userData))
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem("token")
    localStorage.removeItem("user")
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}