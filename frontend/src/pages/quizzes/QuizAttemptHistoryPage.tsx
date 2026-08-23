import {
  useEffect,
  useState,
  useRef,
} from "react"
import { useNavigate, useParams } from "react-router-dom"

import axios from "axios"
import apiClient from "../../api/client"

import {
  ArrowLeft,
  ArrowRight,
  RotateCcw,
} from "lucide-react";

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
  const [visibleCount, setVisibleCount] = useState(10)
  const loadMoreRef = useRef<HTMLDivElement | null>(null)

  const visibleAttempts = attempts.slice(0, visibleCount)
  const hasMoreAttempts = visibleCount < attempts.length

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


  useEffect(() => {
    const target = loadMoreRef.current

    if (!target || !hasMoreAttempts) {
      return
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const firstEntry = entries[0]

        if (firstEntry?.isIntersecting) {
          setVisibleCount((current) =>
            Math.min(current + 10, attempts.length),
          )
        }
      },
      {
        rootMargin: "180px 0px",
      },
    )

    observer.observe(target)

    return () => {
      observer.disconnect()
    }
  }, [hasMoreAttempts, attempts.length])


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
          onClick={() => navigate("/attempts")}
        >
          <ArrowLeft
            size={17}
            strokeWidth={2}
            aria-hidden="true"
          />
          Back to attempts
        </button>

        <header className="attempt-history-header">
          <div className="attempt-history-header__content">
            <p className="history-eyebrow">
              Attempt History
            </p>

            <h1>{quiz.title}</h1>

            <p className="history-description">
              Review your previous attempts and open any submission
              to see the full results.
            </p>
          </div>

          <button
            type="button"
            className="history-take-button"
            onClick={() => navigate(`/quizzes/${quizId}/take`)}
          >
            <RotateCcw
              size={17}
              strokeWidth={2}
              aria-hidden="true"
            />
            Take again
          </button>
        </header>

        <div className="history-list-heading">
          <h2>Attempts</h2>

          <span>
            {attempts.length}{" "}
            {attempts.length === 1 ? "attempt" : "attempts"}
          </span>
        </div>

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
            {visibleAttempts.map((attempt, index) => {
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
                  className="history-card history-card--enter"
                  key={attempt.attempt_id}
                  style={{
                    animationDelay: `${(index % 10) * 35}ms`,
                  }}
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
                    <span>View results</span>

                    <ArrowRight
                      size={16}
                      strokeWidth={2}
                      aria-hidden="true"
                    />
                  </button>
                </article>
              )
            })}
            {hasMoreAttempts && (
              <div
                ref={loadMoreRef}
                className="history-load-more"
                aria-hidden="true"
              >
                <span />
                Loading more attempts...
              </div>
            )}
          </section>
        )}
      </div>
    </main>
  )
}

export default QuizAttemptHistoryPage