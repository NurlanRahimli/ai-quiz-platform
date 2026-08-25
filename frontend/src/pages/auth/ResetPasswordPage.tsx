import { useEffect, useState } from "react"
import type { FormEvent } from "react"
import axios from "axios"
import {
  ArrowLeft,
  Eye,
  EyeOff,
  LockKeyhole,
  ShieldCheck,
} from "lucide-react"
import {
  Link,
  useLocation,
  useNavigate,
} from "react-router-dom"

import apiClient from "../../api/client"
import "../../styles/pages/auth/LoginRedesign.css"


type LocationState = {
  email?: string
  resetToken?: string
}


function ResetPasswordPage() {
  const navigate = useNavigate()
  const location = useLocation()

  const state = location.state as LocationState | null
  const resetToken = state?.resetToken ?? ""

  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] =
    useState(false)
  const [error, setError] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (!resetToken) {
      navigate("/forgot-password", { replace: true })
    }
  }, [navigate, resetToken])

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault()

    if (password.length < 8) {
      setError("Password must be at least 8 characters.")
      return
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.")
      return
    }

    setIsSubmitting(true)
    setError("")

    try {
      await apiClient.post("/auth/reset-password", {
        reset_token: resetToken,
        new_password: password,
      })

      navigate("/login", {
        replace: true,
        state: {
          passwordResetSuccess: true,
        },
      })
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail

        setError(
          typeof detail === "string"
            ? detail
            : "Unable to reset your password.",
        )
      } else {
        setError("Something went wrong. Please try again.")
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!resetToken) {
    return null
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
          <Link
            to="/"
            className="login-brand"
            aria-label="QuizApp home"
          >
            <img
              src="/quizapp-logo.svg"
              alt=""
              className="login-brand__logo"
            />

            <span className="login-brand-name">
              <span>Quiz</span>
              <strong>App</strong>
            </span>
          </Link>

          <span className="login-showcase__eyebrow">
            ✦ SECURE PASSWORD RESET
          </span>

          <div className="login-showcase__copy">
            <h1>
              Almost there.
              <span>Create your new password.</span>
            </h1>

            <p>
              Choose a new password for your QuizApp account
              and you'll be ready to get back to learning.
            </p>
          </div>

          <div className="login-benefits">
            <div className="login-benefit">
              <span className="login-benefit__icon">
                <LockKeyhole size={20} />
              </span>

              <div>
                <strong>Choose a new password</strong>
                <p>
                  Use at least 8 characters to protect your
                  account.
                </p>
              </div>
            </div>

            <div className="login-benefit">
              <span className="login-benefit__icon">
                <ShieldCheck size={20} />
              </span>

              <div>
                <strong>Secure recovery</strong>
                <p>
                  Your identity has been verified before
                  allowing your password to change.
                </p>
              </div>
            </div>
          </div>

          <div className="login-visual" aria-hidden="true">
            <div className="login-visual__quiz">
              <div className="login-visual__quiz-heading">
                <span className="login-visual__quiz-icon">
                  <LockKeyhole size={19} />
                </span>

                <div>
                  <span>Password Recovery</span>
                  <strong>Create new password</strong>
                </div>
              </div>

              <div className="login-visual__progress">
                <span />
              </div>

              <div className="login-visual__percent">
                Verified
              </div>
            </div>

            <div className="login-visual__score">
              <span>Status</span>
              <strong>Secure</strong>
              <ShieldCheck size={22} />
            </div>

            <div className="login-visual__streak">
              <span>Final step</span>
              <strong>New password</strong>
            </div>

            <div className="login-visual__platform login-visual__platform--one" />
            <div className="login-visual__platform login-visual__platform--two" />
            <div className="login-visual__platform login-visual__platform--three" />
          </div>
        </div>
      </section>

      <section className="login-form-panel">
        <div className="login-mobile-brand">
          <img src="/quizapp-logo.svg" alt="" />

          <span>
            <strong>Quiz</strong>
            <b>App</b>
          </span>
        </div>

        <div className="login-form-card">
          <div className="login-heading">
            <span className="login-heading__eyebrow">
              NEW PASSWORD
            </span>

            <h2>Reset your password</h2>

            <p>
              Enter your new password below to finish
              recovering your account.
            </p>
          </div>

          {error && (
            <div
              className="login-message login-message--error"
              role="alert"
            >
              {error}
            </div>
          )}

          <form
            className="login-form"
            onSubmit={handleSubmit}
            noValidate
          >
            <div className="login-field">
              <label htmlFor="new-password">
                New password
              </label>

              <div className="login-input">
                <LockKeyhole size={19} />

                <input
                  id="new-password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="new-password"
                  placeholder="Enter your new password"
                  value={password}
                  onChange={(event) => {
                    setPassword(event.target.value)
                    setError("")
                  }}
                  autoFocus
                />

                <button
                  className="login-password-toggle"
                  type="button"
                  onClick={() =>
                    setShowPassword((current) => !current)
                  }
                  aria-label={
                    showPassword
                      ? "Hide password"
                      : "Show password"
                  }
                >
                  {showPassword ? (
                    <EyeOff size={19} />
                  ) : (
                    <Eye size={19} />
                  )}
                </button>
              </div>
            </div>

            <div className="login-field">
              <label htmlFor="confirm-password">
                Confirm password
              </label>

              <div className="login-input">
                <LockKeyhole size={19} />

                <input
                  id="confirm-password"
                  type={
                    showConfirmPassword
                      ? "text"
                      : "password"
                  }
                  autoComplete="new-password"
                  placeholder="Confirm your new password"
                  value={confirmPassword}
                  onChange={(event) => {
                    setConfirmPassword(event.target.value)
                    setError("")
                  }}
                />

                <button
                  className="login-password-toggle"
                  type="button"
                  onClick={() =>
                    setShowConfirmPassword(
                      (current) => !current,
                    )
                  }
                  aria-label={
                    showConfirmPassword
                      ? "Hide password"
                      : "Show password"
                  }
                >
                  {showConfirmPassword ? (
                    <EyeOff size={19} />
                  ) : (
                    <Eye size={19} />
                  )}
                </button>
              </div>
            </div>

            <button
              className="login-submit"
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting
                ? "Resetting password..."
                : "Reset password"}

              {!isSubmitting && <span>→</span>}
            </button>
          </form>

          <p className="login-switch">
            <Link to="/login">
              <ArrowLeft size={14} />
              Back to login
            </Link>
          </p>
        </div>

        <div className="login-security">
          <ShieldCheck size={16} />
          <span>Your account recovery is secure</span>
        </div>
      </section>
    </main>
  )
}


export default ResetPasswordPage
