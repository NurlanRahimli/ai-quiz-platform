import {
    useEffect,
    useState,
    useRef,
} from "react";
import { useNavigate } from "react-router-dom";

import axios from "axios";
import apiClient from "../../api/client";

import {
    Search,
} from "lucide-react";

import "../../styles/pages/attempts/MyAttemptsPage.css";

type UserAttemptQuiz = {
    quiz_id: string;
    quiz_title: string;
    quiz_category: string | null;
    latest_submitted_at: string;
    average_score: number | null;
    attempt_count: number;
    latest_score: number;
    latest_gradable_questions: number;
    latest_total_questions: number;
};

type UserAttemptPage = {
    quizzes: UserAttemptQuiz[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
};


export default function MyAttemptsPage() {
    const navigate = useNavigate();
    const [search, setSearch] = useState("");
    const [category, setCategory] = useState("");
    const [scoreRange, setScoreRange] = useState("");
    const [dateFrom, setDateFrom] = useState("");
    const [dateTo, setDateTo] = useState("");
    const [page, setPage] = useState(1);

    const [quizzes, setQuizzes] = useState<UserAttemptQuiz[]>([]);
    const [total, setTotal] = useState(0);
    const [isLoadingMore, setIsLoadingMore] = useState(false);
    const [totalPages, setTotalPages] = useState(0);

    const loadMoreRef = useRef<HTMLDivElement | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        let isCancelled = false;

        const loadAttempts = async () => {
            if (page > 1) {
                setIsLoadingMore(true);
            }
            try {
                const response = await apiClient.get<UserAttemptPage>(
                    "/attempts",
                    {
                        params: {
                            page,
                            page_size: 10,
                            search: search.trim() || undefined,
                            category: category || undefined,
                            score_range: scoreRange || undefined,
                            date_from: dateFrom || undefined,
                            date_to: dateTo || undefined,
                        },
                    },
                );

                if (isCancelled) {
                    return;
                }

                setQuizzes((current) =>
                    page === 1
                        ? response.data.quizzes
                        : [...current, ...response.data.quizzes],
                );

                setTotal(response.data.total);
                setTotalPages(response.data.total_pages);
                setError("");
            } catch (requestError) {
                if (isCancelled) {
                    return;
                }

                if (axios.isAxiosError(requestError)) {
                    setError("Unable to load your attempts.");
                } else {
                    setError("Something went wrong.");
                }

                if (page === 1) {
                    setQuizzes([]);
                    setTotal(0);
                    setTotalPages(0);
                }

                setError("Unable to load your attempts.");
            } finally {
                if (!isCancelled) {
                    if (page === 1) {
                        setIsLoading(false);
                    } else {
                        setIsLoadingMore(false);
                    }
                }
            }
        };

        void loadAttempts();

        return () => {
            isCancelled = true;
        };
    }, [
        page,
        search,
        category,
        scoreRange,
        dateFrom,
        dateTo,
    ]);


    useEffect(() => {
        const target = loadMoreRef.current;

        if (
            !target ||
            isLoading ||
            isLoadingMore ||
            page >= totalPages
        ) {
            return;
        }

        const observer = new IntersectionObserver(
            (entries) => {
                const firstEntry = entries[0];

                if (firstEntry?.isIntersecting) {
                    setPage((current) => current + 1);
                }
            },
            {
                rootMargin: "200px 0px",
            },
        );

        observer.observe(target);

        return () => {
            observer.disconnect();
        };
    }, [
        isLoading,
        isLoadingMore,
        page,
        totalPages,
    ]);


    return (
        <main className="my-attempts-page">
            <div className="my-attempts-page__container">
                <header className="my-attempts-page__header">
                    <div>
                        <h1>My Attempts</h1>
                        <p>
                            Review your quiz attempts, scores, and results.
                        </p>
                    </div>

                    
                </header>

                <section
                    className="my-attempts-filters"
                    aria-label="Attempt filters"
                >
                    <div className="my-attempts-filters__search">
                        <Search
                            size={18}
                            strokeWidth={1.9}
                            aria-hidden="true"
                        />

                        <input
                            type="search"
                            value={search}
                            onChange={(event) => {
                                setSearch(event.target.value);
                                setPage(1);
                            }}
                            placeholder="Search quizzes..."
                            aria-label="Search attempts by quiz title"
                        />
                    </div>

                    <select
                        className="my-attempts-filters__control"
                        value={category}
                        onChange={(event) => {
                            setCategory(event.target.value);
                            setPage(1);
                        }}
                        aria-label="Filter by category"
                    >
                        <option value="">All categories</option>
                        <option value="Programming">Programming</option>
                        <option value="Mathematics">Mathematics</option>
                        <option value="Science">Science</option>
                        <option value="History">History</option>
                        <option value="Geography">Geography</option>
                        <option value="Language">Language</option>
                        <option value="Technology">Technology</option>
                        <option value="Business">Business</option>
                        <option value="General Knowledge">
                            General Knowledge
                        </option>
                    </select>

                    <select
                        className="my-attempts-filters__control"
                        value={scoreRange}
                        onChange={(event) => {
                            setScoreRange(event.target.value);
                            setPage(1);
                        }}
                        aria-label="Filter by score"
                    >
                        <option value="">All scores</option>
                        <option value="90-100">90–100%</option>
                        <option value="80-89">80–89%</option>
                        <option value="70-79">70–79%</option>
                        <option value="below-70">Below 70%</option>
                    </select>

                    <div className="my-attempts-filters__date">
                        <span>From</span>

                        <input
                            type="date"
                            value={dateFrom}
                            max={dateTo || undefined}
                            onChange={(event) => {
                                setDateFrom(event.target.value);
                                setPage(1);
                            }}
                            aria-label="Filter attempts from date"
                        />
                    </div>

                    <div className="my-attempts-filters__date">
                        <span>To</span>

                        <input
                            type="date"
                            value={dateTo}
                            min={dateFrom || undefined}
                            onChange={(event) => {
                                setDateTo(event.target.value);
                                setPage(1);
                            }}
                            aria-label="Filter attempts to date"
                        />
                    </div>

                    {(search ||
                        category ||
                        scoreRange ||
                        dateFrom ||
                        dateTo) && (
                            <button
                                type="button"
                                className="my-attempts-filters__clear"
                                onClick={() => {
                                    setSearch("");
                                    setCategory("");
                                    setScoreRange("");
                                    setDateFrom("");
                                    setDateTo("");
                                    setPage(1);
                                }}
                            >
                                Clear
                            </button>
                        )}
                </section>

                {isLoading ? (
                    <p>Loading attempts...</p>
                ) : error ? (
                    <p>{error}</p>
                ) : (
                    <section className="my-attempts-results">
                        <div className="my-attempts-results__heading">
                            <h2>Attempts</h2>

                            <span>
                                {total} {total === 1 ? "quiz" : "quizzes"}
                            </span>
                        </div>

                        {quizzes.length === 0 ? (
                            <div className="my-attempts-empty">
                                <h3>No attempts found</h3>

                                <p>
                                    {search ||
                                        category ||
                                        scoreRange ||
                                        dateFrom ||
                                        dateTo
                                        ? "Try changing or clearing your filters."
                                        : "Your completed quiz attempts will appear here."}
                                </p>
                            </div>
                        ) : (
                            <>
                                <div className="my-attempts-list">
                                    {quizzes.map((quiz, index) => {
                                        const averageScore =
                                            quiz.average_score === null
                                                ? null
                                                : Math.round(quiz.average_score);

                                        return (
                                            <button
                                                key={quiz.quiz_id}
                                                type="button"
                                                className="my-attempt-card my-attempt-card--enter"
                                                style={{
                                                    animationDelay: `${Math.min(index % 10, 9) * 35}ms`,
                                                }}
                                                onClick={() =>
                                                    navigate(
                                                        `/quizzes/${quiz.quiz_id}/history`,
                                                    )
                                                }
                                            >
                                                <div className="my-attempt-card__main">
                                                    <div className="my-attempt-card__title-row">
                                                        <h3>{quiz.quiz_title}</h3>

                                                        {quiz.quiz_category && (
                                                            <span className="my-attempt-card__category">
                                                                {quiz.quiz_category}
                                                            </span>
                                                        )}
                                                    </div>

                                                    <p className="my-attempt-card__date">
                                                        Last attempted{" "}
                                                        {new Date(
                                                            quiz.latest_submitted_at,
                                                        ).toLocaleString(undefined, {
                                                            month: "short",
                                                            day: "numeric",
                                                            year: "numeric",
                                                            hour: "numeric",
                                                            minute: "2-digit",
                                                        })}
                                                        <span
                                                            className="my-attempt-card__meta-separator"
                                                            aria-hidden="true"
                                                        >
                                                            ·
                                                        </span>
                                                        <span className="my-attempt-card__attempt-count">
                                                            {quiz.attempt_count}{" "}
                                                            {quiz.attempt_count === 1
                                                                ? "attempt"
                                                                : "attempts"}
                                                        </span>
                                                    </p>
                                                </div>

                                                <div className="my-attempt-card__score">
                                                    {averageScore === null ? (
                                                        <>
                                                            <strong>—</strong>
                                                            <span>Not graded</span>
                                                        </>
                                                    ) : (
                                                        <>
                                                            <strong>{averageScore}%</strong>
                                                            <span>Average score</span>
                                                        </>
                                                    )}
                                                </div>
                                            </button>
                                        );
                                    })}
                                </div>
                                <div
                                    ref={loadMoreRef}
                                    className="my-attempts-load-more"
                                    aria-hidden="true"
                                />

                                {isLoadingMore && (
                                    <div className="my-attempts-loading-more">
                                        Loading more quizzes...
                                    </div>
                                )}
                            </>

                        )}
                    </section>
                )}
            </div>
        </main>
    );
}