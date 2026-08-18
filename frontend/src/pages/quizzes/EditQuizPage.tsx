import { useEffect, useState } from "react"
import type { FormEvent } from "react"
import axios from "axios"
import { useNavigate, useParams } from "react-router-dom"

import apiClient from "../../api/client"
import "./EditQuizPage.css"

type AnswerChoice = {
  id: string
  text: string
  is_correct: boolean
  position: number
}

type Question = {
  id: string
  quiz_id: string
  text: string
  question_type: string
  position: number
  answer_choices: AnswerChoice[]
}

type Quiz = {
  id: string
  owner_id: string
  title: string
  description: string | null
  created_at: string
  updated_at: string
  questions: Question[]
}

type QuizForm = {
  title: string
  description: string
}

function EditQuizPage() {
  const { quizId } = useParams()
  const navigate = useNavigate()

  const [quiz, setQuiz] = useState<Quiz | null>(null)
  const [form, setForm] = useState<QuizForm>({
    title: "",
    description: "",
  })

  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState("")
  const [successMessage, setSuccessMessage] = useState("")
  const [editingQuestionId, setEditingQuestionId] = useState<string | null>(
    null,
  )
  const [deletingQuestionId, setDeletingQuestionId] = useState<string | null>(
    null,
  )

  const [editingText, setEditingText] = useState("")
  const [editingChoices, setEditingChoices] = useState<AnswerChoice[]>([])
  const [isSavingQuestion, setIsSavingQuestion] = useState(false)


  useEffect(() => {
    const loadQuiz = async () => {
      if (!quizId) {
        setError("Quiz not found")
        setIsLoading(false)
        return
      }

      try {
        const response = await apiClient.get<Quiz>(
          `/quizzes/${quizId}`,
        )

        setQuiz(response.data)

        setForm({
          title: response.data.title,
          description: response.data.description ?? "",
        })
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

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault()

    const title = form.title.trim()

    if (!title) {
      setError("Quiz title is required")
      return
    }

    if (title.length > 255) {
      setError("Quiz title must be 255 characters or fewer")
      return
    }

    if (form.description.length > 1000) {
      setError("Description must be 1000 characters or fewer")
      return
    }

    if (!quizId) {
      return
    }

    setIsSaving(true)
    setError("")
    setSuccessMessage("")

    try {
      const response = await apiClient.patch<Quiz>(
        `/quizzes/${quizId}`,
        {
          title,
          description: form.description.trim() || null,
        },
      )

      setQuiz((current) =>
        current
          ? {
              ...current,
              title: response.data.title,
              description: response.data.description,
              updated_at: response.data.updated_at,
            }
          : current,
      )

      setForm({
        title: response.data.title,
        description: response.data.description ?? "",
      })

      setSuccessMessage("Quiz details saved.")
    } catch (requestError) {
      if (axios.isAxiosError(requestError)) {
        const detail = requestError.response?.data?.detail

        setError(
          typeof detail === "string"
            ? detail
            : "Unable to update quiz",
        )
      } else {
        setError("Something went wrong. Please try again.")
      }
    } finally {
      setIsSaving(false)
    }
  }

  const startEditingQuestion = (question: Question) => {
  setEditingQuestionId(question.id)
  setEditingText(question.text)
  setEditingChoices(
    question.answer_choices.map((choice) => ({
      ...choice,
    })),
  )
  setError("")
  setSuccessMessage("")
}

const cancelEditingQuestion = () => {
  setEditingQuestionId(null)
  setEditingText("")
  setEditingChoices([])
}

const updateChoiceText = (choiceId: string, text: string) => {
  setEditingChoices((current) =>
    current.map((choice) =>
      choice.id === choiceId
        ? {
            ...choice,
            text,
          }
        : choice,
    ),
  )
}

const selectCorrectChoice = (choiceId: string) => {
  setEditingChoices((current) =>
    current.map((choice) => ({
      ...choice,
      is_correct: choice.id === choiceId,
    })),
  )
}


const deleteQuestion = async (question: Question) => {
  if (!quizId) {
    return
  }

  const confirmed = window.confirm(
    `Delete question ${question.position}? This cannot be undone.`,
  )

  if (!confirmed) {
    return
  }

  setDeletingQuestionId(question.id)
  setError("")
  setSuccessMessage("")

  try {
    await apiClient.delete(
      `/quizzes/${quizId}/questions/${question.id}`,
    )

    setQuiz((current) =>
      current
        ? {
            ...current,
            questions: current.questions
              .filter(
                (existingQuestion) =>
                  existingQuestion.id !== question.id,
              )
              .map((existingQuestion, index) => ({
                ...existingQuestion,
                position: index + 1,
              })),
          }
        : current,
    )

    if (editingQuestionId === question.id) {
      cancelEditingQuestion()
    }

    setSuccessMessage("Question deleted.")
  } catch (requestError) {
    if (axios.isAxiosError(requestError)) {
      const detail = requestError.response?.data?.detail

      setError(
        typeof detail === "string"
          ? detail
          : "Unable to delete question",
      )
    } else {
      setError("Something went wrong. Please try again.")
    }
  } finally {
    setDeletingQuestionId(null)
  }
}


const saveQuestion = async (question: Question) => {
  if (!quizId) {
    return
  }

  const text = editingText.trim()

  if (!text) {
    setError("Question cannot be empty")
    return
  }

  if (
    question.question_type === "multiple_choice" &&
    editingChoices.some((choice) => !choice.text.trim())
  ) {
    setError("Answer choices cannot be empty")
    return
  }

  setIsSavingQuestion(true)
  setError("")
  setSuccessMessage("")

  try {
    const payload =
      question.question_type === "multiple_choice"
        ? {
            text,
            choices: editingChoices.map((choice) => ({
              text: choice.text.trim(),
              is_correct: choice.is_correct,
            })),
          }
        : {
            text,
          }

    const response = await apiClient.patch<Question>(
      `/quizzes/${quizId}/questions/${question.id}`,
      payload,
    )

    setQuiz((current) =>
      current
        ? {
            ...current,
            questions: current.questions.map((existingQuestion) =>
              existingQuestion.id === question.id
                ? response.data
                : existingQuestion,
            ),
          }
        : current,
    )

    cancelEditingQuestion()
    setSuccessMessage("Question saved.")
  } catch (requestError) {
    if (axios.isAxiosError(requestError)) {
      const detail = requestError.response?.data?.detail

      setError(
        typeof detail === "string"
          ? detail
          : "Unable to update question",
      )
    } else {
      setError("Something went wrong. Please try again.")
    }
  } finally {
    setIsSavingQuestion(false)
  }
}

  if (isLoading) {
    return (
      <main className="edit-quiz-page">
        <p>Loading quiz...</p>
      </main>
    )
  }

  if (!quiz) {
    return (
      <main className="edit-quiz-page">
        <section className="edit-quiz-card">
          <h1>Quiz unavailable</h1>
          <p className="form-message form-error">
            {error || "Quiz not found"}
          </p>

          <button
            type="button"
            className="secondary-button"
            onClick={() => navigate("/dashboard")}
          >
            Back to dashboard
          </button>
        </section>
      </main>
    )
  }

  return (
    <main className="edit-quiz-page">
      <section className="edit-quiz-card">
        <button
          type="button"
          className="back-button"
          onClick={() => navigate("/dashboard")}
        >
          ← Back to dashboard
        </button>

        <div className="edit-quiz-heading">
          <p className="quiz-eyebrow">Quiz editor</p>
          <h1>{quiz.title}</h1>
          <p>
            Edit your quiz details and manage its questions.
          </p>
        </div>

        {error && (
          <div className="form-message form-error" role="alert">
            {error}
          </div>
        )}

        {successMessage && (
          <div className="form-message form-success" role="status">
            {successMessage}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-field">
            <label htmlFor="edit-title">Quiz title</label>

            <input
              id="edit-title"
              type="text"
              maxLength={255}
              value={form.title}
              onChange={(event) => {
                setForm((current) => ({
                  ...current,
                  title: event.target.value,
                }))
                setError("")
                setSuccessMessage("")
              }}
            />
          </div>

          <div className="form-field">
            <label htmlFor="edit-description">
              Description
              <span className="optional-label"> Optional</span>
            </label>

            <textarea
              id="edit-description"
              maxLength={1000}
              value={form.description}
              onChange={(event) => {
                setForm((current) => ({
                  ...current,
                  description: event.target.value,
                }))
                setError("")
                setSuccessMessage("")
              }}
            />

            <div className="description-footer">
              <span />
              <span className="character-count">
                {form.description.length}/1000
              </span>
            </div>
          </div>

          <div className="quiz-form-actions">
            <button
              type="submit"
              className="quiz-primary-button"
              disabled={isSaving}
            >
              {isSaving ? "Saving..." : "Save changes"}
            </button>
          </div>
        </form>

        <section className="questions-section">
          <div>
            <p className="quiz-eyebrow">Questions</p>
            <h2>
              {quiz.questions.length === 1
                ? "1 question"
                : `${quiz.questions.length} questions`}
            </h2>
          </div>

          {quiz.questions.length === 0 ? (
            <p className="empty-questions">
              This quiz doesn't have any questions yet.
            </p>
          ) : (
            <div className="question-list">
                {quiz.questions.map((question) => {
                    const isEditing = editingQuestionId === question.id

                    return (
                    <article
                        className="question-card"
                        key={question.id}
                    >
                        <div className="question-card-heading">
                        <span>Question {question.position}</span>
                        <span>
                            {question.question_type.replaceAll("_", " ")}
                        </span>
                        </div>

                        {isEditing ? (
                        <div className="question-editor">
                            <div className="form-field">
                            <label htmlFor={`question-${question.id}`}>
                                Question
                            </label>

                            <textarea
                                id={`question-${question.id}`}
                                maxLength={2000}
                                value={editingText}
                                onChange={(event) => {
                                setEditingText(event.target.value)
                                setError("")
                                }}
                            />
                            </div>

                            {question.question_type === "multiple_choice" && (
                            <div className="choice-editor">
                                <p className="choice-editor-label">
                                Answer choices
                                </p>

                                {editingChoices.map((choice, index) => (
                                <div
                                    className="choice-edit-row"
                                    key={choice.id}
                                >
                                    <input
                                    type="radio"
                                    name={`correct-${question.id}`}
                                    checked={choice.is_correct}
                                    onChange={() =>
                                        selectCorrectChoice(choice.id)
                                    }
                                    aria-label={`Mark answer ${index + 1} as correct`}
                                    />

                                    <input
                                    type="text"
                                    value={choice.text}
                                    maxLength={1000}
                                    onChange={(event) =>
                                        updateChoiceText(
                                        choice.id,
                                        event.target.value,
                                        )
                                    }
                                    aria-label={`Answer ${index + 1}`}
                                    />
                                </div>
                                ))}

                                <p className="choice-help">
                                Select the radio button beside the correct answer.
                                </p>
                            </div>
                            )}

                            <div className="question-actions">
                                <button
                                    type="button"
                                    className="secondary-button"
                                    onClick={cancelEditingQuestion}
                                    disabled={isSavingQuestion}
                                >
                                    Cancel
                                </button>

                                <button
                                    type="button"
                                    className="quiz-primary-button"
                                    onClick={() => void saveQuestion(question)}
                                    disabled={isSavingQuestion}
                                >
                                    {isSavingQuestion
                                    ? "Saving..."
                                    : "Save question"}
                                </button>
                            </div>
                        </div>
                        ) : (
                        <>
                            <p className="question-text">
                            {question.text}
                            </p>

                            {question.question_type === "multiple_choice" && (
                            <ol>
                                {question.answer_choices.map((choice) => (
                                <li key={choice.id}>
                                    {choice.text}
                                    {choice.is_correct ? " ✓" : ""}
                                </li>
                                ))}
                            </ol>
                            )}

                            <div className="question-actions">
                                <button
                                    type="button"
                                    className="secondary-button"
                                    onClick={() => startEditingQuestion(question)}
                                    disabled={deletingQuestionId === question.id}
                                >
                                    Edit
                                </button>

                                <button
                                    type="button"
                                    className="delete-question-button"
                                    onClick={() => void deleteQuestion(question)}
                                    disabled={deletingQuestionId === question.id}
                                >
                                    {deletingQuestionId === question.id
                                    ? "Deleting..."
                                    : "Delete"}
                                </button>
                            </div>
                        </>
                        )}
                    </article>
                    )
                })}
                </div>
          )}
        </section>
      </section>
    </main>
  )
}

export default EditQuizPage