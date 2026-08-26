import { useState } from "react"
import type { FormEvent } from "react"
import axios from "axios"
import { Link, useNavigate } from "react-router-dom"
import { useAuth } from "../../auth/useAuth"

import apiClient from "../../api/client"
import {
  BarChart3,
  BrainCircuit,
  Eye,
  EyeOff,
  FlaskConical,
  LockKeyhole,
  Mail,
  PencilLine,
  ShieldCheck,
  TrendingUp,
} from "lucide-react"
import "../../styles/pages/auth/LoginRedesign.css"

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
  const [showPassword, setShowPassword] = useState(false)

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
    <main className="login-page">
      <section className="login-showcase">
        <div className="login-showcase__glow login-showcase__glow--one" />
        <div className="login-showcase__glow login-showcase__glow--two" />

        <div className="login-particle login-particle--one" />
        <div className="login-particle login-particle--two" />
        <div className="login-particle login-particle--three" />

        <div className="login-showcase__content">
          <button type="button" className="login-brand" onClick={() => navigate("/")}>
            <img
              src="/quizapp-logo.svg"
              alt=""
              className="login-brand__logo"
            />

            <span className="login-brand-name">
              <span>Quiz</span>
              <strong>App</strong>
            </span>
          </button>

          <span className="login-showcase__eyebrow">
            ✦ Smarter Quizzes. Better Learning.
          </span>

          <div className="login-showcase__copy">
            <h1>
              Master what matters.
              <span>One quiz at a time.</span>
            </h1>

            <p>
              Create engaging quizzes, challenge yourself, and track your
              progress with powerful analytics and AI insights.
            </p>
          </div>

          <div className="login-benefits">
            <div className="login-benefit">
              <span className="login-benefit__icon">
                <PencilLine size={20} />
              </span>
              <div>
                <strong>Create &amp; Customize</strong>
                <p>Build beautiful quizzes with multiple question types.</p>
              </div>
            </div>

            <div className="login-benefit">
              <span className="login-benefit__icon">
                <BarChart3 size={20} />
              </span>
              <div>
                <strong>Track Progress</strong>
                <p>Detailed analytics to help you improve every day.</p>
              </div>
            </div>

            <div className="login-benefit">
              <span className="login-benefit__icon">
                <BrainCircuit size={20} />
              </span>
              <div>
                <strong>AI-Powered Insights</strong>
                <p>Get personalized suggestions to learn smarter.</p>
              </div>
            </div>

            <div className="login-benefit">
              <span className="login-benefit__icon">
                <ShieldCheck size={20} />
              </span>
              <div>
                <strong>Secure &amp; Private</strong>
                <p>Your data is encrypted and always protected.</p>
              </div>
            </div>
          </div>

          <div className="login-visual" aria-hidden="true">
            <div className="login-visual__quiz">
              <div className="login-visual__quiz-heading">
                <span className="login-visual__quiz-icon">
                  <FlaskConical size={19} />
                </span>

                <div>
                  <span>Science Quiz</span>
                  <strong>8 of 10 completed</strong>
                </div>
              </div>

              <div className="login-visual__progress">
                <span />
              </div>

              <div className="login-visual__percent">85%</div>
            </div>

            <div className="login-visual__score">
              <span>Score</span>
              <strong>92%</strong>
              <TrendingUp size={22} />
            </div>

            <div className="login-visual__streak">
              <span>🔥 Streak</span>
              <strong>7 days</strong>
            </div>

            <div className="login-visual__platform login-visual__platform--one" />
            <div className="login-visual__platform login-visual__platform--two" />
            <div className="login-visual__platform login-visual__platform--three" />
          </div>
        </div>
      </section>

      <section className="login-form-panel">
        <button type="button" className="login-mobile-brand" onClick={() => navigate("/")}>
          <img src="/quizapp-logo.svg" alt="" />
          <span>
            <strong>Quiz</strong>
            <b>App</b>
          </span>
        </button>

        <div className="login-form-card">
          <div className="login-heading">
            <span className="login-heading__eyebrow">WELCOME BACK</span>
            <h2>Welcome back! 👋</h2>
            <p>Log in to continue your learning journey.</p>
          </div>

          {errors.form && (
            <div className="login-message login-message--error" role="alert">
              {errors.form}
            </div>
          )}

          <form className="login-form" onSubmit={handleSubmit} noValidate>
            <div className="login-field">
              <label htmlFor="email">Email address</label>

              <div className="login-input">
                <Mail size={19} />
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  placeholder="Enter your email"
                  value={form.email}
                  onChange={(event) =>
                    updateField("email", event.target.value)
                  }
                />
              </div>

              {errors.email && (
                <span className="login-field__error">{errors.email}</span>
              )}
            </div>

            <div className="login-field">
              <div className="login-field__header">
                <label htmlFor="password">Password</label>

                <Link
                  to="/forgot-password"
                  className="login-forgot-password"
                >
                  Forgot password?
                </Link>
              </div>

              <div className="login-input">
                <LockKeyhole size={19} />

                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  placeholder="Enter your password"
                  value={form.password}
                  onChange={(event) =>
                    updateField("password", event.target.value)
                  }
                />

                <button
                  className="login-password-toggle"
                  type="button"
                  onClick={() => setShowPassword((current) => !current)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <EyeOff size={19} />
                  ) : (
                    <Eye size={19} />
                  )}
                </button>
              </div>

              {errors.password && (
                <span className="login-field__error">{errors.password}</span>
              )}
            </div>

            <button
              className="login-submit"
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Logging in..." : "Log in"}
              {!isSubmitting && <span>→</span>}
            </button>
          </form>

          <p className="login-switch">
            Don't have an account? <Link to="/register">Sign up</Link>
          </p>
        </div>

        <div className="login-security">
          <ShieldCheck size={16} />
          <span>Your data is secure and encrypted</span>
        </div>
      </section>
    </main>
  )
}

export default LoginPage