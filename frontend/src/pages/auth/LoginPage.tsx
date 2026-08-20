import { useState } from "react"
import type { FormEvent } from "react"
import axios from "axios"
import { Link, useNavigate } from "react-router-dom"
import { useAuth } from "../../auth/useAuth"

import apiClient from "../../api/client"
import "../../styles/pages/auth/RegisterPage.css"

type LoginForm = {
  email: string
  password: string
}

type LoginErrors = Partial<Record<keyof LoginForm | "form", string>>

type LoginResponse = {
  access_token: string
  token_type: string
}

function LoginPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState<LoginForm>({
    email: "",
    password: "",
  })

  const { login } = useAuth()
  const [errors, setErrors] = useState<LoginErrors>({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  const updateField = (field: keyof LoginForm, value: string) => {
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
    const nextErrors: LoginErrors = {}

    if (!form.email.trim()) {
      nextErrors.email = "Email is required"
    }

    if (!form.password) {
      nextErrors.password = "Password is required"
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
      const response = await apiClient.post<LoginResponse>("/auth/login", {
        email: form.email.trim(),
        password: form.password,
      })

      await login(response.data.access_token)
      navigate("/dashboard", { replace: true })
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail

        setErrors((current) => ({
          ...current,
          form:
            typeof detail === "string"
              ? detail
              : "Unable to log in",
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
          <h1>Welcome back</h1>
          <p>Log in to continue creating smarter quizzes.</p>
        </div>

        {errors.form && (
          <div className="form-message form-error" role="alert">
            {errors.form}
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-field">
            <label htmlFor="email">Email</label>

            <input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              value={form.email}
              onChange={(event) =>
                updateField("email", event.target.value)
              }
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
              autoComplete="current-password"
              placeholder="Enter your password"
              value={form.password}
              onChange={(event) =>
                updateField("password", event.target.value)
              }
            />

            {errors.password && (
              <span className="field-error">{errors.password}</span>
            )}
          </div>

          <button
            className="primary-button"
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting ? "Logging in..." : "Log in"}
          </button>
        </form>

        <p className="auth-switch">
          Don't have an account?{" "}
          <Link to="/register">Create one</Link>
        </p>
      </section>
    </main>
  )
}

export default LoginPage