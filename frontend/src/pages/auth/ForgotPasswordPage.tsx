import { useState } from "react"
import type { FormEvent } from "react"
import axios from "axios"
import { ArrowLeft, Mail, ShieldCheck } from "lucide-react"
import { Link, useNavigate } from "react-router-dom"

import apiClient from "../../api/client"
import "../../styles/pages/auth/LoginRedesign.css"


function ForgotPasswordPage() {
  const navigate = useNavigate()

  const [email, setEmail] = useState("")
  const [error, setError] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault()

    const normalizedEmail = email.trim()

    if (!normalizedEmail) {
      setError("Email is required")
      return
    }

    setIsSubmitting(true)
    setError("")

    try {
      await apiClient.post("/auth/forgot-password", {
        email: normalizedEmail,
      })

      navigate("/verify-password-reset", {
        state: {
          email: normalizedEmail,
        },
      })
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail

        setError(
          typeof detail === "string"
            ? detail
            : "Unable to start password recovery.",
        )
      } else {
        setError(
          "Something went wrong. Please try again.",
        )
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
          <div className="login-brand">
            <img
              src="/quizapp-logo.svg"
              alt=""
              className="login-brand__logo"
            />

            <span className="login-brand-name">
              <span>Quiz</span>
              <strong>App</strong>
            </span>
          </div>

          <span className="login-showcase__eyebrow">
            ✦ Secure Account Recovery
          </span>

          <div className="login-showcase__copy">
            <h1>
              Get back to learning.
              <span>We'll help you reset.</span>
            </h1>

            <p>
              Enter the email connected to your account and
              we'll send you a secure verification code.
            </p>
          </div>

          <div className="login-benefits">
            <div className="login-benefit">
              <span className="login-benefit__icon">
                <Mail size={20} />
              </span>

              <div>
                <strong>Check Your Email</strong>
                <p>
                  We'll send a secure 6-digit password reset
                  code to your inbox.
                </p>
              </div>
            </div>

            <div className="login-benefit">
              <span className="login-benefit__icon">
                <ShieldCheck size={20} />
              </span>

              <div>
                <strong>Secure Recovery</strong>
                <p>
                  Your reset code expires shortly to help
                  protect your account.
                </p>
              </div>
            </div>
          </div>

          <div className="login-visual" aria-hidden="true">
            <div className="login-visual__quiz">
              <div className="login-visual__quiz-heading">
                <span className="login-visual__quiz-icon">
                  <ShieldCheck size={19} />
                </span>

                <div>
                  <span>Account Recovery</span>
                  <strong>Secure password reset</strong>
                </div>
              </div>

              <div className="login-visual__progress">
                <span />
              </div>

              <div className="login-visual__percent">
                Protected
              </div>
            </div>

            <div className="login-visual__score">
              <span>Security</span>
              <strong>OTP</strong>
              <ShieldCheck size={22} />
            </div>

            <div className="login-visual__streak">
              <span>Code</span>
              <strong>6 digits</strong>
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
              PASSWORD RECOVERY
            </span>

            <h2>Forgot your password?</h2>

            <p>
              No worries. Enter your email and we'll send you
              a verification code.
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
              <label htmlFor="reset-email">
                Email address
              </label>

              <div className="login-input">
                <Mail size={19} />

                <input
                  id="reset-email"
                  type="email"
                  autoComplete="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(event) => {
                    setEmail(event.target.value)
                    setError("")
                  }}
                  autoFocus
                />
              </div>
            </div>

            <button
              className="login-submit"
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting
                ? "Sending code..."
                : "Send reset code"}

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


export default ForgotPasswordPage
