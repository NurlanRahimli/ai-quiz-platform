import { useEffect, useState } from "react"
import axios from "axios"
import { useNavigate } from "react-router-dom"
import Swal from "sweetalert2"
import {
  ArrowRight,
  CalendarDays,
  CircleUserRound,
  FileQuestion,
  Grid3X3,
  Pencil,
  Plus,
  Sparkles,
} from "lucide-react"

import apiClient from "../../api/client"
import { useAuth } from "../../auth/useAuth"
import Button from "../../components/ui/Button"

import "../../styles/pages/profile/ProfilePage.css"

type Quiz = {
  id: string
  owner_id: string
  title: string
  description: string | null
  visibility: "public" | "unlisted";
  category: string | null
  tags: string[]
  creator_name: string
  created_at: string
  updated_at: string
}

function formatMemberDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    month: "long",
    year: "numeric",
  }).format(new Date(value))
}

function formatQuizDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value))
}

function ProfilePage() {
  const navigate = useNavigate()
  const { user, refreshUser } = useAuth()

  const [quizzes, setQuizzes] = useState<Quiz[]>([])
  const [isLoadingQuizzes, setIsLoadingQuizzes] = useState(true)
  const [quizError, setQuizError] = useState("")

  useEffect(() => {
    const loadQuizzes = async () => {
      try {
        const response = await apiClient.get<Quiz[]>("/quizzes")
        setQuizzes(response.data)
      } catch {
        setQuizError("Unable to load your quizzes.")
      } finally {
        setIsLoadingQuizzes(false)
      }
    }

    void loadQuizzes()
  }, [])

  const handleEditProfile = async () => {
    if (!user) {
      return
    }

    const result = await Swal.fire({
      title: "Edit profile",
      html: `
        <div class="profile-edit-modal">
          <label for="profile-display-name">
            Display name
          </label>
          <input
            id="profile-display-name"
            class="swal2-input profile-edit-modal__input"
            value="${user.display_name.replace(/"/g, "&quot;")}"
            maxlength="100"
            autocomplete="name"
          />

          <div class="profile-edit-modal__email">
            <span>Email</span>
            <strong>${user.email}</strong>
            <small>Email changes aren't supported yet.</small>
          </div>
        </div>
      `,
      showCancelButton: true,
      confirmButtonText: "Save changes",
      cancelButtonText: "Cancel",
      focusConfirm: false,
      preConfirm: () => {
        const input = document.getElementById(
          "profile-display-name",
        ) as HTMLInputElement | null

        const displayName = input?.value.trim() ?? ""

        if (displayName.length < 2) {
          Swal.showValidationMessage(
            "Display name must contain at least 2 characters.",
          )
          return false
        }

        return displayName
      },
    })

    if (!result.isConfirmed || !result.value) {
      return
    }

    try {
      await apiClient.patch("/auth/me", {
        display_name: result.value,
      })

      await refreshUser()

      await Swal.fire({
        icon: "success",
        title: "Profile updated",
        text: "Your display name has been updated.",
        timer: 1600,
        showConfirmButton: false,
      })
    } catch (requestError) {
      let message = "Unable to update your profile."

      if (axios.isAxiosError(requestError)) {
        const detail = requestError.response?.data?.detail

        if (typeof detail === "string") {
          message = detail
        }
      }

      await Swal.fire({
        icon: "error",
        title: "Update failed",
        text: message,
      })
    }
  }

  if (!user) {
    return null
  }

  const initial =
    user.display_name.trim().charAt(0).toUpperCase() || "U"

  return (
    <div className="profile-page">
      <div className="profile-page__container">
        <header className="profile-page__heading">
          <div>
            <span className="profile-page__eyebrow">
              Your account
            </span>
            <h1>Profile</h1>
            <p>
              Manage your profile and everything you've created.
            </p>
          </div>
        </header>

        <section className="profile-hero">
          <div className="profile-hero__identity">
            <div className="profile-avatar" aria-hidden="true">
              <span>{initial}</span>
            </div>

            <div className="profile-identity">
              <div className="profile-identity__name-row">
                <h2>{user.display_name}</h2>

                <span className="profile-identity__badge">
                  <Sparkles size={13} aria-hidden="true" />
                  Creator
                </span>
              </div>

              <p className="profile-identity__email">
                {user.email}
              </p>

              <div className="profile-identity__joined">
                <CalendarDays size={15} aria-hidden="true" />
                Member since {formatMemberDate(user.created_at)}
              </div>
            </div>
          </div>

          <div className="profile-hero__side">
            <Button
              variant="secondary"
              onClick={() => void handleEditProfile()}
            >
              <Pencil size={16} aria-hidden="true" />
              Edit Profile
            </Button>

            <div className="profile-stat">
              <strong>{quizzes.length}</strong>
              <span>
                {quizzes.length === 1
                  ? "Quiz Created"
                  : "Quizzes Created"}
              </span>
            </div>
          </div>
        </section>

        <section className="profile-quizzes">
          <div className="profile-quizzes__header">
            <div className="profile-quizzes__title">
              <Grid3X3 size={18} aria-hidden="true" />
              <h2>My Quizzes</h2>
              {!isLoadingQuizzes && (
                <span>{quizzes.length}</span>
              )}
            </div>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate("/quizzes/new")}
            >
              <Plus size={16} aria-hidden="true" />
              New Quiz
            </Button>
          </div>

          {isLoadingQuizzes ? (
            <div className="profile-quizzes__state">
              <div
                className="profile-quizzes__state-icon"
                aria-hidden="true"
              >
                <FileQuestion size={26} />
              </div>

              <h3>Loading your quizzes...</h3>
              <p>Getting your creations ready.</p>
            </div>
          ) : quizError ? (
            <div className="profile-quizzes__state">
              <div
                className="profile-quizzes__state-icon"
                aria-hidden="true"
              >
                <FileQuestion size={26} />
              </div>

              <h3>Couldn't load your quizzes</h3>
              <p>{quizError}</p>
            </div>
          ) : quizzes.length === 0 ? (
            <div className="profile-quizzes__state">
              <div
                className="profile-quizzes__state-icon"
                aria-hidden="true"
              >
                <FileQuestion size={26} />
              </div>

              <h3>No quizzes yet</h3>
              <p>
                Create your first quiz and it'll appear here.
              </p>

              <Button onClick={() => navigate("/quizzes/new")}>
                <Plus size={17} aria-hidden="true" />
                Create Quiz
              </Button>
            </div>
          ) : (
            <div className="profile-quiz-grid">
              {quizzes.map((quiz, index) => (
                <article
                  key={quiz.id}
                  className="profile-quiz-card"
                  role="button"
                  tabIndex={0}
                  onClick={() =>
                    navigate(`/quizzes/${quiz.id}`)
                  }
                  onKeyDown={(event) => {
                    if (
                      event.key === "Enter" ||
                      event.key === " "
                    ) {
                      event.preventDefault()
                      navigate(`/quizzes/${quiz.id}`)
                    }
                  }}
                >
                  <div className="profile-quiz-card__visual">
                    <div className="profile-quiz-card__number">
                      {String(index + 1).padStart(2, "0")}
                    </div>

                    <div className="profile-quiz-card__icon">
                      <FileQuestion
                        size={23}
                        aria-hidden="true"
                      />
                    </div>

                    <span
                      className={`profile-quiz-card__visibility profile-quiz-card__visibility--${quiz.visibility}`}
                    >
                      {quiz.visibility === "public" ? "Public" : "Unlisted"}
                    </span>
                  </div>

                  <div className="profile-quiz-card__body">
                    {quiz.category && (
                      <span className="profile-quiz-card__category">
                        {quiz.category}
                      </span>
                    )}

                    <h3>{quiz.title}</h3>

                    <p>
                      {quiz.description ||
                        "No description has been added yet."}
                    </p>

                    {quiz.tags.length > 0 && (
                      <div
                        className="profile-quiz-card__tags"
                        aria-label="Quiz tags"
                      >
                        {quiz.tags.map((tag) => (
                          <span
                            key={tag}
                            className="profile-quiz-card__tag"
                          >
                            #{tag}
                          </span>
                        ))}
                      </div>
                    )}

                    <div className="profile-quiz-card__creator">
                      <CircleUserRound
                        size={15}
                        strokeWidth={2}
                        aria-hidden="true"
                      />
                      <span>By {quiz.creator_name}</span>
                    </div>

                    <div className="profile-quiz-card__footer">
                      <span>
                        Updated {formatQuizDate(quiz.updated_at)}
                      </span>

                      <span
                        className="profile-quiz-card__open"
                        aria-hidden="true"
                      >
                        <ArrowRight size={16} />
                      </span>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

export default ProfilePage