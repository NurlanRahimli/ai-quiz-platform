import { useEffect, useState } from "react"
import { useAuth } from "../../auth/useAuth"
import type { FormEvent } from "react"
import axios from "axios"
import { useNavigate, useParams } from "react-router-dom"

import MathWhiteboard from "../../components/quizzes/MathWhiteboard"
import Button from "../../components/ui/Button"

import Swal from "sweetalert2"

import {
  ArrowLeft,
  ArrowRight,
  Check,
  CheckCircle2,
  FileText,
  History,
  ListChecks,
  PenLine,
  Calculator,
} from "lucide-react"

import apiClient from "../../api/client"
import "../../styles/pages/quizzes/TakeQuizPage.css"

type AnswerChoice = {
  id: string
  text: string
  position: number
}

type Question = {
  id: string
  text: string
  question_type: string
  position: number
  answer_choices: AnswerChoice[]
}

type Quiz = {
  id: string
  title: string
  description: string | null
  questions: Question[]
}

type Answers = Record<string, string>

type WhiteboardDrawings = Record<string, string>

type QuizDraft = {
  answers: Answers
  whiteboardDrawings: WhiteboardDrawings
  currentQuestionIndex: number
}

function TakeQuizPage() {
  const { quizId } = useParams()
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()

  const [quiz, setQuiz] = useState<Quiz | null>(null)
  const [answers, setAnswers] = useState<Answers>({})
  const [whiteboardDrawings, setWhiteboardDrawings] = useState<WhiteboardDrawings>({})
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)

  useEffect(() => {
    const loadQuiz = async () => {
      if (!quizId) {
        setError("Quiz not found")
        setIsLoading(false)
        return
      }

      try {
        const response = await apiClient.get<Quiz>(
          `/quizzes/${quizId}/take`,
        )

        setQuiz(response.data)

        const draftKey = `quiz-draft:${response.data.id}`
        const savedDraft = localStorage.getItem(draftKey)

        if (savedDraft) {
          try {
            const draft = JSON.parse(savedDraft) as QuizDraft

            setAnswers(draft.answers ?? {})
            setWhiteboardDrawings(draft.whiteboardDrawings ?? {})

            const lastQuestionIndex = Math.max(
              response.data.questions.length - 1,
              0,
            )

            setCurrentQuestionIndex(
              Math.min(
                Math.max(draft.currentQuestionIndex ?? 0, 0),
                lastQuestionIndex,
              ),
            )
          } catch {
            localStorage.removeItem(draftKey)
          }
        }
      } catch (requestError) {
        if (
          axios.isAxiosError(requestError) &&
          requestError.response?.status === 404
        ) {
          setError("Quiz not found")
        } else {
          setError("Unable to load quiz")
        }
      } finally {
        setIsLoading(false)
      }
    }

    void loadQuiz()
  }, [quizId])

  useEffect(() => {
    if (!quiz) {
      return
    }

    const draft: QuizDraft = {
      answers,
      whiteboardDrawings,
      currentQuestionIndex,
    }

    localStorage.setItem(
      `quiz-draft:${quiz.id}`,
      JSON.stringify(draft),
    )
  }, [
    quiz,
    answers,
    whiteboardDrawings,
    currentQuestionIndex,
  ])

  const updateAnswer = (questionId: string, value: string) => {
    setAnswers((current) => ({
      ...current,
      [questionId]: value,
    }))
  }

  const questionCount = quiz?.questions.length ?? 0
  const currentQuestion = quiz?.questions[currentQuestionIndex] ?? null

  const answeredCount = quiz
    ? quiz.questions.filter(
      (question) => answers[question.id]?.trim(),
    ).length
    : 0

  const progressPercentage =
    questionCount > 0
      ? Math.round((answeredCount / questionCount) * 100)
      : 0

  const isFirstQuestion = currentQuestionIndex === 0
  const isLastQuestion =
    questionCount > 0 &&
    currentQuestionIndex === questionCount - 1

  const goToPreviousQuestion = () => {
    setCurrentQuestionIndex((current) =>
      Math.max(current - 1, 0),
    )
  }

  const goToNextQuestion = () => {
    setCurrentQuestionIndex((current) =>
      Math.min(current + 1, questionCount - 1),
    )
  }

  const goToQuestion = (index: number) => {
    setCurrentQuestionIndex(index)
  }

  const handleReviewAndSubmit = () => {
    document
      .querySelector<HTMLFormElement>(".take-quiz-workspace")
      ?.requestSubmit()
  }


  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (!quiz || !quizId) {
      return
    }

    const unansweredCount = quiz.questions.filter(
      (question) => !answers[question.id]?.trim(),
    ).length

    if (unansweredCount > 0) {
      const result = await Swal.fire({
        icon: "warning",
        title: "Unanswered questions",
        text: `You have ${unansweredCount} unanswered ${unansweredCount === 1 ? "question" : "questions"
          }. Unanswered questions will be marked incorrect. Are you sure you want to submit?`,
        showCancelButton: true,
        confirmButtonText: "Submit anyway",
        cancelButtonText: "Continue quiz",
        reverseButtons: true,
      })

      if (!result.isConfirmed) {
        return
      }
    }

    const submittedAnswers = quiz.questions.map((question) => {
      const answer = answers[question.id]?.trim() ?? ""

      if (question.question_type === "multiple_choice") {
        return {
          question_id: question.id,
          selected_choice_id: answer || null,
          text_answer: null,
        }
      }

      return {
        question_id: question.id,
        selected_choice_id: null,
        text_answer: answer || null,
      }
    })

    setIsSubmitting(true)
    setError("")

    try {
      if (isAuthenticated) {
        const response = await apiClient.post(
          `/quizzes/${quizId}/attempts`,
          {
            answers: submittedAnswers,
          },
        )

        localStorage.removeItem(`quiz-draft:${quizId}`)

        navigate(
          `/quizzes/${quizId}/attempts/${response.data.id}/results`,
          { replace: true },
        )

        return
      }

      const response = await apiClient.post(
        `/quizzes/${quizId}/attempts/guest`,
        {
          answers: submittedAnswers,
        },
      )

      localStorage.removeItem(`quiz-draft:${quizId}`)

      navigate(
        `/quizzes/${quizId}/guest-results`,
        {
          replace: true,
          state: {
            guestResults: response.data,
          },
        },
      )
    } catch (requestError) {
      if (axios.isAxiosError(requestError)) {
        const detail = requestError.response?.data?.detail

        setError(
          typeof detail === "string"
            ? detail
            : "Unable to submit quiz.",
        )
      } else {
        setError("Unable to submit quiz.")
      }
    } finally {
      setIsSubmitting(false)
    }
  }



  if (isLoading) {
    return <main>Loading quiz...</main>
  }

  if (error || !quiz) {
    return <main>{error || "Quiz not found"}</main>
  }

  return (
    <main className="take-quiz-page">
      <div className="take-quiz-header">
        <div className="take-quiz-header-main">
          <button
            className="take-quiz-back-button"
            type="button"
            onClick={() => navigate("/dashboard")}
            aria-label="Back to dashboard"
          >
            <ArrowLeft size={20} />
          </button>

          <div className="take-quiz-title-group">
            <h1>{quiz.title}</h1>

            <div className="take-quiz-meta">
              <span>
                {questionCount}{" "}
                {questionCount === 1 ? "question" : "questions"}
              </span>

              {quiz.description && (
                <>
                  <span className="take-quiz-meta-dot" />
                  <span>{quiz.description}</span>
                </>
              )}
            </div>
          </div>
        </div>

        {isAuthenticated && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => navigate(`/quizzes/${quizId}/history`)}
          >
            <History size={16} />
            Attempt history
          </Button>
        )}
      </div>

      {questionCount === 0 ? (
        <div className="take-quiz-empty">
          <FileText size={28} />
          <h2>No questions yet</h2>
          <p>This quiz doesn't have any questions yet.</p>
        </div>
      ) : (
        <>
          <div className="take-quiz-mobile-progress">
            <div className="take-quiz-progress-heading">
              <span>
                Question {currentQuestionIndex + 1} of {questionCount}
              </span>
              <span>{progressPercentage}% answered</span>
            </div>

            <div className="take-quiz-progress-track">
              <div
                className="take-quiz-progress-value"
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
          </div>

          <div className="take-quiz-layout">
            <form
              className="take-quiz-workspace"
              onSubmit={handleSubmit}
            >
              {error && (
                <div className="take-quiz-error" role="alert">
                  {error}
                </div>
              )}

              {currentQuestion && (
                <section className="take-question-card">
                  <div className="take-question-header">
                    <div className="take-question-labels">
                      <span className="take-question-number">
                        {currentQuestionIndex + 1}
                      </span>

                      <span className="take-question-type">
                        {currentQuestion.question_type ===
                          "multiple_choice" ? (
                          <>
                            <ListChecks size={15} />
                            Multiple choice
                          </>
                        ) : currentQuestion.question_type ===
                          "written_answer" ? (
                          <>
                            <PenLine size={15} />
                            Written answer
                          </>
                        ) : (
                          <>
                            <Calculator size={15} />
                            Math work
                          </>
                        )}
                      </span>
                    </div>

                    {answers[currentQuestion.id]?.trim() && (
                      <span className="take-question-answered">
                        <CheckCircle2 size={16} />
                        Answered
                      </span>
                    )}
                  </div>

                  <h2 className="take-question-text">
                    {currentQuestion.text}
                  </h2>

                  {currentQuestion.question_type ===
                    "multiple_choice" && (
                      <div className="take-answer-options">
                        {currentQuestion.answer_choices.map(
                          (choice, index) => {
                            const selected =
                              answers[currentQuestion.id] === choice.id

                            return (
                              <label
                                className={`take-answer-option ${selected
                                  ? "take-answer-option--selected"
                                  : ""
                                  }`}
                                key={choice.id}
                              >
                                <input
                                  type="radio"
                                  name={currentQuestion.id}
                                  value={choice.id}
                                  checked={selected}
                                  onChange={(event) =>
                                    updateAnswer(
                                      currentQuestion.id,
                                      event.target.value,
                                    )
                                  }
                                />

                                <span className="take-answer-letter">
                                  {String.fromCharCode(65 + index)}
                                </span>

                                <span className="take-answer-text">
                                  {choice.text}
                                </span>

                                <span className="take-answer-check">
                                  {selected && <Check size={16} />}
                                </span>
                              </label>
                            )
                          },
                        )}
                      </div>
                    )}

                  {currentQuestion.question_type ===
                    "written_answer" && (
                      <div className="take-written-answer">
                        <label
                          htmlFor={`written-answer-${currentQuestion.id}`}
                        >
                          Your answer
                        </label>

                        <textarea
                          id={`written-answer-${currentQuestion.id}`}
                          placeholder="Type your answer here..."
                          value={answers[currentQuestion.id] ?? ""}
                          onChange={(event) =>
                            updateAnswer(
                              currentQuestion.id,
                              event.target.value,
                            )
                          }
                        />
                      </div>
                    )}

                  {currentQuestion.question_type === "math_work" && (
                    <div className="math-work-answer">
                      <p className="math-work-instruction">
                        Use the whiteboard for your scratch work, then
                        enter your final answer below.
                      </p>

                      <MathWhiteboard
                        key={currentQuestion.id}
                        value={whiteboardDrawings[currentQuestion.id] ?? ""}
                        onChange={(drawing) => {
                          setWhiteboardDrawings((current) => ({
                            ...current,
                            [currentQuestion.id]: drawing,
                          }))
                        }}
                      />

                      <div className="math-final-answer">
                        <label
                          htmlFor={`math-answer-${currentQuestion.id}`}
                        >
                          Final answer
                        </label>

                        <input
                          id={`math-answer-${currentQuestion.id}`}
                          type="text"
                          placeholder="Enter your final answer..."
                          value={answers[currentQuestion.id] ?? ""}
                          onChange={(event) =>
                            updateAnswer(
                              currentQuestion.id,
                              event.target.value,
                            )
                          }
                        />

                        <p>
                          Your final answer will be used for grading.
                        </p>
                      </div>
                    </div>
                  )}

                  <div className="take-question-navigation">
                    <Button
                      type="button"
                      variant="outline"
                      disabled={isFirstQuestion}
                      onClick={goToPreviousQuestion}
                    >
                      <ArrowLeft size={17} />
                      Previous
                    </Button>

                    <Button
                      type="button"
                      disabled={isLastQuestion}
                      onClick={goToNextQuestion}
                    >
                      Next
                      <ArrowRight size={17} />
                    </Button>
                  </div>

                  <div className="take-question-mobile-submit">
                    <Button
                      type="button"
                      fullWidth
                      loading={isSubmitting}
                      disabled={isSubmitting}
                      onClick={handleReviewAndSubmit}
                    >
                      <CheckCircle2 size={17} />
                      Review & Submit
                    </Button>
                  </div>
                </section>
              )}
            </form>

            <aside className="take-quiz-sidebar">
              <div className="take-quiz-sidebar-card">
                <div className="take-quiz-sidebar-heading">
                  <span>Progress</span>
                  <strong>{progressPercentage}%</strong>
                </div>

                <p className="take-quiz-sidebar-description">
                  {answeredCount} of {questionCount} questions answered
                </p>

                <div className="take-quiz-progress-track">
                  <div
                    className="take-quiz-progress-value"
                    style={{ width: `${progressPercentage}%` }}
                  />
                </div>
              </div>

              <div className="take-quiz-sidebar-card">
                <h3>Questions</h3>

                <div className="take-quiz-question-grid">
                  {quiz.questions.map((question, index) => {
                    const answered =
                      Boolean(answers[question.id]?.trim())
                    const current =
                      index === currentQuestionIndex

                    return (
                      <button
                        key={question.id}
                        type="button"
                        className={[
                          "take-quiz-question-button",
                          answered
                            ? "take-quiz-question-button--answered"
                            : "",
                          current
                            ? "take-quiz-question-button--current"
                            : "",
                        ]
                          .filter(Boolean)
                          .join(" ")}
                        onClick={() => goToQuestion(index)}
                        aria-label={`Go to question ${index + 1}`}
                        aria-current={current ? "step" : undefined}
                      >
                        {answered && !current ? (
                          <Check size={16} />
                        ) : (
                          index + 1
                        )}
                      </button>
                    )
                  })}
                </div>

                <div className="take-quiz-question-legend">
                  <span>
                    <i className="take-quiz-legend-dot take-quiz-legend-dot--answered" />
                    Answered
                  </span>

                  <span>
                    <i className="take-quiz-legend-dot take-quiz-legend-dot--current" />
                    Current
                  </span>

                  <span>
                    <i className="take-quiz-legend-dot" />
                    Not answered
                  </span>
                </div>
              </div>

              <div className="take-quiz-sidebar-card">
                <h3>Quiz overview</h3>

                <dl className="take-quiz-overview">
                  <div>
                    <dt>Total questions</dt>
                    <dd>{questionCount}</dd>
                  </div>

                  <div>
                    <dt>Answered</dt>
                    <dd>{answeredCount}</dd>
                  </div>

                  <div>
                    <dt>Remaining</dt>
                    <dd>{questionCount - answeredCount}</dd>
                  </div>
                </dl>
              </div>

              <Button
                type="button"
                fullWidth
                onClick={handleReviewAndSubmit}
              >
                <CheckCircle2 size={17} />
                Review & Submit
              </Button>
            </aside>
          </div>
        </>
      )}
    </main>
  )
}

export default TakeQuizPage