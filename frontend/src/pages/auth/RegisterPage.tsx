import { useState } from "react"
import type { FormEvent } from "react"
import axios from "axios"
import { Link } from "react-router-dom"

import apiClient from "../../api/client"
import "./RegisterPage.css"

type RegisterForm = {
  displayName: string
  email: string
  password: string
  confirmPassword: string
}

type RegisterErrors = Partial<Record<keyof RegisterForm | "form", string>>

function RegisterPage() {
  const [form, setForm] = useState<RegisterForm>({
    displayName: "",
    email: "",
    password: "",
    confirmPassword: "",
  })

  const [errors, setErrors] = useState<RegisterErrors>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)

  const updateField = (field: keyof RegisterForm, value: string) => {
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
    const nextErrors: RegisterErrors = {}

    if (!form.displayName.trim()) {
      nextErrors.displayName = "Display name is required"
    }

    if (!form.email.trim()) {
      nextErrors.email = "Email is required"
    }

    if (form.password.length < 8) {
      nextErrors.password = "Password must be at least 8 characters"
    }

    if (form.password !== form.confirmPassword) {
      nextErrors.confirmPassword = "Passwords do not match"
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
    setIsSuccess(false)

    try {
      await apiClient.post("/auth/register", {
        display_name: form.displayName.trim(),
        email: form.email.trim(),
        password: form.password,
      })

      setIsSuccess(true)

      setForm({
        displayName: "",
        email: "",
        password: "",
        confirmPassword: "",
      })
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail

        setErrors((current) => ({
          ...current,
          form:
            typeof detail === "string"
              ? detail
              : "Unable to create your account",
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
    <main className="auth-page">
      <section className="auth-card">
        <div className="auth-brand">
          <div className="brand-icon">Q</div>

          <div>
            <p className="brand-name">AI Quiz</p>
            <p className="brand-subtitle">Intelligent learning platform</p>
          </div>
        </div>

        <div className="auth-heading">
          <h1>Create your account</h1>
          <p>Start creating smarter quizzes with AI.</p>
        </div>

        {errors.form && (
          <div className="form-message form-error" role="alert">
            {errors.form}
          </div>
        )}

        {isSuccess && (
          <div className="form-message form-success" role="status">
            Account created successfully. You can now log in.
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-field">
            <label htmlFor="displayName">Display name</label>

            <input
              id="displayName"
              type="text"
              autoComplete="name"
              placeholder="Your name"
              value={form.displayName}
              onChange={(event) =>
                updateField("displayName", event.target.value)
              }
            />

            {errors.displayName && (
              <span className="field-error">{errors.displayName}</span>
            )}
          </div>

          <div className="form-field">
            <label htmlFor="email">Email</label>

            <input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              value={form.email}
              onChange={(event) => updateField("email", event.target.value)}
            />

            {errors.email && (
              <span className="field-error">{errors.email}</span>
            )}
          </div>

          <div className="form-field">
            <label htmlFor="password">Password</label>

            <input
              id="password"
              type="password"
              autoComplete="new-password"
              placeholder="At least 8 characters"
              value={form.password}
              onChange={(event) =>
                updateField("password", event.target.value)
              }
            />

            {errors.password && (
              <span className="field-error">{errors.password}</span>
            )}
          </div>

          <div className="form-field">
            <label htmlFor="confirmPassword">Confirm password</label>

            <input
              id="confirmPassword"
              type="password"
              autoComplete="new-password"
              placeholder="Enter your password again"
              value={form.confirmPassword}
              onChange={(event) =>
                updateField("confirmPassword", event.target.value)
              }
            />

            {errors.confirmPassword && (
              <span className="field-error">{errors.confirmPassword}</span>
            )}
          </div>

          <button
            className="primary-button"
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting ? "Creating account..." : "Create account"}
          </button>
        </form>

        <p className="auth-switch">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </section>
    </main>
  )
}

export default RegisterPage