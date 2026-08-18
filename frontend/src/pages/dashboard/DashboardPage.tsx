import { useEffect, useState } from "react"
import axios from "axios"
import { useNavigate } from "react-router-dom"
import apiClient from "../../api/client"
import { useAuth } from "../../auth/useAuth"
import "./DashboardPage.css"

type Quiz = {
  id: string
  owner_id: string
  title: string
  description: string | null
  created_at: string
  updated_at: string
}

function DashboardPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const [quizzes, setQuizzes] = useState<Quiz[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    const loadQuizzes = async () => {
      try {
        const response = await apiClient.get<Quiz[]>("/quizzes")
        setQuizzes(response.data)
      } catch (requestError) {
        if (axios.isAxiosError(requestError)) {
          const detail = requestError.response?.data?.detail

          setError(
            typeof detail === "string"
              ? detail
              : "Unable to load your quizzes",
          )
        } else {
          setError("Unable to load your quizzes")
        }
      } finally {
        setIsLoading(false)
      }
    }

    void loadQuizzes()
  }, [])

  const handleLogout = () => {
    logout()
    navigate("/login", { replace: true })
  }

  return (
    <main className="dashboard-page">
      <header className="dashboard-header">
        <div>
          <p className="dashboard-eyebrow">AI Quiz</p>
          <h1>Your quizzes</h1>
          <p className="dashboard-welcome">
            Welcome back, {user?.display_name}.
          </p>
        </div>

        <div className="dashboard-actions">
          <button
            className="dashboard-secondary-button"
            type="button"
            onClick={handleLogout}
          >
            Log out
          </button>

          <button
            className="dashboard-primary-button"
            type="button"
            onClick={() => navigate("/quizzes/new")}
          >
            + Create quiz
          </button>
        </div>
      </header>

      {error && (
        <div className="dashboard-message dashboard-error" role="alert">
          {error}
        </div>
      )}

      {isLoading ? (
        <section className="dashboard-state">
          <p>Loading your quizzes...</p>
        </section>
      ) : quizzes.length === 0 ? (
        <section className="dashboard-state dashboard-empty">
          <h2>No quizzes yet</h2>
          <p>Create your first quiz to get started.</p>

          <button
            className="dashboard-primary-button"
            type="button"
            onClick={() => navigate("/quizzes/new")}
          >
            Create your first quiz
          </button>
        </section>
      ) : (
        <section className="quiz-list-section">
          <div className="quiz-list-heading">
            <h2>
              {quizzes.length} {quizzes.length === 1 ? "quiz" : "quizzes"}
            </h2>
          </div>

          <div className="quiz-grid">
            {quizzes.map((quiz) => (
              <article
                className="quiz-card"
                key={quiz.id}
                tabIndex={0}
                role="button"
                onClick={() => navigate(`/quizzes/${quiz.id}`)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault()
                    navigate(`/quizzes/${quiz.id}`)
                  }
                }}
              >
                <div className="quiz-card-content">
                  <p className="quiz-card-label">Quiz</p>
                  <h3>{quiz.title}</h3>

                  <p className="quiz-card-description">
                    {quiz.description || "No description"}
                  </p>
                </div>

                <div className="quiz-card-footer">
                  <span>
                    Updated{" "}
                    {new Date(quiz.updated_at).toLocaleDateString()}
                  </span>

                  <span className="quiz-open-link">
                    Edit →
                  </span>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}
    </main>
  )
}

export default DashboardPage
