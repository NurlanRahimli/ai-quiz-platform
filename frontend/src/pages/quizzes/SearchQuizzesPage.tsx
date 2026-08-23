import {
    useCallback,
    useEffect,
    useRef,
    useState,
} from "react";
import { useAuth } from "../../auth/useAuth"

import axios from "axios";

import {
    ArrowLeft,
    ArrowRight,
    CircleHelp,
    Search,
    UserRound,
} from "lucide-react";

import apiClient from "../../api/client";
import { useNavigate } from "react-router-dom";


import "../../styles/pages/quizzes/SearchQuizzesPage.css";


type SearchQuiz = {
    id: string;
    owner_id: string;
    title: string;
    description: string | null;
    visibility: "public" | "unlisted";
    category: string | null;
    tags: string[];
    creator_name: string;
    question_count: number;
    attempt_count: number;
    created_at: string;
    updated_at: string;
};

type SearchResponse = {
    quizzes: SearchQuiz[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
};

type DiscoveryOverviewResponse = {
    categories: string[];
};


export default function SearchQuizzesPage() {
    const navigate = useNavigate();
    const { user } = useAuth()
    const inputRef = useRef<HTMLInputElement>(null);
    const loadMoreRef = useRef<HTMLDivElement>(null);

    const [search, setSearch] = useState("");
    const [isLoadingMore, setIsLoadingMore] = useState(false);
    const [submittedSearch, setSubmittedSearch] = useState("");
    const [results, setResults] = useState<SearchQuiz[]>([]);
    const [resultsPage, setResultsPage] = useState(1);
    const [resultsTotal, setResultsTotal] = useState(0);
    const [resultsTotalPages, setResultsTotalPages] = useState(0);
    const [isLoadingResults, setIsLoadingResults] = useState(false);
    const [resultsError, setResultsError] = useState("");
    const [suggestions, setSuggestions] = useState<SearchQuiz[]>([]);
    const [isSearching, setIsSearching] = useState(false);
    const [error, setError] = useState("");
    const [selectedCategory, setSelectedCategory] = useState("");
    const [categories, setCategories] = useState<string[]>([]);
    const [sortBy, setSortBy] = useState<
        "popular" | "newest" | "oldest"
    >("popular");


    useEffect(() => {
        inputRef.current?.focus();
    }, []);


    useEffect(() => {
        if (!submittedSearch) {
            return;
        }

        const loadResults = async () => {
            setIsLoadingResults(true);

            try {
                const response = await apiClient.get<SearchResponse>(
                    "/quizzes/discover",
                    {
                        params: {
                            page: 1,
                            page_size: 10,
                            search: submittedSearch,
                            category: selectedCategory || undefined,
                            sort: sortBy,
                        },
                    },
                );

                setResults(response.data.quizzes);
                setResultsPage(response.data.page);
                setResultsTotal(response.data.total);
                setResultsTotalPages(response.data.total_pages);
                setResultsError("");
            } catch (requestError) {
                setResults([]);

                if (axios.isAxiosError(requestError)) {
                    const detail = requestError.response?.data?.detail;

                    setResultsError(
                        typeof detail === "string"
                            ? detail
                            : "Unable to load search results.",
                    );
                } else {
                    setResultsError("Unable to load search results.");
                }
            } finally {
                setIsLoadingResults(false);
            }
        };

        void loadResults();
    }, [submittedSearch, selectedCategory, sortBy]);


    useEffect(() => {
        const query = search.trim();

        if (!query || submittedSearch) {
            return;
        }

        const timeoutId = window.setTimeout(() => {
            const loadSuggestions = async () => {
                setIsSearching(true);

                try {
                    const response = await apiClient.get<SearchResponse>(
                        "/quizzes/discover",
                        {
                            params: {
                                page: 1,
                                page_size: 6,
                                search: query,
                            },
                        },
                    );

                    setSuggestions(response.data.quizzes);
                    setError("");
                } catch (requestError) {
                    setSuggestions([]);

                    if (axios.isAxiosError(requestError)) {
                        const detail = requestError.response?.data?.detail;

                        setError(
                            typeof detail === "string"
                                ? detail
                                : "Unable to search quizzes.",
                        );
                    } else {
                        setError("Unable to search quizzes.");
                    }
                } finally {
                    setIsSearching(false);
                }
            };

            void loadSuggestions();
        }, 300);

        return () => {
            window.clearTimeout(timeoutId);
        };
    }, [search, submittedSearch]);


    useEffect(() => {
        const loadCategories = async () => {
            try {
                const response =
                    await apiClient.get<DiscoveryOverviewResponse>(
                        "/quizzes/discover/overview",
                    );

                setCategories(response.data.categories);
            } catch {
                setCategories([]);
            }
        };

        void loadCategories();
    }, []);


    const loadMoreResults = useCallback(async () => {
        if (
            isLoadingMore ||
            isLoadingResults ||
            !submittedSearch ||
            resultsPage >= resultsTotalPages
        ) {
            return;
        }

        const nextPage = resultsPage + 1;

        setIsLoadingMore(true);

        try {
            const response = await apiClient.get<SearchResponse>(
                "/quizzes/discover",
                {
                    params: {
                        page: nextPage,
                        page_size: 10,
                        search: submittedSearch,
                        category: selectedCategory || undefined,
                        sort: sortBy,
                    },
                },
            );

            setResults((currentResults) => [
                ...currentResults,
                ...response.data.quizzes,
            ]);

            setResultsPage(response.data.page);
            setResultsTotal(response.data.total);
            setResultsTotalPages(response.data.total_pages);
        } catch {
            setResultsError("Unable to load more quizzes.");
        } finally {
            setIsLoadingMore(false);
        }
    }, [
        isLoadingMore,
        isLoadingResults,
        submittedSearch,
        resultsPage,
        resultsTotalPages,
        selectedCategory,
        sortBy,
    ]);


    useEffect(() => {
        const target = loadMoreRef.current;

        if (
            !target ||
            !submittedSearch ||
            resultsPage >= resultsTotalPages
        ) {
            return;
        }

        const observer = new IntersectionObserver(
            (entries) => {
                const [entry] = entries;

                if (entry.isIntersecting) {
                    void loadMoreResults();
                }
            },
            {
                root: null,
                rootMargin: "200px 0px",
                threshold: 0,
            },
        );

        observer.observe(target);

        return () => {
            observer.disconnect();
        };
    }, [
        submittedSearch,
        resultsPage,
        resultsTotalPages,
        loadMoreResults,
    ]);


    const handleSuggestionClick = (suggestion: SearchQuiz) => {
        submitSearch(suggestion.title);
    };


    const submitSearch = (query: string) => {
        const normalizedQuery = query.trim();

        if (!normalizedQuery) {
            return;
        }

        setSearch(normalizedQuery);
        setResults([]);
        setResultsPage(1);
        setResultsTotal(0);
        setResultsTotalPages(0);
        setResultsError("");
        setSuggestions([]);
        setSelectedCategory("");
        setSubmittedSearch(normalizedQuery);
    };


    return (
        <div className="quiz-search-page">
            <div className="quiz-search-topbar">
                <button
                    type="button"
                    className="quiz-search-back"
                    onClick={() => navigate(-1)}
                    aria-label="Go back"
                >
                    <ArrowLeft size={20} aria-hidden="true" />
                </button>

                <form
                    className="quiz-search-input"
                    onSubmit={(event) => {
                        event.preventDefault();
                        submitSearch(search);
                    }}
                >
                    <Search size={19} aria-hidden="true" />

                    <input
                        ref={inputRef}
                        type="search"
                        value={search}
                        onChange={(event) => {
                            setSearch(event.target.value);
                            setSubmittedSearch("");
                        }}
                        placeholder="Search quizzes by title, creator, category, or tag..."
                        aria-label="Search quizzes"
                    />
                </form>
            </div>

            {submittedSearch ? (
                <section className="quiz-search-results">
                    <div className="quiz-search-results__header">
                        <div>
                            <span className="quiz-search-results__eyebrow">
                                Search results
                            </span>

                            <h1>
                                Results for <strong>"{submittedSearch}"</strong>
                            </h1>
                        </div>

                        {!isLoadingResults && !resultsError && (
                            <span className="quiz-search-results__count">
                                {resultsTotal}{" "}
                                {resultsTotal === 1 ? "quiz" : "quizzes"}
                            </span>
                        )}
                    </div>

                    <div className="quiz-search-controls">
                        <div className="quiz-search-controls__group">
                            <label htmlFor="quiz-search-category">
                                Filter
                            </label>

                            <select
                                id="quiz-search-category"
                                value={selectedCategory}
                                onChange={(event) =>
                                    setSelectedCategory(event.target.value)
                                }
                            >
                                <option value="">All categories</option>
                                {categories.map((category) => (
                                    <option key={category} value={category}>
                                        {category}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="quiz-search-controls__group">
                            <label htmlFor="quiz-search-sort">
                                Sort by
                            </label>

                            <select
                                id="quiz-search-sort"
                                value={sortBy}
                                onChange={(event) =>
                                    setSortBy(
                                        event.target.value as
                                        | "popular"
                                        | "newest"
                                        | "oldest",
                                    )
                                }
                            >
                                <option value="popular">Most popular</option>
                                <option value="newest">Newest</option>
                                <option value="oldest">Oldest</option>
                            </select>
                        </div>
                    </div>

                    {isLoadingResults ? (
                        <div className="quiz-search-results__state">
                            <span className="quiz-search-results__loader" />
                            <span>Finding quizzes...</span>
                        </div>
                    ) : resultsError ? (
                        <div className="quiz-search-results__state">
                            {resultsError}
                        </div>
                    ) : results.length === 0 ? (
                        <div className="quiz-search-results__state">
                            <Search size={22} aria-hidden="true" />

                            <div>
                                <strong>No quizzes found</strong>
                                <span>
                                    Try another title, creator, category, or tag.
                                </span>
                            </div>
                        </div>
                    ) : (
                        <>
                            <div className="quiz-search-results__list">
                                {results.map((quiz, index) => (
                                    <article
                                        key={quiz.id}
                                        className={`quiz-search-result-card ${index >= 10 ? "quiz-search-result-card--loaded" : ""
                                            }`}
                                        style={
                                            index >= 10
                                                ? {
                                                    animationDelay: `${Math.min(
                                                        (index % 10) * 35,
                                                        315,
                                                    )}ms`,
                                                }
                                                : undefined
                                        }
                                        tabIndex={0}
                                        role="link"
                                        onClick={() => navigate(`/quizzes/${quiz.id}`)}
                                        onKeyDown={(event) => {
                                            if (event.key === "Enter" || event.key === " ") {
                                                event.preventDefault();
                                                navigate(`/quizzes/${quiz.id}`);
                                            }
                                        }}
                                    >
                                        <div className="quiz-search-result-card__icon">
                                            <CircleHelp size={21} aria-hidden="true" />
                                        </div>

                                        <div className="quiz-search-result-card__main">
                                            {quiz.category && (
                                                <span className="quiz-search-result-card__category">
                                                    {quiz.category}
                                                </span>
                                            )}

                                            <h2>{quiz.title}</h2>

                                            <p>
                                                {quiz.description ||
                                                    "Test your knowledge with this community quiz."}
                                            </p>

                                            {quiz.tags.length > 0 && (
                                                <div className="quiz-search-result-card__tags">
                                                    {quiz.tags.slice(0, 3).map((tag) => (
                                                        <span key={tag}>#{tag}</span>
                                                    ))}
                                                </div>
                                            )}

                                            <div className="quiz-search-result-card__meta">
                                                <span>
                                                    <UserRound size={13} aria-hidden="true" />

                                                    {user?.id === quiz.owner_id ? (
                                                        <span className="quiz-search-created-by-me">
                                                            Created by Me
                                                        </span>
                                                    ) : (
                                                        <>
                                                            By

                                                            <button
                                                                type="button"
                                                                className="quiz-search-creator-link"
                                                                onClick={(event) => {
                                                                    event.stopPropagation()
                                                                    navigate(`/users/${quiz.owner_id}`)
                                                                }}
                                                            >
                                                                {quiz.creator_name}
                                                            </button>
                                                        </>
                                                    )}
                                                </span>

                                                <span>
                                                    <CircleHelp size={13} aria-hidden="true" />
                                                    {quiz.question_count}{" "}
                                                    {quiz.question_count === 1
                                                        ? "Question"
                                                        : "Questions"}
                                                </span>

                                                <span>
                                                    {quiz.attempt_count}{" "}
                                                    {quiz.attempt_count === 1
                                                        ? "Attempt"
                                                        : "Attempts"}
                                                </span>
                                            </div>
                                        </div>

                                        <ArrowRight
                                            className="quiz-search-result-card__arrow"
                                            size={18}
                                            aria-hidden="true"
                                        />
                                    </article>
                                ))}
                            </div>
                            <div
                                ref={loadMoreRef}
                                className="quiz-search-load-more"
                                aria-hidden="true"
                            />

                            {isLoadingMore && (
                                <div className="quiz-search-load-more__status">
                                    <span className="quiz-search-results__loader" />
                                    <span>Loading more quizzes...</span>
                                </div>
                            )}

                            {!isLoadingMore &&
                                resultsTotalPages > 0 &&
                                resultsPage >= resultsTotalPages && (
                                    <div className="quiz-search-results__end">
                                        You've reached the end of the results.
                                    </div>
                                )}
                        </>


                    )}
                </section>
            ) : !search.trim() ? (
                <div className="quiz-search-empty">
                    <div className="quiz-search-empty__icon">
                        <Search size={24} aria-hidden="true" />
                    </div>

                    <h1>Search for quizzes</h1>

                    <p>
                        Find quizzes by title, creator, category, or tag.
                    </p>
                </div>
            ) : (
                <section className="quiz-search-suggestions">
                    <div className="quiz-search-suggestions__heading">
                        <div>
                            <span>Suggestions</span>
                            <h1>Search results</h1>
                        </div>

                        {isSearching && (
                            <span className="quiz-search-suggestions__loading">
                                Searching...
                            </span>
                        )}
                    </div>

                    {error ? (
                        <div className="quiz-search-message quiz-search-message--error">
                            {error}
                        </div>
                    ) : !isSearching && suggestions.length === 0 ? (
                        <div className="quiz-search-message">
                            <Search size={21} aria-hidden="true" />

                            <div>
                                <strong>No quizzes found</strong>
                                <span>
                                    Try another title, creator, category, or tag.
                                </span>
                            </div>
                        </div>
                    ) : (
                        <div className="quiz-search-suggestion-list">
                            {suggestions.map((quiz) => (
                                <button
                                    key={quiz.id}
                                    type="button"
                                    className="quiz-search-suggestion"
                                    onClick={() => handleSuggestionClick(quiz)}
                                >
                                    <div className="quiz-search-suggestion__icon">
                                        <Search size={17} aria-hidden="true" />
                                    </div>

                                    <div className="quiz-search-suggestion__content">
                                        <strong>{quiz.title}</strong>

                                        <div className="quiz-search-suggestion__context">
                                            {quiz.category && <span>{quiz.category}</span>}

                                            <span>By {quiz.creator_name}</span>
                                        </div>
                                    </div>
                                </button>
                            ))}
                            <button
                                type="button"
                                className="quiz-search-view-all"
                                onClick={() => submitSearch(search)}
                            >
                                <Search size={15} aria-hidden="true" />

                                <span>
                                    See all results for <strong>"{search.trim()}"</strong>
                                </span>

                                <ArrowRight size={16} aria-hidden="true" />
                            </button>
                        </div>
                    )}
                </section>
            )}
        </div>
    );
}