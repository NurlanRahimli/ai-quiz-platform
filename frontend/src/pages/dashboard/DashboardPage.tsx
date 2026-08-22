import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import axios from "axios";
import Swal from "sweetalert2";


import {
  ArrowRight,
  CircleUserRound,
  FileQuestion,
  Plus,
  RefreshCw,
  Sparkles,
  Trash2,
} from "lucide-react";

import apiClient from "../../api/client";
import { useAuth } from "../../auth/useAuth";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";

import "../../styles/pages/dashboard/DashboardPage.css";

type Quiz = {
  id: string;
  owner_id: string;
  title: string;
  description: string | null;
  creator_name: string;
  created_at: string;
  updated_at: string;
};

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingQuizId, setDeletingQuizId] = useState<string | null>(null);
  const [currentTime] = useState(() => Date.now());

  useEffect(() => {
    const loadQuizzes = async () => {
      try {
        const response = await apiClient.get<Quiz[]>("/quizzes");
        setQuizzes(response.data);
      } catch (requestError) {
        if (axios.isAxiosError(requestError)) {
          const detail = requestError.response?.data?.detail;

          setError(
            typeof detail === "string"
              ? detail
              : "Unable to load your quizzes",
          );
        } else {
          setError("Unable to load your quizzes");
        }
      } finally {
        setIsLoading(false);
      }
    };

    void loadQuizzes();
  }, []);


  const deleteQuiz = async (quiz: Quiz) => {
    const result = await Swal.fire({
      title: "Delete quiz?",
      text: `Are you sure you want to delete "${quiz.title}"? This action cannot be undone.`,
      icon: "warning",
      showCancelButton: true,
      confirmButtonText: "Delete Quiz",
      cancelButtonText: "Cancel",
      reverseButtons: true,
      focusCancel: true,
    });

    if (!result.isConfirmed) {
      return;
    }

    setDeletingQuizId(quiz.id);
    setError("");

    try {
      await apiClient.delete(`/quizzes/${quiz.id}`);

      setQuizzes((current) =>
        current.filter((existingQuiz) => existingQuiz.id !== quiz.id),
      );

      await Swal.fire({
        title: "Quiz deleted",
        text: `"${quiz.title}" has been deleted.`,
        icon: "success",
        confirmButtonText: "Done",
      });
    } catch (requestError) {
      let message = "Unable to delete quiz.";

      if (axios.isAxiosError(requestError)) {
        const detail = requestError.response?.data?.detail;

        if (typeof detail === "string") {
          message = detail;
        }
      }

      await Swal.fire({
        title: "Could not delete quiz",
        text: message,
        icon: "error",
        confirmButtonText: "OK",
      });
    } finally {
      setDeletingQuizId(null);
    }
  };


  const recentlyUpdatedQuizzes = useMemo(
    () =>
      [...quizzes]
        .sort(
          (a, b) =>
            new Date(b.updated_at).getTime() -
            new Date(a.updated_at).getTime(),
        )
        .slice(0, 6),
    [quizzes],
  );

  const recentlyCreatedCount = useMemo(() => {
    const sevenDaysAgo = currentTime - 7 * 24 * 60 * 60 * 1000;

    return quizzes.filter(
      (quiz) => new Date(quiz.created_at).getTime() >= sevenDaysAgo,
    ).length;
  }, [quizzes, currentTime]);

  return (
    <div className="dashboard-page">
      <header className="dashboard-header">
        <div className="dashboard-header__content">
          <p className="dashboard-eyebrow">Overview</p>

          <h1>
            Welcome back
            {user?.display_name ? `, ${user.display_name}` : ""}.
          </h1>

          <p className="dashboard-subtitle">
            Create, manage, and keep track of your quizzes.
          </p>
        </div>

        <Button
          size="lg"
          onClick={() => navigate("/quizzes/new")}
        >
          <span aria-hidden="true">＋</span>
          Create Quiz
        </Button>
      </header>

      {error && (
        <div className="dashboard-error" role="alert">
          {error}
        </div>
      )}

      <section
        className="dashboard-stats"
        aria-label="Quiz overview"
      >
        <Card className="dashboard-stat-card">
          <div className="dashboard-stat-card__icon" aria-hidden="true">
            <FileQuestion size={22} strokeWidth={1.9} />
          </div>

          <div>
            <span className="dashboard-stat-card__label">
              Total Quizzes
            </span>

            <strong className="dashboard-stat-card__value">
              {isLoading ? "—" : quizzes.length}
            </strong>
          </div>
        </Card>

        <Card className="dashboard-stat-card">
          <div className="dashboard-stat-card__icon" aria-hidden="true">
            <Sparkles size={22} strokeWidth={1.9} />
          </div>

          <div>
            <span className="dashboard-stat-card__label">
              Created This Week
            </span>

            <strong className="dashboard-stat-card__value">
              {isLoading ? "—" : recentlyCreatedCount}
            </strong>
          </div>
        </Card>

        <Card className="dashboard-stat-card">
          <div className="dashboard-stat-card__icon" aria-hidden="true">
            <RefreshCw size={22} strokeWidth={1.9} />
          </div>

          <div>
            <span className="dashboard-stat-card__label">
              Recently Updated
            </span>

            <strong className="dashboard-stat-card__value">
              {isLoading
                ? "—"
                : recentlyUpdatedQuizzes.length}
            </strong>
          </div>
        </Card>
      </section>

      <section className="dashboard-quizzes">
        <div className="dashboard-section-header">
          <div>
            <h2>Your quizzes</h2>

            <p>
              Open a quiz to edit questions, take it, or review
              previous attempts.
            </p>
          </div>

          {!isLoading && quizzes.length > 0 && (
            <span className="dashboard-quiz-count">
              {quizzes.length}{" "}
              {quizzes.length === 1 ? "quiz" : "quizzes"}
            </span>
          )}
        </div>

        {isLoading ? (
          <Card className="dashboard-state">
            <div
              className="dashboard-loading-spinner"
              aria-hidden="true"
            />

            <p>Loading your quizzes...</p>
          </Card>
        ) : quizzes.length === 0 ? (
          <Card className="dashboard-state dashboard-empty">
            <div
              className="dashboard-empty__icon"
              aria-hidden="true"
            >
              <Plus size={24} strokeWidth={2} />
            </div>

            <h2>Create your first quiz</h2>

            <p>
              Your quizzes will appear here once you create one.
            </p>

            <Button
              size="lg"
              onClick={() => navigate("/quizzes/new")}
            >
              <Plus size={18} strokeWidth={2} aria-hidden="true" />
              Create Quiz
            </Button>
          </Card>
        ) : (
          <div className="dashboard-quiz-grid">
            {recentlyUpdatedQuizzes.map((quiz) => (
              <Card
                key={quiz.id}
                className="dashboard-quiz-card"
                interactive
                role="button"
                tabIndex={0}
                onClick={() => navigate(`/quizzes/${quiz.id}`)}
                onKeyDown={(event) => {
                  if (
                    event.key === "Enter" ||
                    event.key === " "
                  ) {
                    event.preventDefault();
                    navigate(`/quizzes/${quiz.id}`);
                  }
                }}
              >
                <div className="dashboard-quiz-card__top">
                  <span className="dashboard-quiz-card__badge">
                    Quiz
                  </span>

                  <span className="dashboard-quiz-card__date">
                    {formatDate(quiz.updated_at)}
                  </span>
                </div>

                <div className="dashboard-quiz-card__content">
                  <h3>{quiz.title}</h3>

                  <p>
                    {quiz.description ||
                      "No description has been added yet."}
                  </p>

                  <div className="dashboard-quiz-card__creator">
                    <CircleUserRound
                      size={15}
                      strokeWidth={2}
                      aria-hidden="true"
                    />
                    <span>By {quiz.creator_name}</span>
                  </div>
                </div>

                <div className="dashboard-quiz-card__footer">
                  <span>Updated {formatDate(quiz.updated_at)}</span>

                  <div className="dashboard-quiz-card__actions">
                    <button
                      type="button"
                      className="dashboard-quiz-card__delete"
                      disabled={deletingQuizId === quiz.id}
                      onClick={(event) => {
                        event.stopPropagation();
                        void deleteQuiz(quiz);
                      }}
                      onKeyDown={(event) => {
                        event.stopPropagation();
                      }}
                      aria-label={`Delete ${quiz.title}`}
                    >
                      <Trash2 size={15} strokeWidth={2} aria-hidden="true" />
                      {deletingQuizId === quiz.id ? "Deleting..." : "Delete"}
                    </button>

                    <span className="dashboard-quiz-card__action">
                      Edit
                      <ArrowRight
                        size={15}
                        strokeWidth={2}
                        aria-hidden="true"
                      />
                    </span>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default DashboardPage;