import {
  useCallback,
  useEffect,
  useState,
} from "react"
import type { ReactNode } from "react"

import apiClient from "../api/client"
import {
  AuthContext,
  type AuthContextValue,
  type User,
} from "./auth-context"


const TOKEN_STORAGE_KEY = "ai_quiz_access_token"


type AuthProviderProps = {
  children: ReactNode
}


export function AuthProvider({ children }: AuthProviderProps) {
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem(TOKEN_STORAGE_KEY),
  )

  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)


  const fetchCurrentUser = useCallback(async (accessToken: string) => {
    const response = await apiClient.get<User>("/auth/me", {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    })

    return response.data
  }, [])


  const login = async (accessToken: string) => {
    localStorage.setItem(TOKEN_STORAGE_KEY, accessToken)
    setToken(accessToken)

    try {
      const currentUser = await fetchCurrentUser(accessToken)
      setUser(currentUser)
    } catch (error) {
      localStorage.removeItem(TOKEN_STORAGE_KEY)
      setToken(null)
      setUser(null)

      throw error
    }
  }


  const logout = () => {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    setToken(null)
    setUser(null)
  }


  useEffect(() => {
    const restoreSession = async () => {
      if (!token) {
        setIsLoading(false)
        return
      }

      try {
        const currentUser = await fetchCurrentUser(token)
        setUser(currentUser)
      } catch {
        localStorage.removeItem(TOKEN_STORAGE_KEY)
        setToken(null)
        setUser(null)
      } finally {
        setIsLoading(false)
      }
    }

    restoreSession()
  }, [token, fetchCurrentUser])


  const value: AuthContextValue = {
    user,
    token,
    isAuthenticated: user !== null,
    isLoading,
    login,
    logout,
  }


  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}