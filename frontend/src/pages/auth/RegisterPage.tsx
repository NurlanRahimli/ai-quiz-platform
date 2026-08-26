import { useState } from "react"
import type { FormEvent } from "react"
import axios from "axios"
import { Link, useNavigate } from "react-router-dom"
import {
  ArrowRight,
  BarChart3,
  BrainCircuit,
  Eye,
  LockKeyhole,
  Mail,
  PencilLine,
  ShieldCheck,
  Trophy,
  UserRound,
  EyeOff
} from "lucide-react"

import apiClient from "../../api/client"
import "../../styles/pages/auth/RegisterRedesign.css"

type RegisterForm = {
  displayName: string
  email: string
  password: string
  confirmPassword: string
}

type RegisterErrors = Partial<Record<keyof RegisterForm | "form", string>>

function RegisterPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState<RegisterForm>({
    displayName: "",
    email: "",
    password: "",
    confirmPassword: "",
  })

  const [errors, setErrors] = useState<RegisterErrors>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

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
    try {
      await apiClient.post("/auth/register", {
        display_name: form.displayName.trim(),
        email: form.email.trim(),
        password: form.password,
      })

      navigate("/verify-email", {
        state: {
          email: form.email.trim().toLowerCase(),
        },
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
    <main className="register-page">
      <section className="register-showcase">
        <div className="register-showcase__glow register-showcase__glow--one" />
        <div className="register-showcase__glow register-showcase__glow--two" />

        <div className="register-showcase__stars" aria-hidden="true">
          <span />
          <span />
          <span />
          <span />
          <span />
          <span />
        </div>

        <div className="register-showcase__content">
          <button type="button" className="register-brand" onClick={() => navigate("/")}>
            <img
              src="/quizapp-logo.svg"
              alt=""
              className="register-brand__logo"
            />

            <span className="register-brand-name">
              <span>Quiz</span>
              <strong>App</strong>
            </span>
          </button>

          <div className="register-showcase__badge">
            <span>✦</span>
            Smarter Quizzes. Better Learning.
          </div>

          <div className="register-showcase__copy">
            <h1>
              Learn more.
              <span className="register-title-white">
                Create more.
              </span>
              <span className="register-title-purple">
                Achieve more.
              </span>
            </h1>

            <p>
              Join a smarter way to learn, create, and grow.
              Build quizzes, explore new challenges, and turn
              every attempt into progress.
            </p>
          </div>

          <div className="register-features">
            <div className="register-feature">
              <div className="register-feature__icon">
                <PencilLine size={21} strokeWidth={1.9} />
              </div>

              <div>
                <strong>Build Your Own Quizzes</strong>
                <p>
                  Turn your ideas into interactive quizzes
                  <br />
                  in just a few simple steps.
                </p>
              </div>
            </div>

            <div className="register-feature">
              <div className="register-feature__icon">
                <BarChart3 size={21} strokeWidth={1.9} />
              </div>

              <div>
                <strong>Challenge Yourself</strong>
                <p>
                  Discover new topics and test your
                  <br />
                  knowledge as you learn.
                </p>
              </div>
            </div>

            <div className="register-feature">
              <div className="register-feature__icon">
                <BrainCircuit size={21} strokeWidth={1.9} />
              </div>

              <div>
                <strong>Learn Smarter With AI</strong>
                <p>
                  Get intelligent explanations and insights
                  <br />
                  designed to help you improve.
                </p>
              </div>
            </div>

            <div className="register-feature">
              <div className="register-feature__icon">
                <ShieldCheck size={21} strokeWidth={1.9} />
              </div>

              <div>
                <strong>Watch Yourself Improve</strong>
                <p>
                  Follow your scores and see your
                  <br />
                  progress grow over time.
                </p>
              </div>
            </div>
          </div>

          <div
            className="register-illustration"
            aria-hidden="true"
          >
            <div className="register-illustration__platform register-illustration__platform--back" />
            <div className="register-illustration__platform register-illustration__platform--front" />

            <div className="register-trophy">
              <div className="register-trophy__handle register-trophy__handle--left" />
              <div className="register-trophy__handle register-trophy__handle--right" />

              <div className="register-trophy__cup">
                <Trophy size={38} strokeWidth={1.6} />
              </div>

              <div className="register-trophy__stem" />
              <div className="register-trophy__base" />
            </div>

            <div className="register-laptop">
              <div className="register-laptop__screen">
                <div className="register-laptop__camera" />

                <div className="register-dashboard">
                  <div className="register-dashboard__header">
                    <span>Your Progress</span>
                    <small>Weekly Goal</small>
                  </div>

                  <div className="register-dashboard__content">
                    <div className="register-progress-chart">
                      <div className="register-progress-ring">
                        <span>78%</span>
                      </div>

                      <div className="register-progress-line">
                        <svg
                          viewBox="0 0 120 70"
                          preserveAspectRatio="none"
                        >
                          <polyline
                            points="0,55 20,48 38,54 58,36 76,43 95,18 120,7"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="4"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                      </div>
                    </div>

                    <div className="register-weekly-chart">
                      <strong>12 / 15</strong>
                      <span>Quizzes</span>

                      <div className="register-weekly-bars">
                        <i />
                        <i />
                        <i />
                        <i />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="register-laptop__base">
                <div className="register-laptop__keyboard">
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            </div>

            <div className="register-stat-card register-stat-card--badges">
              <span>Badges Earned</span>

              <div>
                <ShieldCheck size={24} />
                <strong>24</strong>
              </div>
            </div>

            <div className="register-stat-card register-stat-card--subject">
              <span>Top Subject</span>

              <div>
                <BrainCircuit size={22} />
                <strong>Science</strong>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="register-form-panel">
        <button type="button" className="register-mobile-brand" onClick={() => navigate("/")}>
          <img src="/quizapp-logo.svg" alt="" />

          <span className="register-mobile-brand__name">
            <span>Quiz</span>
            <strong>App</strong>
          </span>
        </button>

        <div className="register-form-card">
          <div className="register-form-container">
            <div className="register-heading">
              <span className="register-heading__eyebrow">
                GET STARTED
              </span>

              <h2>Create your account</h2>

              <p>
                Join QuizApp and start learning smarter today.
              </p>
            </div>

            {errors.form && (
              <div
                className="register-message register-message--error"
                role="alert"
              >
                {errors.form}
              </div>
            )}

            <form
              className="register-form"
              onSubmit={handleSubmit}
              noValidate
            >
              <div className="register-field">
                <label htmlFor="displayName">
                  Display name
                </label>

                <div className="register-input-wrap">
                  <UserRound
                    className="register-input-icon"
                    size={20}
                    strokeWidth={1.8}
                  />

                  <input
                    id="displayName"
                    type="text"
                    autoComplete="name"
                    placeholder="Enter your name"
                    value={form.displayName}
                    onChange={(event) =>
                      updateField(
                        "displayName",
                        event.target.value,
                      )
                    }
                  />
                </div>

                {errors.displayName && (
                  <span className="register-field__error">
                    {errors.displayName}
                  </span>
                )}
              </div>

              <div className="register-field">
                <label htmlFor="email">
                  Email address
                </label>

                <div className="register-input-wrap">
                  <Mail
                    className="register-input-icon"
                    size={20}
                    strokeWidth={1.8}
                  />

                  <input
                    id="email"
                    type="email"
                    autoComplete="email"
                    placeholder="you@example.com"
                    value={form.email}
                    onChange={(event) =>
                      updateField(
                        "email",
                        event.target.value,
                      )
                    }
                  />
                </div>

                {errors.email && (
                  <span className="register-field__error">
                    {errors.email}
                  </span>
                )}
              </div>

              <div className="register-field">
                <label htmlFor="password">
                  Password
                </label>

                <div className="register-input-wrap">
                  <LockKeyhole
                    className="register-input-icon"
                    size={20}
                    strokeWidth={1.8}
                  />

                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="new-password"
                    placeholder="At least 8 characters"
                    value={form.password}
                    onChange={(event) =>
                      updateField("password", event.target.value)
                    }
                  />

                  <button
                    type="button"
                    className="register-password-toggle"
                    onClick={() =>
                      setShowPassword((current) => !current)
                    }
                    aria-label={
                      showPassword ? "Hide password" : "Show password"
                    }
                    aria-pressed={showPassword}
                  >
                    {showPassword ? (
                      <EyeOff size={20} strokeWidth={1.8} />
                    ) : (
                      <Eye size={20} strokeWidth={1.8} />
                    )}
                  </button>
                </div>

                {errors.password && (
                  <span className="register-field__error">
                    {errors.password}
                  </span>
                )}
              </div>

              <div className="register-field">
                <label htmlFor="confirmPassword">
                  Confirm password
                </label>

                <div className="register-input-wrap">
                  <LockKeyhole
                    className="register-input-icon"
                    size={20}
                    strokeWidth={1.8}
                  />

                  <input
                    id="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    autoComplete="new-password"
                    placeholder="Confirm your password"
                    value={form.confirmPassword}
                    onChange={(event) =>
                      updateField("confirmPassword", event.target.value)
                    }
                  />

                  <button
                    type="button"
                    className="register-password-toggle"
                    onClick={() =>
                      setShowConfirmPassword((current) => !current)
                    }
                    aria-label={
                      showConfirmPassword
                        ? "Hide confirm password"
                        : "Show confirm password"
                    }
                    aria-pressed={showConfirmPassword}
                  >
                    {showConfirmPassword ? (
                      <EyeOff size={20} strokeWidth={1.8} />
                    ) : (
                      <Eye size={20} strokeWidth={1.8} />
                    )}
                  </button>
                </div>

                {errors.confirmPassword && (
                  <span className="register-field__error">
                    {errors.confirmPassword}
                  </span>
                )}
              </div>

              <button
                className="register-submit"
                type="submit"
                disabled={isSubmitting}
              >
                <span>
                  {isSubmitting
                    ? "Creating account..."
                    : "Create account"}
                </span>

                {!isSubmitting && (
                  <ArrowRight
                    size={22}
                    strokeWidth={1.8}
                  />
                )}
              </button>
            </form>

            <p className="register-login">
              Already have an account?{" "}
              <Link to="/login">
                Log in
              </Link>
            </p>

            <div className="register-secure">
              <ShieldCheck
                size={18}
                strokeWidth={1.9}
              />

              <span>
                Your data is secure and encrypted
              </span>
            </div>
          </div>
        </div>
      </section>
    </main>
  )
}

export default RegisterPage