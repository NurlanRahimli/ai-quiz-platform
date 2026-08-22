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
    setIsLoading(true)

    try {
      localStorage.setItem(TOKEN_STORAGE_KEY, accessToken)
      setToken(accessToken)

      const currentUser = await fetchCurrentUser(accessToken)
      setUser(currentUser)
    } catch (error) {
      localStorage.removeItem(TOKEN_STORAGE_KEY)
      setToken(null)
      setUser(null)
      throw error
    } finally {
      setIsLoading(false)
    }
  }


  const refreshUser = async () => {
    const accessToken =
      token ?? localStorage.getItem(TOKEN_STORAGE_KEY)

    if (!accessToken) {
      return
    }

    const currentUser = await fetchCurrentUser(accessToken)
    setUser(currentUser)
  }


  const logout = () => {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    setToken(null)
    setUser(null)
    setIsLoading(false)
  }

  useEffect(() => {
    const restoreSession = async () => {
      const storedToken = localStorage.getItem(TOKEN_STORAGE_KEY)

      if (!storedToken) {
        setToken(null)
        setUser(null)
        setIsLoading(false)
        return
      }

      setIsLoading(true)

      try {
        const currentUser = await fetchCurrentUser(storedToken)
        setToken(storedToken)
        setUser(currentUser)
      } catch {
        localStorage.removeItem(TOKEN_STORAGE_KEY)
        setToken(null)
        setUser(null)
      } finally {
        setIsLoading(false)
      }
    }

    void restoreSession()
  }, [fetchCurrentUser])

  const value: AuthContextValue = {
    user,
    token,
    isAuthenticated: user !== null,
    isLoading,
    login,
    logout,
    refreshUser,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
