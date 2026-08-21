import { useEffect, useState, useRef } from "react";
import type { FormEvent } from "react";
import axios from "axios";
import {
  ArrowLeft,
  Clock3,
  FileQuestion,
  Play,
  Save,
  Plus,
  X,
  Info,
  Check,
  ListChecks,
  PenLine,
  Calculator,
  Trash2,
} from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import apiClient from "../../api/client";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import Input from "../../components/ui/Input";
import "../../styles/pages/quizzes/EditQuizPage.css";

type AnswerChoice = {
  id: string
  text: string
  is_correct: boolean
  position: number
}

type NewQuestionType =
  | "multiple_choice"
  | "written_answer"
  | "math_work"

type NewQuestionChoice = {
  id: string
  text: string
  is_correct: boolean
}

type NewQuestionDraft = {
  isAddingQuestion: boolean
  questionType: NewQuestionType
  questionText: string
  expectedAnswer: string
  choices: NewQuestionChoice[]
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

const QUESTIONS_PER_BATCH = 10

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
  const [visibleQuestionCount, setVisibleQuestionCount] = useState(QUESTIONS_PER_BATCH)
  const [error, setError] = useState("")
  const [questionError, setQuestionError] = useState("")
  const [newQuestionError, setNewQuestionError] = useState("")
  const [successMessage, setSuccessMessage] = useState("")
  const [editingQuestionId, setEditingQuestionId] = useState<string | null>(
    null,
  )
  const [deletingQuestionId, setDeletingQuestionId] = useState<string | null>(
    null,
  )

  const [editingText, setEditingText] = useState("")
  const [editingChoices, setEditingChoices] = useState<AnswerChoice[]>([])
  const [editingExpectedAnswer, setEditingExpectedAnswer] = useState("")
  const [isSavingQuestion, setIsSavingQuestion] = useState(false)
  const questionCount = quiz?.questions.length ?? 0;
  const visibleQuestions = quiz?.questions.slice(0, visibleQuestionCount) ?? []
  const hasMoreQuestions = visibleQuestionCount < questionCount
  const newQuestionCardRef = useRef<HTMLDivElement>(null)

  const [isAddingQuestion, setIsAddingQuestion] = useState(false)
  const [newQuestionType, setNewQuestionType] =
    useState<NewQuestionType>("multiple_choice")
  const [newQuestionText, setNewQuestionText] = useState("")
  const [newExpectedAnswer, setNewExpectedAnswer] = useState("")
  const [newQuestionChoices, setNewQuestionChoices] = useState<
    NewQuestionChoice[]
  >([
    {
      id: "choice-1",
      text: "",
      is_correct: true,
    },
    {
      id: "choice-2",
      text: "",
      is_correct: false,
    },
  ])
  const [isCreatingQuestion, setIsCreatingQuestion] = useState(false)

  const formattedUpdatedAt = quiz
    ? new Date(quiz.updated_at).toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    })
    : "";


  useEffect(() => {
    if (!isAddingQuestion) {
      return
    }

    newQuestionCardRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    })
  }, [isAddingQuestion])


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
        const draftKey = `edit-quiz-draft:${response.data.id}`
        const savedDraft = localStorage.getItem(draftKey)

        if (savedDraft) {
          try {
            const draft = JSON.parse(savedDraft) as NewQuestionDraft

            setIsAddingQuestion(draft.isAddingQuestion ?? false)
            setNewQuestionType(
              draft.questionType ?? "multiple_choice",
            )
            setNewQuestionText(draft.questionText ?? "")
            setNewExpectedAnswer(draft.expectedAnswer ?? "")

            if (
              Array.isArray(draft.choices) &&
              draft.choices.length >= 2
            ) {
              setNewQuestionChoices(draft.choices)
            }
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
    if (!quizId || isLoading) {
      return
    }

    const draftKey = `edit-quiz-draft:${quizId}`

    if (!isAddingQuestion) {
      localStorage.removeItem(draftKey)
      return
    }

    const draft: NewQuestionDraft = {
      isAddingQuestion,
      questionType: newQuestionType,
      questionText: newQuestionText,
      expectedAnswer: newExpectedAnswer,
      choices: newQuestionChoices,
    }

    localStorage.setItem(draftKey, JSON.stringify(draft))
  }, [
    quizId,
    isLoading,
    isAddingQuestion,
    newQuestionType,
    newQuestionText,
    newExpectedAnswer,
    newQuestionChoices,
  ])


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
    setQuestionError("")
    setSuccessMessage("")
  }

  const cancelEditingQuestion = () => {
    setEditingQuestionId(null)
    setEditingText("")
    setEditingChoices([])
    setEditingExpectedAnswer("")
    setQuestionError("")
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
    setQuestionError("")
  }

  const selectCorrectChoice = (choiceId: string) => {
    setEditingChoices((current) =>
      current.map((choice) => ({
        ...choice,
        is_correct: choice.id === choiceId,
      })),
    )
    setQuestionError("")
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


  const resetNewQuestion = () => {
    if (quizId) {
      localStorage.removeItem(`edit-quiz-draft:${quizId}`)
    }

    setIsAddingQuestion(false)
    setNewQuestionType("multiple_choice")
    setNewQuestionText("")
    setNewExpectedAnswer("")
    setNewQuestionChoices([
      {
        id: "choice-1",
        text: "",
        is_correct: true,
      },
      {
        id: "choice-2",
        text: "",
        is_correct: false,
      },
    ])
    setNewQuestionError("")
  }

  const updateNewChoiceText = (choiceId: string, text: string) => {
    setNewQuestionChoices((current) =>
      current.map((choice) =>
        choice.id === choiceId
          ? {
            ...choice,
            text,
          }
          : choice,
      ),
    )

    setNewQuestionError("")
  }

  const selectNewCorrectChoice = (choiceId: string) => {
    setNewQuestionChoices((current) =>
      current.map((choice) => ({
        ...choice,
        is_correct: choice.id === choiceId,
      })),
    )

    setNewQuestionError("")
  }

  const addNewChoice = () => {
    setNewQuestionChoices((current) => [
      ...current,
      {
        id: crypto.randomUUID(),
        text: "",
        is_correct: false,
      },
    ])
  }

  const removeNewChoice = (choiceId: string) => {
    setNewQuestionChoices((current) => {
      if (current.length <= 2) {
        return current
      }

      const nextChoices = current.filter(
        (choice) => choice.id !== choiceId,
      )

      if (!nextChoices.some((choice) => choice.is_correct)) {
        nextChoices[0] = {
          ...nextChoices[0],
          is_correct: true,
        }
      }

      return nextChoices
    })
  }

  const createQuestion = async () => {
    if (!quizId) {
      return
    }

    const text = newQuestionText.trim()

    if (!text) {
      setNewQuestionError("Question cannot be empty")
      return
    }

    if (
      newQuestionType === "multiple_choice" &&
      newQuestionChoices.some((choice) => !choice.text.trim())
    ) {
      setNewQuestionError("Answer choices cannot be empty")
      return
    }

    const expectedAnswer = newExpectedAnswer.trim()

    if (
      newQuestionType === "math_work" &&
      !expectedAnswer
    ) {
      setNewQuestionError("Expected answer cannot be empty")
      return
    }

    setIsCreatingQuestion(true)
    setNewQuestionError("")
    setSuccessMessage("")

    try {
      let response

      if (newQuestionType === "multiple_choice") {
        response = await apiClient.post<Question>(
          `/quizzes/${quizId}/questions`,
          {
            text,
            choices: newQuestionChoices.map((choice) => ({
              text: choice.text.trim(),
              is_correct: choice.is_correct,
            })),
          },
        )
      } else if (newQuestionType === "written_answer") {
        response = await apiClient.post<Question>(
          `/quizzes/${quizId}/questions/written`,
          {
            text,
          },
        )
      } else {
        response = await apiClient.post<Question>(
          `/quizzes/${quizId}/questions/math-work`,
          {
            text,
            expected_answer: expectedAnswer,
          },
        )
      }

      setQuiz((current) =>
        current
          ? {
            ...current,
            questions: [
              ...current.questions,
              response.data,
            ],
          }
          : current,
      )

      resetNewQuestion()
      setSuccessMessage("Question added successfully")
    } catch (requestError) {
      if (axios.isAxiosError(requestError)) {
        const detail = requestError.response?.data?.detail

        setNewQuestionError(
          typeof detail === "string"
            ? detail
            : "Unable to add question",
        )
      } else {
        setNewQuestionError("Something went wrong. Please try again.")
      }
    } finally {
      setIsCreatingQuestion(false)
    }
  }


  const saveQuestion = async (question: Question) => {
    if (!quizId) {
      return
    }

    const text = editingText.trim()
    const expectedAnswer = editingExpectedAnswer.trim()

    if (!text) {
      setQuestionError("Question cannot be empty")
      return
    }

    if (question.question_type === "multiple_choice") {
      if (editingChoices.length < 2) {
        setQuestionError("A multiple-choice question must have at least two answers")
        return
      }

      if (editingChoices.some((choice) => !choice.text.trim())) {
        setQuestionError("Answer choices cannot be empty")
        return
      }

      const correctChoiceCount = editingChoices.filter(
        (choice) => choice.is_correct,
      ).length

      if (correctChoiceCount !== 1) {
        setQuestionError("Select exactly one correct answer")
        return
      }
    }

    if (question.question_type === "math_work" && !expectedAnswer) {
      setQuestionError("Expected answer cannot be empty")
      return
    }

    setIsSavingQuestion(true)
    setQuestionError("")
    setSuccessMessage("")

    try {
      let payload:
        | {
          text: string
        }
        | {
          text: string
          expected_answer: string
        }
        | {
          text: string
          choices: {
            text: string
            is_correct: boolean
          }[]
        }

      if (question.question_type === "multiple_choice") {
        payload = {
          text,
          choices: editingChoices.map((choice) => ({
            text: choice.text.trim(),
            is_correct: choice.is_correct,
          })),
        }
      } else if (question.question_type === "math_work") {
        payload = {
          text,
          expected_answer: expectedAnswer,
        }
      } else {
        payload = {
          text,
        }
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

        if (typeof detail === "string") {
          setQuestionError(detail)
        } else if (Array.isArray(detail)) {
          const firstError = detail[0]

          setQuestionError(
            typeof firstError?.msg === "string"
              ? firstError.msg
              : "Unable to update question",
          )
        } else {
          setQuestionError("Unable to update question")
        }
      } else {
        setQuestionError("Something went wrong. Please try again.")
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


  const handleQuestionListScroll = (
    event: React.UIEvent<HTMLDivElement>,
  ) => {
    if (!hasMoreQuestions) {
      return
    }

    const { scrollTop, scrollHeight, clientHeight } = event.currentTarget

    const isNearBottom =
      scrollHeight - scrollTop - clientHeight < 120

    if (isNearBottom) {
      setVisibleQuestionCount((current) =>
        Math.min(current + QUESTIONS_PER_BATCH, questionCount),
      )
    }
  }

  return (
    <main className="edit-quiz-page">
      <div className="edit-quiz-page__container">
        <button
          type="button"
          className="edit-quiz-page__back"
          onClick={() => navigate("/dashboard")}
        >
          <ArrowLeft size={18} strokeWidth={2} aria-hidden="true" />
          <span>Dashboard</span>
        </button>

        <header className="edit-quiz-page__header">
          <div className="edit-quiz-page__heading">
            <div className="edit-quiz-page__eyebrow">
              <span className="edit-quiz-page__eyebrow-icon">
                <FileQuestion size={16} strokeWidth={2} aria-hidden="true" />
              </span>
              Quiz editor
            </div>

            <h1>{quiz.title}</h1>

            <p>
              Manage your quiz details, questions, and correct answers.
            </p>
          </div>

          <Button
            type="button"
            variant="secondary"
            onClick={() => navigate(`/quizzes/${quiz.id}/take`)}
          >
            <Play size={17} strokeWidth={2} aria-hidden="true" />
            Preview quiz
          </Button>
        </header>

        <section className="edit-quiz-page__meta" aria-label="Quiz information">
          <div className="edit-quiz-page__meta-item">
            <span className="edit-quiz-page__meta-icon">
              <FileQuestion size={18} strokeWidth={2} aria-hidden="true" />
            </span>

            <div>
              <strong>{questionCount}</strong>
              <span>{questionCount === 1 ? "Question" : "Questions"}</span>
            </div>
          </div>

          <div className="edit-quiz-page__meta-divider" />

          <div className="edit-quiz-page__meta-item">
            <span className="edit-quiz-page__meta-icon">
              <Clock3 size={18} strokeWidth={2} aria-hidden="true" />
            </span>

            <div>
              <strong>{formattedUpdatedAt}</strong>
              <span>Last updated</span>
            </div>
          </div>
        </section>

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

        <Card className="edit-quiz-details">
          <div className="edit-quiz-details__header">
            <div>
              <h2>Quiz details</h2>
              <p>Update the title and description shown to participants.</p>
            </div>
          </div>

          <form className="edit-quiz-details__form" onSubmit={handleSubmit}>
            <Input
              id="edit-title"
              label="Quiz title"
              type="text"
              maxLength={255}
              value={form.title}
              onChange={(event) => {
                setForm((current) => ({
                  ...current,
                  title: event.target.value,
                }));
                setError("");
                setSuccessMessage("");
              }}
            />

            <div className="edit-quiz-details__field">
              <div className="edit-quiz-details__label-row">
                <label htmlFor="edit-description">Description</label>
                <span>Optional</span>
              </div>

              <textarea
                id="edit-description"
                maxLength={1000}
                value={form.description}
                placeholder="What is this quiz about?"
                onChange={(event) => {
                  setForm((current) => ({
                    ...current,
                    description: event.target.value,
                  }));
                  setError("");
                  setSuccessMessage("");
                }}
              />

              <div className="edit-quiz-details__character-count">
                {form.description.length}/1000
              </div>
            </div>

            <div className="edit-quiz-details__actions">
              <Button type="submit" loading={isSaving}>
                <Save size={17} strokeWidth={2} aria-hidden="true" />
                Save changes
              </Button>
            </div>
          </form>
        </Card>

        <section className="questions-section">
          <div className="questions-section__header">
            <div>
              <p className="quiz-eyebrow">Questions</p>

              <h2>
                {quiz.questions.length === 1
                  ? "1 question"
                  : `${quiz.questions.length} questions`}
              </h2>
            </div>

            <Button
              type="button"
              onClick={() => {
                setIsAddingQuestion(true)
                setNewQuestionError("")
                setSuccessMessage("")
              }}
              disabled={isAddingQuestion}
            >
              <Plus size={17} strokeWidth={2} aria-hidden="true" />
              Add a question
            </Button>
          </div>

          <div
            className="question-list"
            onScroll={handleQuestionListScroll}
          >
            {quiz.questions.length === 0 && !isAddingQuestion && (
              <p className="empty-questions">
                This quiz doesn't have any questions yet.
              </p>
            )}

            {visibleQuestions.map((question) => {
              const isEditing = editingQuestionId === question.id;

              return (
                <article className="question-card" key={question.id}>
                  <div className="question-card-heading">
                    <span>Question {question.position}</span>
                    <span>
                      {question.question_type.replaceAll("_", " ")}
                    </span>
                  </div>

                  {isEditing ? (
                    <div className="question-editor">
                      {questionError && (
                        <div className="form-message form-error" role="alert">
                          {questionError}
                        </div>
                      )}

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
                            setQuestionError("")
                          }}
                        />

                        {question.question_type === "math_work" && (
                          <div className="question-editor__expected-answer">
                            <label htmlFor={`expected-answer-${question.id}`}>
                              Expected answer
                            </label>

                            <input
                              id={`expected-answer-${question.id}`}
                              type="text"
                              value={editingExpectedAnswer}
                              maxLength={1000}
                              placeholder="e.g. 42, x + 5, 3/4"
                              onChange={(event) => {
                                setEditingExpectedAnswer(event.target.value);
                                setQuestionError("");
                              }}
                            />

                            <span className="question-editor__field-help">
                              Enter the answer students should reach after showing their work.
                            </span>
                          </div>
                        )}

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
                                aria-label={`Mark answer ${index + 1
                                  } as correct`}
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
                      <p className="question-text">{question.text}</p>

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
                          onClick={() =>
                            startEditingQuestion(question)
                          }
                          disabled={
                            deletingQuestionId === question.id
                          }
                        >
                          Edit
                        </button>

                        <button
                          type="button"
                          className="delete-question-button"
                          onClick={() =>
                            void deleteQuestion(question)
                          }
                          disabled={
                            deletingQuestionId === question.id
                          }
                        >
                          {deletingQuestionId === question.id
                            ? "Deleting..."
                            : "Delete"}
                        </button>
                      </div>
                    </>
                  )}
                </article>
              );
            })}
            {isAddingQuestion && (
              <div ref={newQuestionCardRef}>
                <Card className="new-question-card">
                  <div className="new-question-card__header">
                    <div>
                      <div className="new-question-card__eyebrow">
                        <Plus size={15} strokeWidth={2.2} aria-hidden="true" />
                        New question
                      </div>

                      <h3>Add a question</h3>

                      <p>
                        Choose a question type and enter the question details.
                      </p>
                    </div>

                    <button
                      type="button"
                      className="new-question-card__close"
                      onClick={resetNewQuestion}
                      aria-label="Cancel adding question"
                      disabled={isCreatingQuestion}
                    >
                      <X size={19} strokeWidth={2} aria-hidden="true" />
                    </button>
                  </div>

                  {newQuestionError && (
                    <div className="form-message form-error" role="alert">
                      {newQuestionError}
                    </div>
                  )}

                  <div className="new-question-type">
                    <p className="new-question-type__label">
                      Question type
                    </p>

                    <div className="new-question-type__options">
                      <button
                        type="button"
                        className={`new-question-type__option ${newQuestionType === "multiple_choice"
                          ? "new-question-type__option--active"
                          : ""
                          }`}
                        onClick={() => setNewQuestionType("multiple_choice")}
                      >
                        <ListChecks size={19} strokeWidth={2} aria-hidden="true" />

                        <span>
                          <strong>Multiple choice</strong>
                          <small>Choose one correct answer</small>
                        </span>

                        {newQuestionType === "multiple_choice" && (
                          <Check
                            className="new-question-type__check"
                            size={17}
                            strokeWidth={2.4}
                            aria-hidden="true"
                          />
                        )}
                      </button>

                      <button
                        type="button"
                        className={`new-question-type__option ${newQuestionType === "written_answer"
                          ? "new-question-type__option--active"
                          : ""
                          }`}
                        onClick={() => setNewQuestionType("written_answer")}
                      >
                        <PenLine size={19} strokeWidth={2} aria-hidden="true" />

                        <span>
                          <strong>Written answer</strong>
                          <small>Student writes a response</small>
                        </span>

                        {newQuestionType === "written_answer" && (
                          <Check
                            className="new-question-type__check"
                            size={17}
                            strokeWidth={2.4}
                            aria-hidden="true"
                          />
                        )}
                      </button>

                      <button
                        type="button"
                        className={`new-question-type__option ${newQuestionType === "math_work"
                          ? "new-question-type__option--active"
                          : ""
                          }`}
                        onClick={() => setNewQuestionType("math_work")}
                      >
                        <Calculator size={19} strokeWidth={2} aria-hidden="true" />

                        <span>
                          <strong>Math work</strong>
                          <small>Show work and submit an answer</small>
                        </span>

                        {newQuestionType === "math_work" && (
                          <Check
                            className="new-question-type__check"
                            size={17}
                            strokeWidth={2.4}
                            aria-hidden="true"
                          />
                        )}
                      </button>
                    </div>
                  </div>

                  <div className="new-question-field">
                    <label htmlFor="new-question-text">
                      Question
                    </label>

                    <textarea
                      id="new-question-text"
                      value={newQuestionText}
                      maxLength={2000}
                      placeholder={
                        newQuestionType === "math_work"
                          ? "e.g. Solve for x: 2x + 6 = 18"
                          : newQuestionType === "written_answer"
                            ? "e.g. Explain what a Python function does."
                            : "e.g. Which keyword defines a function in Python?"
                      }
                      onChange={(event) => {
                        setNewQuestionText(event.target.value)
                        setNewQuestionError("")
                      }}
                    />

                    <span className="new-question-field__count">
                      {newQuestionText.length}/2000
                    </span>
                  </div>

                  {newQuestionType === "multiple_choice" && (
                    <div className="new-question-choices">
                      <div className="new-question-choices__heading">
                        <div>
                          <h4>Answer choices</h4>
                          <p>Select the correct answer.</p>
                        </div>

                        <Button
                          type="button"
                          variant="secondary"
                          onClick={addNewChoice}
                        >
                          <Plus size={16} strokeWidth={2} aria-hidden="true" />
                          Add choice
                        </Button>
                      </div>

                      <div className="new-question-choices__list">
                        {newQuestionChoices.map((choice, index) => (
                          <div
                            className={`new-question-choice ${choice.is_correct
                              ? "new-question-choice--correct"
                              : ""
                              }`}
                            key={choice.id}
                          >
                            <label className="new-question-choice__correct">
                              <input
                                type="radio"
                                name="new-question-correct-answer"
                                checked={choice.is_correct}
                                onChange={() =>
                                  selectNewCorrectChoice(choice.id)
                                }
                              />

                              <span className="new-question-choice__number">
                                {index + 1}
                              </span>
                            </label>

                            <input
                              className="new-question-choice__input"
                              type="text"
                              value={choice.text}
                              maxLength={1000}
                              placeholder={`Answer choice ${index + 1}`}
                              onChange={(event) =>
                                updateNewChoiceText(
                                  choice.id,
                                  event.target.value,
                                )
                              }
                            />

                            <button
                              type="button"
                              className="new-question-choice__remove"
                              onClick={() => removeNewChoice(choice.id)}
                              disabled={newQuestionChoices.length <= 2}
                              aria-label={`Remove answer choice ${index + 1}`}
                            >
                              <Trash2
                                size={17}
                                strokeWidth={2}
                                aria-hidden="true"
                              />
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {newQuestionType === "math_work" && (
                    <div className="new-question-field">
                      <label htmlFor="new-question-expected-answer">
                        Expected answer
                      </label>

                      <input
                        id="new-question-expected-answer"
                        type="text"
                        value={newExpectedAnswer}
                        maxLength={1000}
                        placeholder="e.g. 6"
                        onChange={(event) => {
                          setNewExpectedAnswer(event.target.value)
                          setNewQuestionError("")
                        }}
                      />

                      <span className="new-question-field__help">
                        Enter the mathematical answer students should reach.
                      </span>
                    </div>
                  )}

                  {newQuestionType === "written_answer" && (
                    <div className="new-question-info">
                      <Info size={18} strokeWidth={2} aria-hidden="true" />

                      <p>
                        Written answers don't require a predefined correct answer.
                        The student will enter their response when taking the quiz.
                      </p>
                    </div>
                  )}

                  <div className="new-question-card__actions">
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={resetNewQuestion}
                      disabled={isCreatingQuestion}
                    >
                      Cancel
                    </Button>

                    <Button
                      type="button"
                      loading={isCreatingQuestion}
                      onClick={() => void createQuestion()}
                    >
                      <Plus size={17} strokeWidth={2} aria-hidden="true" />
                      Add question
                    </Button>
                  </div>
                </Card>
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}

export default EditQuizPage