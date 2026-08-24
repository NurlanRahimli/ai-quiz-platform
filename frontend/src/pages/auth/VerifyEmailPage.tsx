import { useEffect, useState } from "react"
import type { FormEvent } from "react"
import axios from "axios"
import { Link, useLocation, useNavigate } from "react-router-dom"
import {
    ArrowLeft,
    Check,
    MailCheck,
    RefreshCw,
    ShieldCheck,
} from "lucide-react"

import apiClient from "../../api/client"
import "../../styles/pages/auth/VerifyEmailPage.css"

type VerificationLocationState = {
    email?: string
}

const RESEND_COOLDOWN_SECONDS = 60

function VerifyEmailPage() {
    const navigate = useNavigate()
    const location = useLocation()

    const state = location.state as VerificationLocationState | null
    const email = state?.email ?? ""

    const [otp, setOtp] = useState("")
    const [error, setError] = useState("")
    const [resendMessage, setResendMessage] = useState("")
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [isResending, setIsResending] = useState(false)
    const [resendCooldown, setResendCooldown] = useState(
        RESEND_COOLDOWN_SECONDS,
    )

    useEffect(() => {
        if (resendCooldown <= 0) {
            return
        }

        const timer = window.setInterval(() => {
            setResendCooldown((current) => {
                if (current <= 1) {
                    window.clearInterval(timer)
                    return 0
                }

                return current - 1
            })
        }, 1000)

        return () => window.clearInterval(timer)
    }, [resendCooldown])

    const handleOtpChange = (value: string) => {
        const digitsOnly = value.replace(/\D/g, "").slice(0, 6)

        setOtp(digitsOnly)
        setError("")
    }

    const handleSubmit = async (
        event: FormEvent<HTMLFormElement>,
    ) => {
        event.preventDefault()

        if (!email) {
            setError(
                "Your verification session is missing. Please register again.",
            )
            return
        }

        if (otp.length !== 6) {
            setError("Enter the 6-digit verification code.")
            return
        }

        setIsSubmitting(true)
        setError("")
        setResendMessage("")

        try {
            await apiClient.post("/auth/verify-email", {
                email,
                otp,
            })

            navigate("/login", {
                replace: true,
                state: {
                    verified: true,
                    email,
                },
            })
        } catch (error) {
            if (axios.isAxiosError(error)) {
                const detail = error.response?.data?.detail

                setError(
                    typeof detail === "string"
                        ? detail
                        : "Unable to verify your email.",
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

    const handleResend = async () => {
        if (
            !email ||
            isResending ||
            resendCooldown > 0
        ) {
            return
        }

        setIsResending(true)
        setError("")
        setResendMessage("")

        try {
            await apiClient.post("/auth/resend-verification", {
                email,
            })

            setOtp("")
            setResendCooldown(RESEND_COOLDOWN_SECONDS)
            setResendMessage(
                "A new verification code was sent to your email.",
            )
        } catch (error) {
            if (axios.isAxiosError(error)) {
                const detail = error.response?.data?.detail

                setError(
                    typeof detail === "string"
                        ? detail
                        : "Unable to resend the verification code.",
                )
            } else {
                setError(
                    "Something went wrong. Please try again.",
                )
            }
        } finally {
            setIsResending(false)
        }
    }

    return (
        <main className="verify-email-page">
            <section className="verify-email-shell">
                <Link
                    to="/register"
                    className="verify-email-back"
                >
                    <ArrowLeft size={18} />
                    <span>Back to registration</span>
                </Link>

                <div className="verify-email-card">
                    <div className="verify-email-brand">
                        Quiz<span>App</span>
                    </div>

                    <div className="verify-email-icon">
                        <MailCheck
                            size={30}
                            strokeWidth={1.8}
                        />
                    </div>

                    <div className="verify-email-heading">
                        <span className="verify-email-eyebrow">
                            EMAIL VERIFICATION
                        </span>

                        <h1>Check your email</h1>

                        <p>
                            We sent a 6-digit verification
                            code to
                        </p>

                        <strong className="verify-email-address">
                            {email || "your email address"}
                        </strong>
                    </div>

                    <form
                        className="verify-email-form"
                        onSubmit={handleSubmit}
                        noValidate
                    >
                        <div className="verify-email-field">
                            <label htmlFor="verification-code">
                                Verification code
                            </label>

                            <div className="verify-email-input-wrap">
                                <ShieldCheck
                                    size={19}
                                    className="verify-email-input-icon"
                                />

                                <input
                                    id="verification-code"
                                    type="text"
                                    inputMode="numeric"
                                    autoComplete="one-time-code"
                                    maxLength={6}
                                    value={otp}
                                    onChange={(event) =>
                                        handleOtpChange(
                                            event.target.value,
                                        )
                                    }
                                    placeholder="000000"
                                    autoFocus
                                />
                            </div>
                        </div>

                        {error && (
                            <div
                                className="verify-email-message verify-email-message--error"
                                role="alert"
                            >
                                {error}
                            </div>
                        )}

                        {resendMessage && (
                            <div
                                className="verify-email-message verify-email-message--success"
                                role="status"
                            >
                                <Check size={17} />
                                <span>{resendMessage}</span>
                            </div>
                        )}

                        <button
                            type="submit"
                            className="verify-email-submit"
                            disabled={
                                isSubmitting ||
                                otp.length !== 6
                            }
                        >
                            {isSubmitting
                                ? "Verifying..."
                                : "Verify email"}
                        </button>
                    </form>

                    <div className="verify-email-resend">
                        <p>Didn't receive the code?</p>

                        <button
                            type="button"
                            onClick={handleResend}
                            disabled={
                                isResending ||
                                resendCooldown > 0 ||
                                !email
                            }
                        >
                            <RefreshCw
                                size={15}
                                className={
                                    isResending
                                        ? "verify-email-spin"
                                        : ""
                                }
                            />

                            {isResending
                                ? "Sending..."
                                : resendCooldown > 0
                                    ? `Resend in ${resendCooldown}s`
                                    : "Resend code"}
                        </button>
                    </div>

                    <p className="verify-email-security">
                        The code expires shortly for your
                        security.
                    </p>
                </div>
            </section>
        </main>
    )
}

export default VerifyEmailPage