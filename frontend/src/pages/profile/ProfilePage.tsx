import { useCallback, useEffect, useRef, useState } from "react"
import axios from "axios"
import { useNavigate } from "react-router-dom"
import Swal from "sweetalert2"
import {
  ArrowRight,
  CalendarDays,
  CircleUserRound,
  MoreHorizontal,
  FileQuestion,
  Grid3X3,
  Pencil,
  Plus,
  Sparkles,
  Trash2,
} from "lucide-react"

import apiClient from "../../api/client"
import { useAuth } from "../../auth/useAuth"
import QuizIcon from "../../components/quizzes/QuizIcon"
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
  icon: string
  creator_name: string
  created_at: string
  updated_at: string
}

type QuizPageResponse = {
  quizzes: Quiz[]
  total: number
  page: number
  page_size: number
  total_pages: number
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
  const { user } = useAuth()

  const [quizzes, setQuizzes] = useState<Quiz[]>([])
  const [quizTotal, setQuizTotal] = useState(0)
  const [quizPage, setQuizPage] = useState(1)
  const [quizTotalPages, setQuizTotalPages] = useState(0)
  const [isLoadingQuizzes, setIsLoadingQuizzes] = useState(true)
  const [isLoadingMore, setIsLoadingMore] = useState(false)
  const [quizError, setQuizError] = useState("")
  const [openQuizMenuId, setOpenQuizMenuId] = useState<string | null>(
    null,
  )

  const loadMoreRef = useRef<HTMLDivElement | null>(null)
  const isLoadingMoreRef = useRef(false)

  useEffect(() => {
    const loadQuizzes = async () => {
      try {
        const response = await apiClient.get<QuizPageResponse>(
          "/users/me/quizzes",
          {
            params: {
              page: 1,
              page_size: 10,
            },
          },
        )

        setQuizzes(response.data.quizzes)
        setQuizTotal(response.data.total)
        setQuizPage(response.data.page)
        setQuizTotalPages(response.data.total_pages)
        setQuizError("")
      } catch {
        setQuizError("Unable to load your quizzes.")
      } finally {
        setIsLoadingQuizzes(false)
      }
    }

    void loadQuizzes()
  }, [])


  const loadMoreQuizzes = useCallback(async () => {
    if (
      isLoadingMoreRef.current ||
      quizPage >= quizTotalPages
    ) {
      return
    }

    isLoadingMoreRef.current = true
    setIsLoadingMore(true)

    try {
      const nextPage = quizPage + 1

      const response = await apiClient.get<QuizPageResponse>(
        "/users/me/quizzes",
        {
          params: {
            page: nextPage,
            page_size: 10,
          },
        },
      )

      setQuizzes((currentQuizzes) => {
        const existingIds = new Set(
          currentQuizzes.map((quiz) => quiz.id),
        )

        const newQuizzes = response.data.quizzes.filter(
          (quiz) => !existingIds.has(quiz.id),
        )

        return [
          ...currentQuizzes,
          ...newQuizzes,
        ]
      })

      setQuizTotal(response.data.total)
      setQuizPage(response.data.page)
      setQuizTotalPages(response.data.total_pages)
    } catch {
      // Keep all quizzes that have already loaded visible.
    } finally {
      isLoadingMoreRef.current = false
      setIsLoadingMore(false)
    }
  }, [quizPage, quizTotalPages])


  const handleDeleteQuiz = async (
    quizId: string,
    quizTitle: string,
  ) => {
    setOpenQuizMenuId(null)

    const result = await Swal.fire({
      title: "Delete quiz?",
      text: `"${quizTitle}" will be permanently deleted. This action cannot be undone.`,
      icon: "warning",
      showCancelButton: true,
      confirmButtonText: "Delete Quiz",
      cancelButtonText: "Cancel",
      confirmButtonColor: "#ef4444",
      reverseButtons: true,
    })

    if (!result.isConfirmed) {
      return
    }

    try {
      await apiClient.delete(`/quizzes/${quizId}`)

      setQuizzes((currentQuizzes) =>
        currentQuizzes.filter((quiz) => quiz.id !== quizId),
      )

      setQuizTotal((currentTotal) =>
        Math.max(0, currentTotal - 1),
      )

      await Swal.fire({
        title: "Quiz deleted",
        text: `"${quizTitle}" has been deleted.`,
        icon: "success",
        confirmButtonText: "Done",
      })
    } catch (error) {
      let message = "Unable to delete this quiz. Please try again."

      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail

        if (typeof detail === "string") {
          message = detail
        }
      }

      await Swal.fire({
        title: "Couldn't delete quiz",
        text: message,
        icon: "error",
        confirmButtonText: "OK",
      })
    }
  }


  useEffect(() => {
    const target = loadMoreRef.current

    if (
      !target ||
      quizPage >= quizTotalPages
    ) {
      return
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries

        if (entry.isIntersecting) {
          void loadMoreQuizzes()
        }
      },
      {
        root: null,
        rootMargin: "300px 0px",
        threshold: 0,
      },
    )

    observer.observe(target)

    return () => {
      observer.disconnect()
    }
  }, [loadMoreQuizzes, quizPage, quizTotalPages])


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


            <div className="profile-stat">
              <strong>{quizTotal}</strong>
              <span>
                {quizTotal === 1
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
                <span>{quizTotal}</span>
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
            <>
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
                      <div
                        className="profile-quiz-card__actions"
                        onClick={(event) => event.stopPropagation()}
                        onKeyDown={(event) => event.stopPropagation()}
                      >
                        <button
                          type="button"
                          className="profile-quiz-card__menu-trigger"
                          aria-label={`Actions for ${quiz.title}`}
                          aria-haspopup="menu"
                          aria-expanded={openQuizMenuId === quiz.id}
                          onClick={(event) => {
                            event.stopPropagation()
                            setOpenQuizMenuId((currentId) =>
                              currentId === quiz.id ? null : quiz.id,
                            )
                          }}
                        >
                          <MoreHorizontal size={19} aria-hidden="true" />
                        </button>

                        {openQuizMenuId === quiz.id && (
                          <div
                            className="profile-quiz-card__menu"
                            role="menu"
                            aria-label={`Quiz actions for ${quiz.title}`}
                          >
                            <button
                              type="button"
                              role="menuitem"
                              onClick={(event) => {
                                event.stopPropagation()
                                setOpenQuizMenuId(null)
                                navigate(`/quizzes/edit/${quiz.id}`)
                              }}
                            >
                              <Pencil size={15} aria-hidden="true" />
                              Edit Quiz
                            </button>

                            <button
                              type="button"
                              role="menuitem"
                              className="profile-quiz-card__menu-delete"
                              onClick={(event) => {
                                event.stopPropagation()
                                setOpenQuizMenuId(null)
                                void handleDeleteQuiz(quiz.id, quiz.title)
                              }}
                            >
                              <Trash2 size={15} aria-hidden="true" />
                              Delete Quiz
                            </button>
                          </div>
                        )}
                      </div>

                      <div className="profile-quiz-card__number">
                        {String(index + 1).padStart(2, "0")}
                      </div>

                      <div className="profile-quiz-card__icon">
                        <QuizIcon name={quiz.icon}
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

              {quizPage < quizTotalPages && (
                <div
                  ref={loadMoreRef}
                  className="profile-load-more"
                  aria-live="polite"
                >
                  {isLoadingMore && (
                    <>
                      <span
                        className="profile-load-more__spinner"
                        aria-hidden="true"
                      />

                      <span>Loading more quizzes...</span>
                    </>
                  )}
                </div>
              )}
            </>
          )}
        </section>
      </div>
    </div>
  )
}

export default ProfilePage