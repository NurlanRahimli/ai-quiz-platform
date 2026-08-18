import { useState } from "react"
import type { FormEvent } from "react"
import axios from "axios"
import { useNavigate } from "react-router-dom"

import apiClient from "../../api/client"
import "./CreateQuizPage.css"

type QuizForm = {
  title: string
  description: string
}

type QuizErrors = Partial<Record<keyof QuizForm | "form", string>>

type QuizResponse = {
  id: string
  owner_id: string
  title: string
  description: string | null
  created_at: string
  updated_at: string
}

function CreateQuizPage() {
  const navigate = useNavigate()

  const [form, setForm] = useState<QuizForm>({
    title: "",
    description: "",
  })
  const [errors, setErrors] = useState<QuizErrors>({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  const updateField = (field: keyof QuizForm, value: string) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }))

    setErrors((current) => ({
      ...current,
      [field]: undefined,
      form: undefined,
    }))
  }

  const validateForm = () => {
    const nextErrors: QuizErrors = {}

    if (!form.title.trim()) {
      nextErrors.title = "Quiz title is required"
    }

    if (form.title.trim().length > 255) {
      nextErrors.title = "Quiz title must be 255 characters or fewer"
    }

    if (form.description.length > 1000) {
      nextErrors.description =
        "Description must be 1000 characters or fewer"
    }

    setErrors(nextErrors)

    return Object.keys(nextErrors).length === 0
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (!validateForm()) {
      return
    }

    setIsSubmitting(true)

    try {
      const response = await apiClient.post<QuizResponse>("/quizzes", {
        title: form.title.trim(),
        description: form.description.trim() || null,
      })

      navigate(`/quizzes/${response.data.id}`, {
        replace: true,
      })
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail

        setErrors((current) => ({
          ...current,
          form:
            typeof detail === "string"
              ? detail
              : "Unable to create quiz",
        }))
      } else {
        setErrors((current) => ({
          ...current,
          form: "Something went wrong. Please try again.",
        }))
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="create-quiz-page">
      <section className="create-quiz-card">
        <button
          className="back-button"
          type="button"
          onClick={() => navigate("/dashboard")}
        >
          ← Back to dashboard
        </button>

        <div className="create-quiz-heading">
          <p className="quiz-eyebrow">New quiz</p>
          <h1>Create a quiz</h1>
          <p>
            Give your quiz a name and description. You can add questions
            afterward.
          </p>
        </div>

        {errors.form && (
          <div className="form-message form-error" role="alert">
            {errors.form}
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-field">
            <label htmlFor="title">Quiz title</label>
            <input
              id="title"
              type="text"
              placeholder="e.g. Python Fundamentals"
              maxLength={255}
              value={form.title}
              onChange={(event) =>
                updateField("title", event.target.value)
              }
            />

            {errors.title && (
              <span className="field-error">{errors.title}</span>
            )}
          </div>

          <div className="form-field">
            <label htmlFor="description">
              Description <span className="optional-label">Optional</span>
            </label>

            <textarea
              id="description"
              placeholder="What is this quiz about?"
              maxLength={1000}
              value={form.description}
              onChange={(event) =>
                updateField("description", event.target.value)
              }
            />

            <div className="description-footer">
              <span className="field-error">
                {errors.description ?? ""}
              </span>

              <span className="character-count">
                {form.description.length}/1000
              </span>
            </div>
          </div>

          <div className="quiz-form-actions">
            <button
              className="secondary-button"
              type="button"
              onClick={() => navigate("/dashboard")}
              disabled={isSubmitting}
            >
              Cancel
            </button>

            <button
              className="quiz-primary-button"
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Creating..." : "Create quiz"}
            </button>
          </div>
        </form>
      </section>
    </main>
  )
}

export default CreateQuizPage