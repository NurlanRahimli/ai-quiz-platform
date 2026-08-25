import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/useAuth"
import axios from "axios";

import {
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  CircleHelp,
  Search,
  Sparkles,
  Star,
  UserRound,
  Users,
} from "lucide-react";

import apiClient from "../../api/client";
import QuizIcon from "../../components/quizzes/QuizIcon";
import "../../styles/pages/quizzes/DiscoverQuizzesPage.css";

type DiscoveryQuiz = {
  id: string;
  owner_id: string;
  title: string;
  description: string | null;
  visibility: "public" | "unlisted";
  category: string | null;
  tags: string[];
  icon: string;
  creator_name: string;
  question_count: number;
  attempt_count: number;
  created_at: string;
  updated_at: string;
};

type DiscoveryPageResponse = {
  quizzes: DiscoveryQuiz[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

type DiscoveryOverviewResponse = {
  featured: DiscoveryQuiz[];
  categories: string[];
};


function getPaginationItems(
  currentPage: number,
  totalPages: number,
  isMobile = false,
): Array<number | "ellipsis"> {
  if (totalPages <= (isMobile ? 5 : 10)) {
    return Array.from(
      { length: totalPages },
      (_, index) => index + 1,
    );
  }

  const pages = new Set<number>();

  if (isMobile) {
    // Current page + one page on each side.
    for (
      let pageNumber = currentPage - 1;
      pageNumber <= currentPage + 1;
      pageNumber += 1
    ) {
      if (pageNumber >= 1 && pageNumber <= totalPages) {
        pages.add(pageNumber);
      }
    }

    // Always show the final two pages.
    pages.add(totalPages - 1);
    pages.add(totalPages);
  } else {
    // Always show the first page.
    pages.add(1);

    // Desktop: three pages on each side.
    for (
      let pageNumber = currentPage - 3;
      pageNumber <= currentPage + 3;
      pageNumber += 1
    ) {
      if (pageNumber >= 1 && pageNumber <= totalPages) {
        pages.add(pageNumber);
      }
    }

    // Always show the final three pages.
    for (
      let pageNumber = Math.max(1, totalPages - 2);
      pageNumber <= totalPages;
      pageNumber += 1
    ) {
      pages.add(pageNumber);
    }
  }

  const sortedPages = Array.from(pages).sort((a, b) => a - b);
  const items: Array<number | "ellipsis"> = [];

  sortedPages.forEach((pageNumber, index) => {
    const previousPage = sortedPages[index - 1];

    if (
      previousPage !== undefined &&
      pageNumber - previousPage > 1
    ) {
      items.push("ellipsis");
    }

    items.push(pageNumber);
  });

  return items;
}


export default function DiscoverQuizzesPage() {
  const navigate = useNavigate();
  const { user } = useAuth()
  const [quizzes, setQuizzes] = useState<DiscoveryQuiz[]>([]);
  const [featured, setFeatured] = useState<DiscoveryQuiz[]>([]);
  const [categories, setCategories] = useState<string[]>([]);

  const [selectedCategory, setSelectedCategory] = useState("");
  const [page, setPage] = useState(1);

  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  const [isLoading, setIsLoading] = useState(true);
  const [isChangingPage, setIsChangingPage] = useState(false);
  const [isOverviewLoading, setIsOverviewLoading] = useState(true);
  const [error, setError] = useState("");
  const [isMobilePagination, setIsMobilePagination] = useState(
    () => window.matchMedia("(max-width: 640px)").matches,
  );

  useEffect(() => {
    const loadOverview = async () => {
      try {
        const response =
          await apiClient.get<DiscoveryOverviewResponse>(
            "/quizzes/discover/overview",
          );

        setFeatured(response.data.featured);
        setCategories(response.data.categories);
      } catch (requestError) {
        if (axios.isAxiosError(requestError)) {
          const detail = requestError.response?.data?.detail;

          setError(
            typeof detail === "string"
              ? detail
              : "Unable to load quiz discovery.",
          );
        } else {
          setError("Unable to load quiz discovery.");
        }
      } finally {
        setIsOverviewLoading(false);
      }
    };

    void loadOverview();
  }, []);

  useEffect(() => {
    const loadQuizzes = async () => {
      if (page === 1) {
        setIsLoading(true);
      } else {
        setIsChangingPage(true);
      }

      try {
        const response = await apiClient.get<DiscoveryPageResponse>(
          "/quizzes/discover",
          {
            params: {
              page,
              page_size: 5,
              category: selectedCategory || undefined,
            },
          },
        );

        setQuizzes(response.data.quizzes);
        setTotal(response.data.total);
        setTotalPages(response.data.total_pages);
        setError("");
      } catch (requestError) {
        if (axios.isAxiosError(requestError)) {
          const detail = requestError.response?.data?.detail;

          setError(
            typeof detail === "string"
              ? detail
              : "Unable to load quizzes.",
          );
        } else {
          setError("Unable to load quizzes.");
        }
      } finally {
        setIsLoading(false);
        setIsChangingPage(false);
      }
    };

    const timeoutId = window.setTimeout(() => {
      void loadQuizzes();
    }, 300);

    return () => window.clearTimeout(timeoutId);
  }, [page, selectedCategory]);


  useEffect(() => {
    const mediaQuery = window.matchMedia("(max-width: 640px)");

    const handleChange = (event: MediaQueryListEvent) => {
      setIsMobilePagination(event.matches);
    };

    mediaQuery.addEventListener("change", handleChange);

    return () => {
      mediaQuery.removeEventListener("change", handleChange);
    };
  }, []);

  const handleCategoryChange = (category: string) => {
    setSelectedCategory(category);
    setPage(1);
  };

  return (
    <div className="discover-page">
      <header className="discover-header">
        <div>
          <span className="discover-eyebrow">
            <Sparkles size={14} aria-hidden="true" />
            Community
          </span>

          <h1>Discover Quizzes</h1>

          <p>
            Explore public quizzes created by the community and
            find something new to learn.
          </p>
        </div>
      </header>

      <section
        className="discover-search-section"
        aria-label="Search and filter quizzes"
      >
        <button
          type="button"
          className="discover-search"
          onClick={() => navigate("/discover/search")}
          aria-label="Search quizzes"
        >
          <Search size={20} aria-hidden="true" />

          <span>
            Search quizzes by title, creator, category, or tag...
          </span>
        </button>

        {!isOverviewLoading && categories.length > 0 && (
          <div
            className="discover-categories"
            aria-label="Filter by category"
          >
            <button
              type="button"
              className={
                selectedCategory === ""
                  ? "discover-category discover-category--active"
                  : "discover-category"
              }
              onClick={() => handleCategoryChange("")}
            >
              All
            </button>

            {categories.map((category) => (
              <button
                key={category}
                type="button"
                className={
                  selectedCategory === category
                    ? "discover-category discover-category--active"
                    : "discover-category"
                }
                onClick={() => handleCategoryChange(category)}
              >
                {category}
              </button>
            ))}
          </div>
        )}
      </section>

      {error && (
        <div className="discover-error" role="alert">
          {error}
        </div>
      )}

      <section className="discover-featured">
        <div className="discover-section-heading">
          <div>
            <h2>
              <Star size={18} aria-hidden="true" />
              Featured Quizzes
            </h2>

            <p>Popular quizzes from the community.</p>
          </div>

          {!isOverviewLoading && featured.length > 0 && (
            <span className="discover-section-label">Most popular</span>
          )}
        </div>

        {isOverviewLoading ? (
          <div className="discover-section-state">
            Loading featured quizzes...
          </div>
        ) : featured.length === 0 ? (
          <div className="discover-section-state">
            No public quizzes are available yet.
          </div>
        ) : (
          <div className="discover-featured-grid">
            {featured.map((quiz) => (
              <article
                key={quiz.id}
                className="discover-featured-card"
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
                <div className="discover-featured-card__top">
                  <div className="discover-featured-card__icon">
                    <QuizIcon name={quiz.icon} size={22} />
                  </div>

                  {quiz.category && (
                    <span className="discover-featured-card__category">
                      {quiz.category}
                    </span>
                  )}
                </div>

                <div className="discover-featured-card__content">
                  <h3>{quiz.title}</h3>

                  <p>
                    {quiz.description ||
                      "Test your knowledge with this community quiz."}
                  </p>

                  {quiz.tags.length > 0 && (
                    <div className="discover-featured-card__tags">
                      {quiz.tags.slice(0, 3).map((tag) => (
                        <span key={tag}>#{tag}</span>
                      ))}
                    </div>
                  )}
                </div>

                <div className="discover-featured-card__creator">
                  <UserRound size={14} aria-hidden="true" />

                  {user?.id === quiz.owner_id ? (
                    <span className="discover-created-by-me">
                      Created by Me
                    </span>
                  ) : (
                    <>
                      <span>By</span>

                      <button
                        type="button"
                        className="discover-creator-link"
                        onClick={(event) => {
                          event.stopPropagation()
                          navigate(`/users/${quiz.owner_id}`)
                        }}
                      >
                        {quiz.creator_name}
                      </button>
                    </>
                  )}
                </div>

                <div className="discover-featured-card__footer">
                  <div className="discover-featured-card__stats">
                    <span>
                      <CircleHelp size={15} aria-hidden="true" />
                      {quiz.question_count}{" "}
                      {quiz.question_count === 1 ? "Question" : "Questions"}
                    </span>

                    <span>
                      <Users size={15} aria-hidden="true" />
                      {quiz.attempt_count}{" "}
                      {quiz.attempt_count === 1 ? "Attempt" : "Attempts"}
                    </span>
                  </div>

                  <ArrowRight
                    className="discover-featured-card__arrow"
                    size={19}
                    aria-hidden="true"
                  />
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="discover-all">
        <div className="discover-section-heading">
          <div>
            <h2>All Quizzes</h2>
            <p>Browse public quizzes from the community.</p>
          </div>

          <div className="discover-all__status">
            {isChangingPage && (
              <span className="discover-all__loading">
                <span className="discover-all__loading-dot" />
                Loading
              </span>
            )}

            {!isLoading && (
              <span className="discover-section-label">
                {total} {total === 1 ? "quiz" : "quizzes"}
              </span>
            )}
          </div>
        </div>

        {isLoading && quizzes.length === 0 ? (
          <div className="discover-section-state">
            Loading quizzes...
          </div>
        ) : quizzes.length === 0 ? (
          <div className="discover-section-state">
            {selectedCategory
              ? "No quizzes match your search or selected category."
              : "No public quizzes are available yet."}
          </div>
        ) : (
          <div
            className={`discover-quiz-list ${isChangingPage ? "discover-quiz-list--loading" : ""
              }`}
          >
            {quizzes.map((quiz) => (
              <article
                key={quiz.id}
                className="discover-quiz-row"
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
                <div className="discover-quiz-row__icon">
                  <QuizIcon name={quiz.icon} size={21} />
                </div>

                <div className="discover-quiz-row__main">
                  <div className="discover-quiz-row__title-line">
                    <h3>{quiz.title}</h3>

                    {quiz.category && (
                      <span className="discover-quiz-row__category">
                        {quiz.category}
                      </span>
                    )}
                  </div>

                  <p>
                    {quiz.description ||
                      "Test your knowledge with this community quiz."}
                  </p>

                  {quiz.tags.length > 0 && (
                    <div className="discover-quiz-row__tags">
                      {quiz.tags.slice(0, 3).map((tag) => (
                        <span key={tag}>#{tag}</span>
                      ))}
                    </div>
                  )}

                  <div className="discover-quiz-row__mobile-meta">
                    <div className="discover-quiz-row__mobile-creator">
                      <UserRound size={14} aria-hidden="true" />

                      {user?.id === quiz.owner_id ? (
                        <span className="discover-created-by-me">
                          Created by Me
                        </span>
                      ) : (
                        <>
                          <span>By</span>

                          <button
                            type="button"
                            className="discover-creator-link"
                            onClick={(event) => {
                              event.stopPropagation()
                              navigate(`/users/${quiz.owner_id}`)
                            }}
                          >
                            {quiz.creator_name}
                          </button>
                        </>
                      )}
                    </div>

                    <div className="discover-quiz-row__mobile-stats">
                      <span>
                        <CircleHelp size={14} aria-hidden="true" />
                        {quiz.question_count}{" "}
                        {quiz.question_count === 1 ? "Question" : "Questions"}
                      </span>

                      <span>
                        <Users size={14} aria-hidden="true" />
                        {quiz.attempt_count}{" "}
                        {quiz.attempt_count === 1 ? "Attempt" : "Attempts"}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="discover-quiz-row__creator">
                  <UserRound size={15} aria-hidden="true" />

                  {user?.id === quiz.owner_id ? (
                    <span className="discover-created-by-me">
                      Created by Me
                    </span>
                  ) : (
                    <>
                      <span>By</span>

                      <button
                        type="button"
                        className="discover-creator-link"
                        onClick={(event) => {
                          event.stopPropagation()
                          navigate(`/users/${quiz.owner_id}`)
                        }}
                      >
                        {quiz.creator_name}
                      </button>
                    </>
                  )}
                </div>

                <div className="discover-quiz-row__stat">
                  <CircleHelp size={15} aria-hidden="true" />
                  <span>
                    {quiz.question_count}{" "}
                    {quiz.question_count === 1 ? "Question" : "Questions"}
                  </span>
                </div>

                <div className="discover-quiz-row__stat">
                  <Users size={15} aria-hidden="true" />
                  <span>
                    {quiz.attempt_count}{" "}
                    {quiz.attempt_count === 1 ? "Attempt" : "Attempts"}
                  </span>
                </div>

                <ArrowRight
                  className="discover-quiz-row__arrow"
                  size={19}
                  aria-hidden="true"
                />
              </article>
            ))}
          </div>
        )}

        {quizzes.length > 0 && totalPages > 1 && (
          <nav
            className="discover-pagination"
            aria-label="Quiz pagination"
          >
            <button
              type="button"
              className="discover-pagination__arrow"
              onClick={() => setPage((current) => Math.max(1, current - 1))}
              disabled={page === 1}
              aria-label="Previous page"
            >
              <ChevronLeft size={17} aria-hidden="true" />
            </button>

            <div className="discover-pagination__pages">
              {getPaginationItems(page, totalPages, isMobilePagination).map(
                (item, index) => {
                  if (item === "ellipsis") {
                    return (
                      <span
                        key={`ellipsis-${index}`}
                        className="discover-pagination__ellipsis"
                        aria-hidden="true"
                      >
                        ...
                      </span>
                    );
                  }

                  return (
                    <button
                      key={item}
                      type="button"
                      className={
                        item === page
                          ? "discover-pagination__page discover-pagination__page--active"
                          : "discover-pagination__page"
                      }
                      onClick={() => setPage(item)}
                      aria-label={`Go to page ${item}`}
                      aria-current={item === page ? "page" : undefined}
                    >
                      {item}
                    </button>
                  );
                },
              )}
            </div>

            <button
              type="button"
              className="discover-pagination__arrow"
              onClick={() =>
                setPage((current) => Math.min(totalPages, current + 1))
              }
              disabled={page === totalPages}
              aria-label="Next page"
            >
              <ChevronRight size={17} aria-hidden="true" />
            </button>
          </nav>
        )}
      </section>
    </div>
  );
}