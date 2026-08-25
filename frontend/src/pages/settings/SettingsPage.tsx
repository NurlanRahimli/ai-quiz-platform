import { type FormEvent, useState } from "react"
import axios from "axios"
import Swal from "sweetalert2"
import {
  Check,
  KeyRound,
  Trash2,
  TriangleAlert,
  UserRound,
} from "lucide-react"

import apiClient from "../../api/client"
import { useAuth } from "../../auth/useAuth"
import "../../styles/pages/settings/SettingsPage.css"

function getApiError(error: unknown) {
  if (
    axios.isAxiosError(error) &&
    typeof error.response?.data?.detail === "string"
  ) {
    return error.response.data.detail
  }

  return "Something went wrong. Please try again."
}

export default function SettingsPage() {
  const { user, refreshUser, logout } = useAuth()

  const [displayName, setDisplayName] = useState(
    () => user?.display_name ?? "",
  )
  const [profileError, setProfileError] = useState("")
  const [profileSuccess, setProfileSuccess] = useState("")
  const [isSavingProfile, setIsSavingProfile] = useState(false)

  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [passwordError, setPasswordError] = useState("")
  const [passwordSuccess, setPasswordSuccess] = useState("")
  const [isChangingPassword, setIsChangingPassword] =
    useState(false)

  const handleProfileSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault()

    const normalizedDisplayName = displayName.trim()

    setProfileError("")
    setProfileSuccess("")

    if (normalizedDisplayName.length < 2) {
      setProfileError(
        "Display name must contain at least 2 characters.",
      )
      return
    }

    setIsSavingProfile(true)

    try {
      await apiClient.patch("/auth/me", {
        display_name: normalizedDisplayName,
      })

      await refreshUser()

      setDisplayName(normalizedDisplayName)
      setProfileSuccess("Display name updated successfully.")
    } catch (error) {
      setProfileError(getApiError(error))
    } finally {
      setIsSavingProfile(false)
    }
  }

  const handlePasswordSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault()

    setPasswordError("")
    setPasswordSuccess("")

    if (!currentPassword) {
      setPasswordError("Enter your current password.")
      return
    }

    if (newPassword.length < 8) {
      setPasswordError(
        "New password must contain at least 8 characters.",
      )
      return
    }

    if (newPassword.length > 128) {
      setPasswordError(
        "New password cannot exceed 128 characters.",
      )
      return
    }

    if (newPassword !== confirmPassword) {
      setPasswordError("New passwords do not match.")
      return
    }

    if (currentPassword === newPassword) {
      setPasswordError(
        "New password must be different from current password.",
      )
      return
    }

    setIsChangingPassword(true)

    try {
      await apiClient.patch("/auth/me/password", {
        current_password: currentPassword,
        new_password: newPassword,
      })

      setCurrentPassword("")
      setNewPassword("")
      setConfirmPassword("")
      setPasswordSuccess("Password changed successfully.")
    } catch (error) {
      setPasswordError(getApiError(error))
    } finally {
      setIsChangingPassword(false)
    }
  }

  const handleDeleteAccount = async () => {
    const result = await Swal.fire({
      title: "Delete your account?",
      text:
        "This permanently deletes your account, quizzes, attempts, " +
        "and other account data. This action cannot be undone.",
      icon: "warning",
      input: "password",
      inputLabel: "Enter your password to confirm",
      inputPlaceholder: "Current password",
      inputAttributes: {
        autocomplete: "current-password",
      },
      showCancelButton: true,
      confirmButtonText: "Delete account",
      cancelButtonText: "Cancel",
      confirmButtonColor: "#dc2626",
      reverseButtons: true,
      showLoaderOnConfirm: true,
      allowOutsideClick: () => !Swal.isLoading(),
      preConfirm: async (password) => {
        if (!password) {
          Swal.showValidationMessage(
            "Enter your current password.",
          )
          return false
        }

        try {
          await apiClient.delete("/auth/me", {
            data: {
              password,
            },
          })

          return true
        } catch (error) {
          Swal.showValidationMessage(getApiError(error))
          return false
        }
      },
    })

    if (!result.isConfirmed) {
      return
    }

    logout()

    await Swal.fire({
      title: "Account deleted",
      text: "Your QuizApp account has been permanently deleted.",
      icon: "success",
      confirmButtonText: "Continue",
    })

    window.location.replace("/login")
  }

  return (
    <div className="settings-page">
      <div className="settings-page__container">
        <header className="settings-page__heading">
          <span className="settings-page__eyebrow">
            Account
          </span>

          <h1>Settings</h1>

          <p>
            Manage your profile, security, and account.
          </p>
        </header>

        <div className="settings-page__cards">
          <section className="settings-card">
            <div className="settings-card__header">
              <div
                className="settings-card__icon"
                aria-hidden="true"
              >
                <UserRound size={20} strokeWidth={2} />
              </div>

              <div>
                <h2>Edit profile</h2>
                <p>
                  Update how your account appears across QuizApp.
                </p>
              </div>
            </div>

            <form
              className="settings-form"
              onSubmit={handleProfileSubmit}
            >
              <div className="settings-form__field">
                <label htmlFor="settings-display-name">
                  Display name
                </label>

                <input
                  id="settings-display-name"
                  type="text"
                  value={displayName}
                  minLength={2}
                  maxLength={100}
                  autoComplete="name"
                  onChange={(event) =>
                    setDisplayName(event.target.value)
                  }
                />

                <p className="settings-form__hint">
                  Display names are unique and must contain
                  at least 2 characters.
                </p>
              </div>

              {profileError && (
                <div
                  className="settings-form__message settings-form__message--error"
                  role="alert"
                >
                  {profileError}
                </div>
              )}

              {profileSuccess && (
                <div
                  className="settings-form__message settings-form__message--success"
                  role="status"
                >
                  <Check size={16} aria-hidden="true" />
                  {profileSuccess}
                </div>
              )}

              <div className="settings-form__actions">
                <button
                  type="submit"
                  className="settings-form__save"
                  disabled={isSavingProfile}
                >
                  {isSavingProfile
                    ? "Saving..."
                    : "Save changes"}
                </button>
              </div>
            </form>
          </section>

          <section className="settings-card">
            <div className="settings-card__header">
              <div
                className="settings-card__icon"
                aria-hidden="true"
              >
                <KeyRound size={20} strokeWidth={2} />
              </div>

              <div>
                <h2>Change password</h2>
                <p>
                  Keep your account secure with a strong password.
                </p>
              </div>
            </div>

            <form
              className="settings-form"
              onSubmit={handlePasswordSubmit}
            >
              <div className="settings-form__field">
                <label htmlFor="settings-current-password">
                  Current password
                </label>

                <input
                  id="settings-current-password"
                  type="password"
                  value={currentPassword}
                  autoComplete="current-password"
                  onChange={(event) =>
                    setCurrentPassword(event.target.value)
                  }
                />
              </div>

              <div className="settings-form__field">
                <label htmlFor="settings-new-password">
                  New password
                </label>

                <input
                  id="settings-new-password"
                  type="password"
                  value={newPassword}
                  minLength={8}
                  maxLength={128}
                  autoComplete="new-password"
                  onChange={(event) =>
                    setNewPassword(event.target.value)
                  }
                />

                <p className="settings-form__hint">
                  Use at least 8 characters.
                </p>
              </div>

              <div className="settings-form__field">
                <label htmlFor="settings-confirm-password">
                  Confirm new password
                </label>

                <input
                  id="settings-confirm-password"
                  type="password"
                  value={confirmPassword}
                  minLength={8}
                  maxLength={128}
                  autoComplete="new-password"
                  onChange={(event) =>
                    setConfirmPassword(event.target.value)
                  }
                />
              </div>

              {passwordError && (
                <div
                  className="settings-form__message settings-form__message--error"
                  role="alert"
                >
                  {passwordError}
                </div>
              )}

              {passwordSuccess && (
                <div
                  className="settings-form__message settings-form__message--success"
                  role="status"
                >
                  <Check size={16} aria-hidden="true" />
                  {passwordSuccess}
                </div>
              )}

              <div className="settings-form__actions">
                <button
                  type="submit"
                  className="settings-form__save"
                  disabled={isChangingPassword}
                >
                  {isChangingPassword
                    ? "Changing..."
                    : "Change password"}
                </button>
              </div>
            </form>
          </section>
        </div>

        <section className="settings-danger">
          <div className="settings-danger__content">
            <div
              className="settings-danger__icon"
              aria-hidden="true"
            >
              <TriangleAlert size={20} strokeWidth={2} />
            </div>

            <div className="settings-danger__copy">
              <h2>Danger zone</h2>
              <p>
                Permanently delete your account and all associated
                data. This action cannot be undone.
              </p>
            </div>
          </div>

          <button
            type="button"
            className="settings-danger__delete"
            onClick={() => void handleDeleteAccount()}
          >
            <Trash2 size={16} strokeWidth={2} />
            Delete account
          </button>
        </section>
      </div>
    </div>
  )
}
