import { useCallback, useEffect, useRef, useState } from "react"

import axios from "axios"

import { useNavigate, useParams } from "react-router-dom"

import {
    ArrowLeft,
    ArrowRight,
    CalendarDays,
    CircleUserRound,
    FileQuestion,
    Grid3X3,
    Sparkles,
    Users,
} from "lucide-react"

import apiClient from "../../api/client"

import "../../styles/pages/profile/PublicProfilePage.css"

type PublicQuiz = {
    id: string
    owner_id: string
    title: string
    description: string | null
    visibility: "public"
    category: string | null
    tags: string[]
    creator_name: string
    question_count: number
    attempt_count: number
    created_at: string
    updated_at: string
}

type PublicProfile = {
    id: string
    display_name: string
    created_at: string
    public_quiz_count: number
    quizzes: PublicQuiz[]
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

function PublicProfilePage() {
    const navigate = useNavigate()
    const { userId } = useParams()

    const [profile, setProfile] = useState<PublicProfile | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState("")
    const [isLoadingMore, setIsLoadingMore] = useState(false)
    const loadMoreRef = useRef<HTMLDivElement | null>(null)
    const isLoadingMoreRef = useRef(false)

    useEffect(() => {
        if (!userId) {
            return
        }

        const loadProfile = async () => {
            try {
                const response = await apiClient.get<PublicProfile>(
                    `/users/${userId}/profile`,
                    {
                        params: {
                            page: 1,
                            page_size: 10,
                        },
                    },
                )

                setProfile(response.data)
                setError("")
            } catch (requestError) {
                if (
                    axios.isAxiosError(requestError) &&
                    requestError.response?.status === 404
                ) {
                    setError("This creator could not be found.")
                } else {
                    setError("Unable to load this creator's profile.")
                }
            } finally {
                setIsLoading(false)
            }
        }

        void loadProfile()
    }, [userId])

    const loadMoreQuizzes = useCallback(async () => {
        if (
            !userId ||
            !profile ||
            isLoadingMoreRef.current ||
            profile.page >= profile.total_pages
        ) {
            return
        }

        isLoadingMoreRef.current = true
        setIsLoadingMore(true)

        try {
            const nextPage = profile.page + 1

            const response = await apiClient.get<PublicProfile>(
                `/users/${userId}/profile`,
                {
                    params: {
                        page: nextPage,
                        page_size: 10,
                    },
                },
            )

            setProfile((currentProfile) => {
                if (!currentProfile) {
                    return response.data
                }

                const existingIds = new Set(
                    currentProfile.quizzes.map((quiz) => quiz.id),
                )

                const newQuizzes = response.data.quizzes.filter(
                    (quiz) => !existingIds.has(quiz.id),
                )

                return {
                    ...response.data,
                    quizzes: [
                        ...currentProfile.quizzes,
                        ...newQuizzes,
                    ],
                }
            })
        } catch {
            // Keep already-loaded quizzes visible if loading
            // another page fails.
        } finally {
            isLoadingMoreRef.current = false
            setIsLoadingMore(false)
        }
    }, [userId, profile])

    useEffect(() => {
        const target = loadMoreRef.current

        if (
            !target ||
            !profile ||
            profile.page >= profile.total_pages
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
    }, [profile, loadMoreQuizzes])

    if (isLoading) {
        return (
            <div className="public-profile-page">
                <div className="public-profile-page__container">
                    <div className="public-profile-state">
                        <div
                            className="public-profile-state__icon"
                            aria-hidden="true"
                        >
                            <CircleUserRound size={30} />
                        </div>

                        <h2>Loading creator...</h2>
                        <p>Getting their public profile ready.</p>
                    </div>
                </div>
            </div>
        )
    }

    if (error || !profile) {
        return (
            <div className="public-profile-page">
                <div className="public-profile-page__container">
                    <button
                        type="button"
                        className="public-profile-back"
                        onClick={() => navigate("/discover")}
                    >
                        <ArrowLeft size={17} aria-hidden="true" />
                        Back to Discover
                    </button>

                    <div className="public-profile-state">
                        <div
                            className="public-profile-state__icon"
                            aria-hidden="true"
                        >
                            <CircleUserRound size={30} />
                        </div>

                        <h2>Creator unavailable</h2>
                        <p>{error || "This creator could not be found."}</p>
                    </div>
                </div>
            </div>
        )
    }

    const initial =
        profile.display_name.trim().charAt(0).toUpperCase() || "U"

    return (
        <div className="public-profile-page">
            <div className="public-profile-page__container">
                <button
                    type="button"
                    className="public-profile-back"
                    onClick={() => navigate(-1)}
                >
                    <ArrowLeft size={17} aria-hidden="true" />
                    Back
                </button>

                <header className="public-profile-heading">
                    <span className="public-profile-heading__eyebrow">
                        <Sparkles size={14} aria-hidden="true" />
                        Creator Profile
                    </span>

                    <h1>{profile.display_name}</h1>

                    <p>
                        Explore quizzes publicly shared by this creator.
                    </p>
                </header>

                <section className="public-profile-hero">
                    <div className="public-profile-hero__identity">
                        <div
                            className="public-profile-avatar"
                            aria-hidden="true"
                        >
                            <span>{initial}</span>
                        </div>

                        <div className="public-profile-identity">
                            <div className="public-profile-identity__name">
                                <h2>{profile.display_name}</h2>

                                <span className="public-profile-identity__badge">
                                    <Sparkles size={13} aria-hidden="true" />
                                    Creator
                                </span>
                            </div>

                            <div className="public-profile-identity__joined">
                                <CalendarDays size={15} aria-hidden="true" />
                                Member since {formatMemberDate(profile.created_at)}
                            </div>
                        </div>
                    </div>

                    <div className="public-profile-stat">
                        <strong>{profile.public_quiz_count}</strong>
                        <span>
                            {profile.public_quiz_count === 1
                                ? "Public Quiz"
                                : "Public Quizzes"}
                        </span>
                    </div>
                </section>

                <section className="public-profile-quizzes">
                    <div className="public-profile-quizzes__header">
                        <div className="public-profile-quizzes__title">
                            <Grid3X3 size={18} aria-hidden="true" />

                            <h2>Public Quizzes</h2>

                            <span>{profile.public_quiz_count}</span>
                        </div>
                    </div>

                    {profile.quizzes.length === 0 ? (
                        <div className="public-profile-state">
                            <div
                                className="public-profile-state__icon"
                                aria-hidden="true"
                            >
                                <FileQuestion size={27} />
                            </div>

                            <h3>No public quizzes yet</h3>

                            <p>
                                {profile.display_name} hasn't published any quizzes yet.
                            </p>
                        </div>
                    ) : (
                        <>
                            <div className="public-profile-quiz-grid">
                                {profile.quizzes.map((quiz, index) => (
                                    <article
                                        key={quiz.id}
                                        className="public-profile-quiz-card"
                                        role="button"
                                        tabIndex={0}
                                        onClick={() => navigate(`/quizzes/${quiz.id}`)}
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
                                        <div className="public-profile-quiz-card__visual">
                                            <div className="public-profile-quiz-card__number">
                                                {String(index + 1).padStart(2, "0")}
                                            </div>

                                            <div className="public-profile-quiz-card__icon">
                                                <FileQuestion
                                                    size={23}
                                                    aria-hidden="true"
                                                />
                                            </div>
                                        </div>

                                        <div className="public-profile-quiz-card__body">
                                            {quiz.category && (
                                                <span className="public-profile-quiz-card__category">
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
                                                    className="public-profile-quiz-card__tags"
                                                    aria-label="Quiz tags"
                                                >
                                                    {quiz.tags.map((tag) => (
                                                        <span
                                                            key={tag}
                                                            className="public-profile-quiz-card__tag"
                                                        >
                                                            #{tag}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}

                                            <div className="public-profile-quiz-card__stats">
                                                <span>
                                                    <FileQuestion size={14} aria-hidden="true" />

                                                    {quiz.question_count}{" "}
                                                    {quiz.question_count === 1
                                                        ? "question"
                                                        : "questions"}
                                                </span>

                                                <span>
                                                    <Users size={14} aria-hidden="true" />

                                                    {quiz.attempt_count}{" "}
                                                    {quiz.attempt_count === 1
                                                        ? "attempt"
                                                        : "attempts"}
                                                </span>
                                            </div>

                                            <div className="public-profile-quiz-card__footer">
                                                <span>
                                                    Updated {formatQuizDate(quiz.updated_at)}
                                                </span>

                                                <span
                                                    className="public-profile-quiz-card__open"
                                                    aria-hidden="true"
                                                >
                                                    <ArrowRight size={16} />
                                                </span>
                                            </div>
                                        </div>
                                    </article>
                                ))}
                            </div>

                            {profile.page < profile.total_pages && (
                                <div
                                    ref={loadMoreRef}
                                    className="public-profile-load-more"
                                    aria-live="polite"
                                >
                                    {isLoadingMore && (
                                        <>
                                            <span
                                                className="public-profile-load-more__spinner"
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

export default PublicProfilePage