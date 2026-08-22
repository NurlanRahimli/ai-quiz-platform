import { createContext } from "react"

export type User = {
  id: string
  email: string
  display_name: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export type AuthContextValue = {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (token: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | undefined>(
  undefined,
)