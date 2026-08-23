import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import {
  ArrowRight,
  BarChart3,
  BookOpen,
  CheckCircle2,
  FileQuestion,
  FolderOpen,
  Trophy,
} from "lucide-react";

import apiClient from "../../api/client";
import { useAuth } from "../../auth/useAuth";
import "../../styles/pages/dashboard/DashboardPage.css";

type DashboardStats = {
  total_quizzes: number;
  average_score: number | null;
  quizzes_taken: number;
};

type DashboardRecentQuiz = {
  quiz_id: string;
  quiz_title: string;
  quiz_category: string | null;
  latest_attempt_id: string;
  latest_submitted_at: string;
  score_percentage: number | null;
};

type DashboardPerformancePoint = {
  submitted_at: string;
  score: number;
  average_score: number;
};

type DashboardCategoryPerformance = {
  category: string;
  average_score: number | null;
  attempt_count: number;
};

type DashboardData = {
  stats: DashboardStats;
  recent_quizzes: DashboardRecentQuiz[];
  performance: DashboardPerformancePoint[];
  top_categories: DashboardCategoryPerformance[];
};

function formatRelativeDate(value: string) {
  const date = new Date(value);
  const now = new Date();
  const difference = now.getTime() - date.getTime();

  const minutes = Math.floor(difference / (1000 * 60));
  const hours = Math.floor(difference / (1000 * 60 * 60));
  const days = Math.floor(difference / (1000 * 60 * 60 * 24));

  if (minutes < 1) {
    return "Just now";
  }

  if (minutes < 60) {
    return `${minutes}m ago`;
  }

  if (hours < 24) {
    return `${hours}h ago`;
  }

  if (days === 1) {
    return "Yesterday";
  }

  if (days < 7) {
    return `${days} days ago`;
  }

  if (days < 14) {
    return "1 week ago";
  }

  if (days < 30) {
    return `${Math.floor(days / 7)} weeks ago`;
  }

  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
  }).format(date);
}

function formatChartDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
  }).format(new Date(value));
}

function getScoreClass(score: number | null) {
  if (score === null) {
    return "dashboard-score--neutral";
  }

  if (score >= 80) {
    return "dashboard-score--high";
  }

  if (score >= 70) {
    return "dashboard-score--medium";
  }

  return "dashboard-score--low";
}

function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let isCancelled = false;

    const loadDashboard = async () => {
      try {
        const response = await apiClient.get<DashboardData>("/dashboard");

        if (isCancelled) {
          return;
        }

        setDashboard(response.data);
        setError("");
      } catch (requestError) {
        if (isCancelled) {
          return;
        }

        if (axios.isAxiosError(requestError)) {
          const detail = requestError.response?.data?.detail;

          setError(
            typeof detail === "string"
              ? detail
              : "Unable to load your dashboard.",
          );
        } else {
          setError("Unable to load your dashboard.");
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    };

    void loadDashboard();

    return () => {
      isCancelled = true;
    };
  }, []);

  const performanceChart = useMemo(() => {
    const points = dashboard?.performance ?? [];

    if (points.length === 0) {
      return null;
    }

    const width = 700;
    const height = 260;
    const paddingLeft = 52;
    const paddingRight = 20;
    const paddingTop = 20;
    const paddingBottom = 42;

    const chartWidth = width - paddingLeft - paddingRight;
    const chartHeight = height - paddingTop - paddingBottom;

    const xForIndex = (index: number) => {
      if (points.length === 1) {
        return paddingLeft + chartWidth / 2;
      }

      return paddingLeft + (index / (points.length - 1)) * chartWidth;
    };

    const yForScore = (score: number) =>
      paddingTop + chartHeight - (score / 100) * chartHeight;

    const scorePoints = points
      .map(
        (point, index) =>
          `${xForIndex(index)},${yForScore(point.score)}`,
      )
      .join(" ");

    const averagePoints = points
      .map(
        (point, index) =>
          `${xForIndex(index)},${yForScore(point.average_score)}`,
      )
      .join(" ");

    const areaPoints = [
      `${xForIndex(0)},${paddingTop + chartHeight}`,
      ...points.map(
        (point, index) =>
          `${xForIndex(index)},${yForScore(point.score)}`,
      ),
      `${xForIndex(points.length - 1)},${paddingTop + chartHeight}`,
    ].join(" ");

    const labelIndexes = Array.from(
      new Set([
        0,
        Math.floor((points.length - 1) / 3),
        Math.floor(((points.length - 1) * 2) / 3),
        points.length - 1,
      ]),
    );

    return {
      width,
      height,
      paddingLeft,
      paddingTop,
      chartHeight,
      scorePoints,
      averagePoints,
      areaPoints,
      xForIndex,
      yForScore,
      labelIndexes,
    };
  }, [dashboard?.performance]);

  const averageScore = dashboard?.stats.average_score ?? null;

  return (
    <div className="dashboard-page">
      <header className="dashboard-header">
        <div className="dashboard-header__content">
          <h1>
            Welcome back
            {user?.display_name ? `, ${user.display_name}` : ""}{" "}
            <span className="dashboard-wave" aria-hidden="true">
              👋
            </span>
          </h1>

          <p className="dashboard-subtitle">
            Let's continue your learning journey.
          </p>
        </div>

        <button
          type="button"
          className="dashboard-create-button"
          onClick={() => navigate("/quizzes/new")}
        >
          <span aria-hidden="true">＋</span>
          Create Quiz
        </button>
      </header>

      {error && (
        <div className="dashboard-error" role="alert">
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="dashboard-loading" aria-live="polite">
          <div className="dashboard-loading__spinner" aria-hidden="true" />
          <p>Loading your dashboard...</p>
        </div>
      ) : dashboard ? (
        <>
          <section
            className="dashboard-stats"
            aria-label="Dashboard overview"
          >
            <article className="dashboard-stat-card">
              <div className="dashboard-stat-card__icon" aria-hidden="true">
                <FileQuestion size={22} strokeWidth={2} />
              </div>

              <div className="dashboard-stat-card__content">
                <span className="dashboard-stat-card__label">
                  Total Quizzes
                </span>

                <strong className="dashboard-stat-card__value">
                  {dashboard.stats.total_quizzes}
                </strong>

                <span className="dashboard-stat-card__hint">
                  Quizzes you've created
                </span>
              </div>
            </article>

            <article className="dashboard-stat-card">
              <div className="dashboard-stat-card__icon" aria-hidden="true">
                <Trophy size={22} strokeWidth={2} />
              </div>

              <div className="dashboard-stat-card__content">
                <span className="dashboard-stat-card__label">
                  Average Score
                </span>

                <strong className="dashboard-stat-card__value">
                  {averageScore === null
                    ? "—"
                    : `${Math.round(averageScore)}%`}
                </strong>

                <span className="dashboard-stat-card__hint">
                  {averageScore === null
                    ? "No graded attempts yet"
                    : "Across graded attempts"}
                </span>
              </div>
            </article>

            <article className="dashboard-stat-card">
              <div className="dashboard-stat-card__icon" aria-hidden="true">
                <BarChart3 size={22} strokeWidth={2} />
              </div>

              <div className="dashboard-stat-card__content">
                <span className="dashboard-stat-card__label">
                  Quizzes Taken
                </span>

                <strong className="dashboard-stat-card__value">
                  {dashboard.stats.quizzes_taken}
                </strong>

                <span className="dashboard-stat-card__hint">
                  Unique quizzes completed
                </span>
              </div>
            </article>
          </section>

          <div className="dashboard-content-grid">
            <div className="dashboard-column dashboard-column--left">
              <section className="dashboard-panel dashboard-recent">
                <div className="dashboard-panel__header">
                  <div>
                    <h2>Recent Quizzes</h2>
                    <p>Your latest quiz activity</p>
                  </div>

                  <button
                    type="button"
                    className="dashboard-view-button"
                    onClick={() => navigate("/attempts")}
                  >
                    View all
                  </button>
                </div>

                {dashboard.recent_quizzes.length > 0 ? (
                  <div className="dashboard-recent__list">
                    {dashboard.recent_quizzes.map((quiz) => (
                      <button
                        key={quiz.quiz_id}
                        type="button"
                        className="dashboard-recent-item"
                        onClick={() =>
                          navigate(`/quizzes/${quiz.quiz_id}/history`)
                        }
                      >
                        <div
                          className="dashboard-recent-item__icon"
                          aria-hidden="true"
                        >
                          <BookOpen size={18} strokeWidth={2} />
                        </div>

                        <div className="dashboard-recent-item__details">
                          <strong>{quiz.quiz_title}</strong>

                          <span>
                            {quiz.quiz_category || "Uncategorized"}
                          </span>
                        </div>

                        <div className="dashboard-recent-item__meta">
                          <span
                            className={`dashboard-score ${getScoreClass(
                              quiz.score_percentage,
                            )}`}
                          >
                            {quiz.score_percentage === null
                              ? "—"
                              : `${Math.round(quiz.score_percentage)}%`}
                          </span>

                          <span className="dashboard-recent-item__date">
                            {formatRelativeDate(
                              quiz.latest_submitted_at,
                            )}
                          </span>

                          <ArrowRight
                            size={16}
                            strokeWidth={2}
                            aria-hidden="true"
                          />
                        </div>
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="dashboard-panel-empty dashboard-panel-empty--recent">
                    <BookOpen size={30} strokeWidth={1.8} aria-hidden="true" />

                    <div>
                      <strong>No quizzes taken yet</strong>
                      <p>
                        Complete a quiz and your recent activity will appear
                        here.
                      </p>
                    </div>
                  </div>
                )}

                <button
                  type="button"
                  className="dashboard-panel-link"
                  onClick={() => navigate("/attempts")}
                >
                  <span>View all quizzes</span>
                  <ArrowRight size={16} strokeWidth={2} aria-hidden="true" />
                </button>
              </section>

              <section className="dashboard-panel dashboard-continue">
                <div className="dashboard-continue__visual" aria-hidden="true">
                  <div className="dashboard-continue__books">
                    <span />
                    <span />
                    <span />
                  </div>

                  <div className="dashboard-continue__check">
                    <CheckCircle2 size={44} strokeWidth={1.8} />
                  </div>
                </div>

                <div className="dashboard-continue__content">
                  <h2>Continue Learning</h2>
                  <strong>Ready for your next quiz?</strong>

                  <p>
                    Discover new quizzes and keep building your knowledge.
                  </p>

                  <button
                    type="button"
                    className="dashboard-primary-action"
                    onClick={() => navigate("/discover")}
                  >
                    Browse Quizzes
                  </button>
                </div>
              </section>
            </div>

            <div className="dashboard-column dashboard-column--right">
              <section className="dashboard-panel dashboard-performance">
                <div className="dashboard-panel__header">
                  <div>
                    <h2>Performance Overview</h2>
                    <p>Your scores over the last year</p>
                  </div>

                  <span className="dashboard-period">Last Year</span>
                </div>

                {performanceChart && dashboard.performance.length > 0 ? (
                  <>
                    <div className="dashboard-chart">
                      <svg
                        viewBox={`0 0 ${performanceChart.width} ${performanceChart.height}`}
                        role="img"
                        aria-label="Performance scores over the last year"
                        preserveAspectRatio="none"
                      >
                        <defs>
                          <linearGradient
                            id="dashboard-score-area"
                            x1="0"
                            y1="0"
                            x2="0"
                            y2="1"
                          >
                            <stop
                              offset="0%"
                              stopColor="currentColor"
                              stopOpacity="0.28"
                            />
                            <stop
                              offset="100%"
                              stopColor="currentColor"
                              stopOpacity="0"
                            />
                          </linearGradient>
                        </defs>

                        {[0, 25, 50, 75, 100].map((value) => {
                          const y = performanceChart.yForScore(value);

                          return (
                            <g key={value}>
                              <line
                                className="dashboard-chart__grid"
                                x1={performanceChart.paddingLeft}
                                y1={y}
                                x2={performanceChart.width - 20}
                                y2={y}
                              />

                              <text
                                className="dashboard-chart__axis-label"
                                x={performanceChart.paddingLeft - 10}
                                y={y + 4}
                                textAnchor="end"
                              >
                                {value}%
                              </text>
                            </g>
                          );
                        })}

                        <polygon
                          className="dashboard-chart__area"
                          points={performanceChart.areaPoints}
                          fill="url(#dashboard-score-area)"
                        />

                        <polyline
                          className="dashboard-chart__average-line"
                          points={performanceChart.averagePoints}
                        />

                        <polyline
                          className="dashboard-chart__score-line"
                          points={performanceChart.scorePoints}
                        />

                        {dashboard.performance.map((point, index) => (
                          <circle
                            key={`${point.submitted_at}-${index}`}
                            className="dashboard-chart__point"
                            cx={performanceChart.xForIndex(index)}
                            cy={performanceChart.yForScore(point.score)}
                            r="4"
                          >
                            <title>
                              {`${formatChartDate(point.submitted_at)}: ${Math.round(
                                point.score,
                              )}%`}
                            </title>
                          </circle>
                        ))}

                        {performanceChart.labelIndexes.map((index) => (
                          <text
                            key={index}
                            className="dashboard-chart__date-label"
                            x={performanceChart.xForIndex(index)}
                            y={performanceChart.height - 10}
                            textAnchor={
                              index === 0
                                ? "start"
                                : index === dashboard.performance.length - 1
                                  ? "end"
                                  : "middle"
                            }
                          >
                            {formatChartDate(
                              dashboard.performance[index].submitted_at,
                            )}
                          </text>
                        ))}
                      </svg>
                    </div>

                    <div className="dashboard-chart-legend">
                      <span>
                        <i className="dashboard-chart-legend__score" />
                        Your Score
                      </span>

                      <span>
                        <i className="dashboard-chart-legend__average" />
                        Average Score
                      </span>
                    </div>
                  </>
                ) : (
                  <div className="dashboard-panel-empty dashboard-panel-empty--chart">
                    <BarChart3 size={32} strokeWidth={1.8} aria-hidden="true" />

                    <div>
                      <strong>No performance data yet</strong>
                      <p>
                        Your score history will appear after you complete
                        graded quizzes.
                      </p>
                    </div>
                  </div>
                )}
              </section>

              <section className="dashboard-panel dashboard-categories">
                <div className="dashboard-panel__header">
                  <div>
                    <h2>Top Categories</h2>
                    <p>Categories you quiz in most</p>
                  </div>

                  <button
                    type="button"
                    className="dashboard-view-button"
                    onClick={() => navigate("/attempts")}
                  >
                    View all
                  </button>
                </div>

                {dashboard.top_categories.length > 0 ? (
                  <div className="dashboard-category-list">
                    {dashboard.top_categories.map((category) => {
                      const progress = category.average_score ?? 0;

                      return (
                        <div
                          key={category.category}
                          className="dashboard-category"
                        >
                          <div className="dashboard-category__top">
                            <div className="dashboard-category__name">
                              <span
                                className="dashboard-category__icon"
                                aria-hidden="true"
                              >
                                <FolderOpen size={17} strokeWidth={2} />
                              </span>

                              <div>
                                <strong>{category.category}</strong>
                                <span>
                                  {category.attempt_count}{" "}
                                  {category.attempt_count === 1
                                    ? "attempt"
                                    : "attempts"}
                                </span>
                              </div>
                            </div>

                            <strong className="dashboard-category__score">
                              {category.average_score === null
                                ? "—"
                                : `${Math.round(category.average_score)}%`}
                            </strong>
                          </div>

                          <div
                            className="dashboard-category__track"
                            aria-hidden="true"
                          >
                            <span
                              style={{
                                width: `${Math.max(
                                  0,
                                  Math.min(100, progress),
                                )}%`,
                              }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="dashboard-panel-empty">
                    <FolderOpen size={30} strokeWidth={1.8} aria-hidden="true" />

                    <div>
                      <strong>No category activity yet</strong>
                      <p>
                        Categories will appear as you complete quizzes.
                      </p>
                    </div>
                  </div>
                )}
              </section>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}

export default DashboardPage;
