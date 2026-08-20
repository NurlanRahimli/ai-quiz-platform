import { useEffect, useState } from "react"
import axios from "axios"
import { useNavigate, useParams } from "react-router-dom"
import apiClient from "../../api/client"
import "../../styles/pages/quizzes/QuizAttemptHistoryPage.css"

type Quiz = {
  id: string
  title: string
}

type AttemptHistoryItem = {
  attempt_id: string
  submitted_at: string
  score: number
  gradable_questions: number
  total_questions: number
}

function QuizAttemptHistoryPage() {
  const { quizId } = useParams()
  const navigate = useNavigate()

  const [quiz, setQuiz] = useState<Quiz | null>(null)
  const [attempts, setAttempts] = useState<AttemptHistoryItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    const loadHistory = async () => {
      if (!quizId) {
        setError("Quiz not found")
        setIsLoading(false)
        return
      }

      try {
        const [quizResponse, attemptsResponse] = await Promise.all([
          apiClient.get<Quiz>(`/quizzes/${quizId}`),
          apiClient.get<AttemptHistoryItem[]>(
            `/quizzes/${quizId}/attempts`,
          ),
        ])

        setQuiz(quizResponse.data)
        setAttempts(attemptsResponse.data)
      } catch (requestError) {
        if (
          axios.isAxiosError(requestError) &&
          requestError.response?.status === 404
        ) {
          setError("Quiz not found")
        } else {
          setError("Unable to load attempt history")
        }
      } finally {
        setIsLoading(false)
      }
    }

    void loadHistory()
  }, [quizId])

  if (isLoading) {
    return (
      <main className="attempt-history-page">
        <p>Loading attempt history...</p>
      </main>
    )
  }

  if (error || !quiz) {
    return (
      <main className="attempt-history-page">
        <p>{error || "Quiz not found"}</p>
      </main>
    )
  }

  return (
    <main className="attempt-history-page">
      <div className="attempt-history-container">
        <button
          className="history-back-button"
          type="button"
          onClick={() => navigate("/dashboard")}
        >
          ← Back to dashboard
        </button>

        <header className="attempt-history-header">
          <p className="history-eyebrow">Quiz history</p>

          <h1>{quiz.title}</h1>

          <p className="history-description">
            Review your previous attempts and open any submission
            to see the full results.
          </p>
        </header>

        <section className="history-summary">
          <div>
            <span className="history-summary-number">
              {attempts.length}
            </span>
            <span className="history-summary-label">
              {attempts.length === 1 ? "Attempt" : "Attempts"}
            </span>
          </div>

          <button
            type="button"
            className="history-take-button"
            onClick={() => navigate(`/quizzes/${quizId}/take`)}
          >
            Take quiz again
          </button>
        </section>

        {attempts.length === 0 ? (
          <section className="history-empty">
            <h2>No attempts yet</h2>
            <p>
              Once you complete this quiz, your previous attempts
              will appear here.
            </p>

            <button
              type="button"
              onClick={() => navigate(`/quizzes/${quizId}/take`)}
            >
              Take quiz
            </button>
          </section>
        ) : (
          <section className="history-list">
            {attempts.map((attempt, index) => {
              const percentage =
                attempt.gradable_questions === 0
                  ? null
                  : Math.round(
                      (attempt.score /
                        attempt.gradable_questions) *
                        100,
                    )

              return (
                <article
                  className="history-card"
                  key={attempt.attempt_id}
                >
                  <div className="history-card-main">
                    <div className="history-attempt-number">
                      {attempts.length - index}
                    </div>

                    <div>
                      <h2>
                        Attempt {attempts.length - index}
                      </h2>

                      <p>
                        {new Date(
                          attempt.submitted_at,
                        ).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  <div className="history-card-score">
                    {percentage === null ? (
                      <>
                        <strong>Not graded</strong>
                        <span>
                          {attempt.total_questions} questions
                        </span>
                      </>
                    ) : (
                      <>
                        <strong>{percentage}%</strong>
                        <span>
                            {attempt.score} /{" "}
                            {attempt.gradable_questions} correct
                        </span>
                      </>
                    )}
                  </div>

                  <button
                    className="history-results-button"
                    type="button"
                    onClick={() =>
                      navigate(
                        `/quizzes/${quizId}/attempts/${attempt.attempt_id}/results`,
                      )
                    }
                  >
                    View results →
                  </button>
                </article>
              )
            })}
          </section>
        )}
      </div>
    </main>
  )
}

export default QuizAttemptHistoryPage