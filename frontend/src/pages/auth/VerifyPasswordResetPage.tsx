import {
  useEffect,
  useRef,
  useState,
} from "react"
import type {
  ClipboardEvent,
  FormEvent,
  KeyboardEvent,
} from "react"
import axios from "axios"
import {
  ArrowLeft,
  KeyRound,
  MailCheck,
  ShieldCheck,
} from "lucide-react"
import {
  Link,
  useLocation,
  useNavigate,
} from "react-router-dom"

import apiClient from "../../api/client"
import "../../styles/pages/auth/VerifyPasswordResetPage.css"

type LocationState = {
  email?: string
}

function VerifyPasswordResetPage() {
  const navigate = useNavigate()
  const location = useLocation()

  const email =
    (location.state as LocationState | null)?.email ?? ""

  const [digits, setDigits] = useState([
    "",
    "",
    "",
    "",
    "",
    "",
  ])
  const [error, setError] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const inputRefs = useRef<Array<HTMLInputElement | null>>([])

  useEffect(() => {
    if (!email) {
      navigate("/forgot-password", { replace: true })
    }
  }, [email, navigate])

  const handleDigitChange = (
    index: number,
    value: string,
  ) => {
    const digit = value.replace(/\D/g, "").slice(-1)

    const nextDigits = [...digits]
    nextDigits[index] = digit
    setDigits(nextDigits)
    setError("")

    if (digit && index < 5) {
      inputRefs.current[index + 1]?.focus()
    }
  }

  const handleKeyDown = (
    index: number,
    event: KeyboardEvent<HTMLInputElement>,
  ) => {
    if (
      event.key === "Backspace" &&
      !digits[index] &&
      index > 0
    ) {
      inputRefs.current[index - 1]?.focus()
    }

    if (event.key === "ArrowLeft" && index > 0) {
      event.preventDefault()
      inputRefs.current[index - 1]?.focus()
    }

    if (event.key === "ArrowRight" && index < 5) {
      event.preventDefault()
      inputRefs.current[index + 1]?.focus()
    }
  }

  const handlePaste = (
    event: ClipboardEvent<HTMLInputElement>,
  ) => {
    event.preventDefault()

    const pastedDigits = event.clipboardData
      .getData("text")
      .replace(/\D/g, "")
      .slice(0, 6)

    if (!pastedDigits) {
      return
    }

    const nextDigits = Array.from({ length: 6 }, (_, index) =>
      pastedDigits[index] ?? "",
    )

    setDigits(nextDigits)
    setError("")

    const focusIndex = Math.min(pastedDigits.length, 6) - 1
    inputRefs.current[focusIndex]?.focus()
  }

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault()

    const otp = digits.join("")

    if (otp.length !== 6) {
      setError("Enter the complete 6-digit verification code.")
      return
    }

    setIsSubmitting(true)
    setError("")

    try {
      const response = await apiClient.post(
        "/auth/verify-password-reset",
        {
          email,
          otp,
        },
      )

      navigate("/reset-password", {
        replace: true,
        state: {
          email,
          resetToken: response.data.reset_token,
        },
      })
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail

        setError(
          typeof detail === "string"
            ? detail
            : "Unable to verify this code.",
        )
      } else {
        setError("Something went wrong. Please try again.")
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!email) {
    return null
  }

  return (
    <main className="reset-verify-page">
      <section className="reset-verify-showcase">
        <div className="reset-verify-glow reset-verify-glow--one" />
        <div className="reset-verify-glow reset-verify-glow--two" />

        <div className="reset-verify-showcase__content">
          <Link
            to="/"
            className="reset-verify-brand"
            aria-label="QuizApp home"
          >
            <img src="/quizapp-logo.svg" alt="" />

            <span>
              Quiz<strong>App</strong>
            </span>
          </Link>

          <span className="reset-verify-eyebrow">
            ✦ SECURE VERIFICATION
          </span>

          <div className="reset-verify-copy">
            <h1>
              One quick step.
              <span>Verify it's you.</span>
            </h1>

            <p>
              We've sent a secure 6-digit code to your email.
              Enter it to continue resetting your password.
            </p>
          </div>

          <div className="reset-verify-benefits">
            <div className="reset-verify-benefit">
              <span>
                <MailCheck size={20} />
              </span>

              <div>
                <strong>Check your inbox</strong>
                <p>
                  Your verification code was sent to the email
                  connected to your QuizApp account.
                </p>
              </div>
            </div>

            <div className="reset-verify-benefit">
              <span>
                <ShieldCheck size={20} />
              </span>

              <div>
                <strong>Protected recovery</strong>
                <p>
                  The code expires shortly to keep your account
                  recovery secure.
                </p>
              </div>
            </div>
          </div>

          <div
            className="reset-verify-visual"
            aria-hidden="true"
          >
            <div className="reset-verify-visual__card">
              <div className="reset-verify-visual__icon">
                <KeyRound size={28} />
              </div>

              <span>Verification code</span>

              <div className="reset-verify-visual__digits">
                <i />
                <i />
                <i />
                <i />
                <i />
                <i />
              </div>

              <div className="reset-verify-visual__status">
                <ShieldCheck size={16} />
                Secure verification
              </div>
            </div>

            <div className="reset-verify-orbit" />
            <span className="reset-verify-spark reset-verify-spark--one">
              ✦
            </span>
            <span className="reset-verify-spark reset-verify-spark--two">
              ✦
            </span>
          </div>
        </div>
      </section>

      <section className="reset-verify-panel">
        <div className="reset-verify-mobile-brand">
          <img src="/quizapp-logo.svg" alt="" />

          <span>
            Quiz<strong>App</strong>
          </span>
        </div>

        <div className="reset-verify-form-card">
          <div className="reset-verify-heading">
            <span>VERIFY YOUR IDENTITY</span>

            <h2>Check your email</h2>

            <p>
              Enter the 6-digit verification code we sent to
            </p>

            <strong className="reset-verify-email">
              {email}
            </strong>
          </div>

          {error && (
            <div
              className="reset-verify-error"
              role="alert"
            >
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="reset-verify-code">
              {digits.map((digit, index) => (
                <input
                  key={index}
                  ref={(element) => {
                    inputRefs.current[index] = element
                  }}
                  type="text"
                  inputMode="numeric"
                  autoComplete={
                    index === 0 ? "one-time-code" : "off"
                  }
                  maxLength={1}
                  value={digit}
                  aria-label={`Verification digit ${index + 1}`}
                  onChange={(event) =>
                    handleDigitChange(
                      index,
                      event.target.value,
                    )
                  }
                  onKeyDown={(event) =>
                    handleKeyDown(index, event)
                  }
                  onPaste={handlePaste}
                  autoFocus={index === 0}
                />
              ))}
            </div>

            <button
              type="submit"
              className="reset-verify-submit"
              disabled={isSubmitting}
            >
              {isSubmitting
                ? "Verifying..."
                : "Verify code"}

              {!isSubmitting && <span>→</span>}
            </button>
          </form>

          <p className="reset-verify-help">
            Didn't receive a code?{" "}
            <Link to="/forgot-password">
              Send another code
            </Link>
          </p>

          <Link
            to="/login"
            className="reset-verify-back"
          >
            <ArrowLeft size={15} />
            Back to login
          </Link>
        </div>

        <div className="reset-verify-security">
          <ShieldCheck size={16} />
          <span>Your account recovery is secure</span>
        </div>
      </section>
    </main>
  )
}

export default VerifyPasswordResetPage
