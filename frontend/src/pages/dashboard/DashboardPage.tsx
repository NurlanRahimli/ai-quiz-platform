import { useNavigate } from "react-router-dom"

import { useAuth } from "../../auth/useAuth"

function DashboardPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate("/login", { replace: true })
  }

  return (
    <main>
      <h1>QuizAI</h1>
      <h2>Welcome, {user?.display_name}</h2>
      <p>You're successfully authenticated.</p>

      <button type="button" onClick={handleLogout}>
        Log Out
      </button>
    </main>
  )
}

export default DashboardPage