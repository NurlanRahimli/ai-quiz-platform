import { useEffect, useState } from "react"
import axios from "axios"
import { useNavigate, useParams } from "react-router-dom"

import apiClient from "../../api/client"
import "../../styles/pages/quizzes/QuizResultsPage.css"

type AnswerResult = {
  question_id: string
  question_text: string
  question_type: string
  submitted_answer: string | null
  correct_answer: string | null
  is_correct: boolean | null
}

type QuizResults = {
  attempt_id: string
  quiz_id: string
  score: number
  gradable_questions: number
  total_questions: number
  answers: AnswerResult[]
}

function QuizResultsPage() {
  const { quizId, attemptId } = useParams()
  const navigate = useNavigate()

  const [results, setResults] = useState<QuizResults | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    const loadResults = async () => {
      if (!quizId || !attemptId) {
        setError("Quiz results not found.")
        setIsLoading(false)
        return
      }

      try {
        const response = await apiClient.get<QuizResults>(
          `/quizzes/${quizId}/attempts/${attemptId}/results`,
        )

        setResults(response.data)
      } catch (requestError) {
        if (
          axios.isAxiosError(requestError) &&
          requestError.response?.status === 404
        ) {
          setError("Quiz results not found.")
        } else {
          setError("Unable to load quiz results.")
        }
      } finally {
        setIsLoading(false)
      }
    }

    void loadResults()
  }, [quizId, attemptId])

  if (isLoading) {
    return <main className="quiz-results-page">Loading results...</main>
  }

  if (error || !results) {
    return (
      <main className="quiz-results-page">
        <p role="alert">{error || "Quiz results not found."}</p>

        <button
          type="button"
          onClick={() => navigate("/dashboard")}
        >
          Back to dashboard
        </button>
      </main>
    )
  }

  return (
    <main className="quiz-results-page">
      <header className="results-header">
        <p>Quiz complete</p>
        <h1>Your results</h1>

        <div className="score-card">
          <strong>
            {results.score} / {results.gradable_questions}
          </strong>

          <span>automatically graded questions correct</span>
        </div>

        {results.total_questions > results.gradable_questions && (
          <p>
            {results.total_questions - results.gradable_questions} written{" "}
            {results.total_questions - results.gradable_questions === 1
              ? "answer was"
              : "answers were"}{" "}
            not automatically graded.
          </p>
        )}
      </header>

      <section className="results-list">
        {results.answers.map((answer, index) => (
          <article
            className={`result-card ${
              answer.is_correct === true
                ? "result-correct"
                : answer.is_correct === false
                  ? "result-incorrect"
                  : "result-ungraded"
            }`}
            key={answer.question_id}
          >
            <div className="result-title">
              <h2>
                {index + 1}. {answer.question_text}
              </h2>

              <strong>
                {answer.is_correct === true
                  ? "Correct"
                  : answer.is_correct === false
                    ? "Incorrect"
                    : "Not graded"}
              </strong>
            </div>

            <div className="result-answer">
              <span>Your answer</span>
              <p>{answer.submitted_answer ?? "No answer"}</p>
            </div>

            {answer.correct_answer !== null && (
              <div className="result-answer">
                <span>Correct answer</span>
                <p>{answer.correct_answer}</p>
              </div>
            )}
          </article>
        ))}
      </section>

      <div className="results-actions">
        <button
          type="button"
          onClick={() => navigate("/dashboard")}
        >
          Back to dashboard
        </button>

        <button
          type="button"
          onClick={() => navigate(`/quizzes/${quizId}/take`)}
        >
          Take quiz again
        </button>
      </div>
    </main>
  )
}

export default QuizResultsPage