import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate, useParams } from "react-router-dom";

import {
  ArrowLeft,
  ArrowRight,
  CalendarDays,
  CircleUserRound,
  Clock3,
  FileQuestion,
  Globe2,
  Link2,
  Pencil,
  Play,
  Share2,
} from "lucide-react";

import apiClient from "../../api/client";
import { useAuth } from "../../auth/useAuth";
import Button from "../../components/ui/Button";
import QuizIcon from "../../components/quizzes/QuizIcon";

import "../../styles/pages/quizzes/QuizDetailsPage.css";

type QuizDetails = {
  id: string;
  owner_id: string;
  title: string;
  description: string | null;
  category: string | null;
  tags: string[];
  icon: string;
  visibility: "public" | "unlisted";
  creator_name: string;
  question_count: number;
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

function QuizDetailsPage() {
  const { quizId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [quiz, setQuiz] = useState<QuizDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const loadQuiz = async () => {
      if (!quizId) {
        setError("Quiz not found");
        setIsLoading(false);
        return;
      }

      try {
        const response = await apiClient.get<QuizDetails>(
          `/quizzes/${quizId}`,
        );

        setQuiz(response.data);
      } catch (requestError) {
        if (
          axios.isAxiosError(requestError) &&
          requestError.response?.status === 404
        ) {
          setError("Quiz not found");
        } else {
          setError("Unable to load quiz details");
        }
      } finally {
        setIsLoading(false);
      }
    };

    void loadQuiz();
  }, [quizId]);

  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);

      window.setTimeout(() => {
        setCopied(false);
      }, 2000);
    } catch {
      setCopied(false);
    }
  };

  if (isLoading) {
    return (
      <div className="quiz-details-page">
        <div className="quiz-details-state">
          <div className="quiz-details-state__icon" aria-hidden="true">
            <FileQuestion size={30} />
          </div>
          <h1>Loading quiz...</h1>
          <p>Getting everything ready for you.</p>
        </div>
      </div>
    );
  }

  if (error || !quiz) {
    return (
      <div className="quiz-details-page">
        <div className="quiz-details-state">
          <div className="quiz-details-state__icon" aria-hidden="true">
            <FileQuestion size={30} />
          </div>

          <h1>Quiz unavailable</h1>
          <p>{error || "This quiz could not be found."}</p>

          <Button onClick={() => navigate("/dashboard")}>
            <ArrowLeft size={17} aria-hidden="true" />
            Back to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  const isOwner = user?.id === quiz.owner_id;

  return (
    <div className="quiz-details-page">
      <div className="quiz-details-container">
        <button
          className="quiz-details-back"
          type="button"
          onClick={() => navigate("/dashboard")}
        >
          <ArrowLeft size={17} aria-hidden="true" />
          Back to dashboard
        </button>

        <section className="quiz-details-hero">
            <div className="quiz-details-hero__main">
                <div className="quiz-details-badges">
                  <div className="quiz-details-eyebrow">
                    <span className="quiz-details-eyebrow__icon">
                      <QuizIcon name={quiz.icon} size={16} />
                    </span>
                    Quiz
                  </div>

                  <span
                    className={`quiz-details-visibility quiz-details-visibility--${quiz.visibility}`}
                  >
                    {quiz.visibility === "public" ? (
                      <Globe2 size={14} strokeWidth={2} aria-hidden="true" />
                    ) : (
                      <Link2 size={14} strokeWidth={2} aria-hidden="true" />
                    )}

                    {quiz.visibility === "public" ? "Public" : "Unlisted"}
                  </span>
                </div>

                <h1>{quiz.title}</h1>

                <p className="quiz-details-description">
                  {quiz.description || "No description has been added for this quiz yet."}
                </p>

                {(quiz.category || quiz.tags.length > 0) && (
                  <div className="quiz-details-taxonomy">
                    {quiz.category && (
                      <span className="quiz-details-category">
                        {quiz.category}
                      </span>
                    )}

                    {quiz.tags.map((tag) => (
                      <span
                        key={tag}
                        className="quiz-details-tag"
                      >
                        #{tag}
                      </span>
                    ))}
                  </div>
                )}

                <div className="quiz-details-creator">
                <div
                    className="quiz-details-creator__avatar"
                    aria-hidden="true"
                >
                    <CircleUserRound size={22} />
                </div>

                <div>
                    <span>Created by</span>
                    <strong>{quiz.creator_name}</strong>
                </div>
                </div>
            </div>

            <div className="quiz-details-hero__actions">
                <Button
                size="lg"
                onClick={() => navigate(`/quizzes/${quiz.id}/take`)}
                disabled={quiz.question_count === 0}
                >
                <Play size={18} fill="currentColor" aria-hidden="true" />
                Start Quiz
                <ArrowRight size={18} aria-hidden="true" />
                </Button>

                <Button
                variant="secondary"
                size="lg"
                onClick={() => void handleShare()}
                >
                <Share2 size={17} aria-hidden="true" />
                {copied ? "Link copied!" : "Copy quiz link"}
                </Button>

                {quiz.question_count === 0 && (
                <p className="quiz-details-empty-note">
                    This quiz does not have any questions yet.
                </p>
                )}
            </div>
            </section>

        <section
          className="quiz-details-info"
          aria-label="Quiz information"
        >
          <div className="quiz-details-info__item">
            <div className="quiz-details-info__icon">
              <FileQuestion size={20} aria-hidden="true" />
            </div>

            <div>
              <span>Questions</span>
              <strong>{quiz.question_count}</strong>
            </div>
          </div>

          <div className="quiz-details-info__item">
            <div className="quiz-details-info__icon">
              <CalendarDays size={20} aria-hidden="true" />
            </div>

            <div>
              <span>Created</span>
              <strong>{formatDate(quiz.created_at)}</strong>
            </div>
          </div>

          <div className="quiz-details-info__item">
            <div className="quiz-details-info__icon">
              <Clock3 size={20} aria-hidden="true" />
            </div>

            <div>
              <span>Last updated</span>
              <strong>{formatDate(quiz.updated_at)}</strong>
            </div>
          </div>
        </section>

        {isOwner && (
          <section className="quiz-details-owner">
            <div>
              <span className="quiz-details-owner__label">
                Your quiz
              </span>
              <h2>Want to make a change?</h2>
              <p>
                Update the quiz details, questions, choices, or correct
                answers from the editor.
              </p>
            </div>

            <Button
              variant="secondary"
              onClick={() => navigate(`/quizzes/edit/${quiz.id}`)}
            >
              <Pencil size={17} aria-hidden="true" />
              Edit Quiz
            </Button>
          </section>
        )}
      </div>
    </div>
  );
}

export default QuizDetailsPage;