import { useEffect, useMemo, useState } from "react"

import axios from "axios"
import {
  ArrowLeft,
  Check,
  CheckCircle2,
  ChevronDown,
  CircleHelp,
  FileText,
  ListChecks,
  RefreshCw,
  X,
  XCircle,
} from "lucide-react"
import {
  useLocation,
  useNavigate,
  useParams,
} from "react-router-dom"

import apiClient from "../../api/client"
import "../../styles/pages/quizzes/QuizResultsPage.css"

type AnswerChoiceResult = {
  id: string
  text: string
  is_correct: boolean
  was_selected: boolean
  position: number
}

type AnswerResult = {
  question_id: string
  question_text: string
  question_type: string
  submitted_answer: string | null
  correct_answer: string | null
  is_correct: boolean | null
  answer_choices: AnswerChoiceResult[]
}

type QuizResults = {
  attempt_id?: string
  quiz_id: string
  score: number
  gradable_questions: number
  total_questions: number
  answers: AnswerResult[]
}


const INITIAL_VISIBLE_QUESTIONS = 5

function QuizResultsPage() {
  const { quizId, attemptId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()

  const guestResults =
    (location.state as { guestResults?: QuizResults } | null)
      ?.guestResults ?? null

  const isGuestResult = guestResults !== null

  const [results, setResults] = useState<QuizResults | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")
  const [expandedQuestions, setExpandedQuestions] = useState<Set<string>>(
    new Set(),
  )
  const [showAllQuestions, setShowAllQuestions] = useState(false)

  useEffect(() => {
    const loadResults = async () => {
      if (guestResults) {
        setResults(guestResults)
        setIsLoading(false)
        return
      }

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
  }, [quizId, attemptId, guestResults])

  const incorrectCount = useMemo(
    () =>
      results?.answers.filter(
        (answer) => answer.is_correct === false,
      ).length ?? 0,
    [results],
  )

  const ungradedCount = useMemo(
    () =>
      results?.answers.filter(
        (answer) => answer.is_correct === null,
      ).length ?? 0,
    [results],
  )

  const scorePercentage =
    results && results.gradable_questions > 0
      ? Math.round(
        (results.score / results.gradable_questions) * 100,
      )
      : 0

  const visibleAnswers =
    results && !showAllQuestions
      ? results.answers.slice(0, INITIAL_VISIBLE_QUESTIONS)
      : results?.answers ?? []

  const toggleQuestion = (questionId: string) => {
    setExpandedQuestions((current) => {
      const next = new Set(current)

      if (next.has(questionId)) {
        next.delete(questionId)
      } else {
        next.add(questionId)
      }

      return next
    })
  }

  const getQuestionTypeLabel = (questionType: string) => {
    if (questionType === "multiple_choice") {
      return "Multiple choice"
    }

    if (questionType === "math_work") {
      return "Math / Work"
    }

    return "Written answer"
  }

  if (isLoading) {
    return (
      <main className="quiz-results-page">
        <div className="results-state-card">
          Loading results...
        </div>
      </main>
    )
  }

  if (error || !results) {
    return (
      <main className="quiz-results-page">
        <div className="results-state-card">
          <p role="alert">
            {error || "Quiz results not found."}
          </p>

          <button
            type="button"
            className="results-secondary-button"
            onClick={() => navigate("/dashboard")}
          >
            <ArrowLeft size={17} />
            Back to dashboard
          </button>
        </div>
      </main>
    )
  }

  return (
    <main className="quiz-results-page">
      <div className="results-topbar">
        <button
          type="button"
          className="results-back-button"
          onClick={() =>
            isGuestResult
              ? navigate(`/quizzes/${quizId}`)
              : navigate(`/quizzes/${quizId}/history`)
          }
        >
          <ArrowLeft size={18} />
          {isGuestResult ? "Back to quiz" : "Back to attempt history"}
        </button>

        <button
          type="button"
          className="results-secondary-button"
          onClick={() => navigate(`/quizzes/${quizId}/take`)}
        >
          <RefreshCw size={17} />
          Retake quiz
        </button>
      </div>

      <section className="results-hero">
        <div className="results-hero-heading">
          <div className="results-hero-icon">
            <CheckCircle2 size={28} />
          </div>

          <div>
            <span className="results-eyebrow">
              Quiz complete
            </span>
            <h1>Your results</h1>
            <p>
              Review your performance and see how you answered
              each question.
            </p>
          </div>
        </div>

        <div className="results-summary">
          <div
            className="results-score-ring"
            style={{
              background: `conic-gradient(
                var(--color-primary-500) ${scorePercentage}%,
                var(--color-border-subtle) ${scorePercentage}% 100%
              )`,
            }}
          >
            <div className="results-score-ring-inner">
              <strong>{scorePercentage}%</strong>
              <span>Your score</span>
            </div>
          </div>

          <div className="results-summary-content">
            <div>
              <span className="results-summary-label">
                Automatically graded
              </span>

              <h2>
                {scorePercentage >= 80
                  ? "Great job!"
                  : scorePercentage >= 60
                    ? "Nice work!"
                    : "Keep practicing!"}
              </h2>

              <p>
                You answered {results.score} of{" "}
                {results.gradable_questions} automatically graded{" "}
                {results.gradable_questions === 1
                  ? "question"
                  : "questions"}{" "}
                correctly.
              </p>
            </div>

            <div className="results-stat-grid">
              <div className="results-stat results-stat--correct">
                <CheckCircle2 size={20} />
                <strong>{results.score}</strong>
                <span>Correct</span>
              </div>

              <div className="results-stat results-stat--incorrect">
                <XCircle size={20} />
                <strong>{incorrectCount}</strong>
                <span>Incorrect</span>
              </div>

              <div className="results-stat results-stat--ungraded">
                <CircleHelp size={20} />
                <strong>{ungradedCount}</strong>
                <span>Not graded</span>
              </div>

              <div className="results-stat">
                <ListChecks size={20} />
                <strong>{results.total_questions}</strong>
                <span>Total</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="results-review-section">
        <div className="results-review-header">
          <div>
            <span className="results-eyebrow">
              Question review
            </span>
            <h2>Review your answers</h2>
            <p>
              Open a question to compare your response with the
              correct answer.
            </p>
          </div>

          <div className="results-legend">
            <span>
              <i className="results-legend-dot results-legend-dot--correct" />
              Correct
            </span>

            <span>
              <i className="results-legend-dot results-legend-dot--incorrect" />
              Incorrect
            </span>

            <span>
              <i className="results-legend-dot results-legend-dot--ungraded" />
              Not graded
            </span>
          </div>
        </div>

        <div
          className={`results-question-list ${showAllQuestions
            ? "results-question-list--scrollable"
            : ""
            }`}
        >
          {visibleAnswers.map((answer, index) => {
            const isExpanded = expandedQuestions.has(
              answer.question_id,
            )

            return (
              <article
                className={`result-accordion ${answer.is_correct === true
                  ? "result-accordion--correct"
                  : answer.is_correct === false
                    ? "result-accordion--incorrect"
                    : "result-accordion--ungraded"
                  }`}
                key={answer.question_id}
              >
                <button
                  type="button"
                  className="result-accordion-trigger"
                  onClick={() =>
                    toggleQuestion(answer.question_id)
                  }
                  aria-expanded={isExpanded}
                >
                  <span className="result-status-icon">
                    {answer.is_correct === true ? (
                      <Check size={17} />
                    ) : answer.is_correct === false ? (
                      <X size={17} />
                    ) : (
                      <CircleHelp size={17} />
                    )}
                  </span>

                  <span className="result-question-copy">
                    <strong>
                      {index + 1}. {answer.question_text}
                    </strong>

                    <span className="result-question-type">
                      {getQuestionTypeLabel(
                        answer.question_type,
                      )}
                    </span>
                  </span>

                  <span className="result-question-status">
                    {answer.is_correct === true
                      ? "Correct"
                      : answer.is_correct === false
                        ? "Incorrect"
                        : "Not graded"}
                  </span>

                  <ChevronDown
                    className={`result-chevron ${isExpanded
                      ? "result-chevron--expanded"
                      : ""
                      }`}
                    size={19}
                  />
                </button>

                {isExpanded && (
                  <div className="result-accordion-content">
                    {answer.question_type ===
                      "multiple_choice" ? (
                      <div className="result-choice-list">
                        {answer.answer_choices.map(
                          (choice) => {
                            const choiceState =
                              choice.was_selected &&
                                choice.is_correct
                                ? "correct-selected"
                                : choice.was_selected
                                  ? "incorrect-selected"
                                  : choice.is_correct
                                    ? "correct-answer"
                                    : "neutral"

                            return (
                              <div
                                className={`result-choice result-choice--${choiceState}`}
                                key={choice.id}
                              >
                                <span className="result-choice-letter">
                                  {String.fromCharCode(
                                    65 + choice.position - 1,
                                  )}
                                </span>

                                <span className="result-choice-text">
                                  {choice.text}
                                </span>

                                <span className="result-choice-label">
                                  {choice.was_selected &&
                                    choice.is_correct
                                    ? "Your answer"
                                    : choice.was_selected
                                      ? "Your answer"
                                      : choice.is_correct
                                        ? "Correct answer"
                                        : ""}
                                </span>
                              </div>
                            )
                          },
                        )}
                      </div>
                    ) : (
                      <div className="result-written-review">
                        <div className="result-answer-box">
                          <span>Your answer</span>
                          <p>
                            {answer.submitted_answer ||
                              "No answer submitted"}
                          </p>
                        </div>

                        {answer.correct_answer !== null && (
                          <div className="result-answer-box result-answer-box--correct">
                            <span>Correct answer</span>
                            <p>{answer.correct_answer}</p>
                          </div>
                        )}

                        {answer.is_correct === null && (
                          <div className="result-ungraded-note">
                            <FileText size={18} />
                            <p>
                              Written responses are not
                              automatically graded.
                            </p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </article>
            )
          })}
        </div>

        {results.answers.length >
          INITIAL_VISIBLE_QUESTIONS && (
            <button
              type="button"
              className="results-show-all"
              onClick={() =>
                setShowAllQuestions((current) => !current)
              }
            >
              {showAllQuestions
                ? "Show fewer questions"
                : `Show all ${results.answers.length} questions`}

              <ChevronDown
                className={
                  showAllQuestions
                    ? "results-show-all-chevron--expanded"
                    : ""
                }
                size={18}
              />
            </button>
          )}
      </section>

      <section className="results-footer-card">
        <div>
          <span className="results-eyebrow">
            Ready for another try?
          </span>
          <h2>Keep up the momentum.</h2>
          <p>
            Review anything you missed and retake the quiz when
            you're ready.
          </p>
        </div>

        <div className="results-footer-actions">
          <button
            type="button"
            className="results-secondary-button"
            onClick={() => navigate("/dashboard")}
          >
            Back to dashboard
          </button>

          <button
            type="button"
            className="results-primary-button"
            onClick={() =>
              navigate(`/quizzes/${quizId}/take`)
            }
          >
            <RefreshCw size={17} />
            Retake quiz
          </button>
        </div>
      </section>
    </main>
  )
}

export default QuizResultsPage