import { useState } from "react";
import type { FormEvent } from "react";
import axios from "axios";
import {
  ArrowLeft,
  FileQuestion,
  Info,
  Sparkles,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import apiClient from "../../api/client";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import Input from "../../components/ui/Input";

import "../../styles/pages/quizzes/CreateQuizPage.css";

type QuizForm = {
  title: string;
  description: string;
};

type QuizErrors = Partial<Record<keyof QuizForm | "form", string>>;

type QuizResponse = {
  id: string;
  owner_id: string;
  title: string;
  description: string | null;
  created_at: string;
  updated_at: string;
};

function CreateQuizPage() {
  const navigate = useNavigate();

  const [form, setForm] = useState<QuizForm>({
    title: "",
    description: "",
  });

  const [errors, setErrors] = useState<QuizErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const updateField = (field: keyof QuizForm, value: string) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));

    setErrors((current) => ({
      ...current,
      [field]: undefined,
      form: undefined,
    }));
  };

  const validateForm = () => {
    const nextErrors: QuizErrors = {};

    if (!form.title.trim()) {
      nextErrors.title = "Quiz title is required";
    }

    if (form.title.trim().length > 255) {
      nextErrors.title = "Quiz title must be 255 characters or fewer";
    }

    if (form.description.length > 1000) {
      nextErrors.description =
        "Description must be 1000 characters or fewer";
    }

    setErrors(nextErrors);

    return Object.keys(nextErrors).length === 0;
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await apiClient.post<QuizResponse>("/quizzes", {
        title: form.title.trim(),
        description: form.description.trim() || null,
      });

      navigate(`/quizzes/${response.data.id}`, {
        replace: true,
      });
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail;

        setErrors((current) => ({
          ...current,
          form:
            typeof detail === "string"
              ? detail
              : "Unable to create quiz",
        }));
      } else {
        setErrors((current) => ({
          ...current,
          form: "Something went wrong. Please try again.",
        }));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="create-quiz-page">
      <header className="create-quiz-page__header">
        <button
          type="button"
          className="create-quiz-page__back"
          onClick={() => navigate("/dashboard")}
        >
          <ArrowLeft size={18} strokeWidth={2} aria-hidden="true" />
          <span>Dashboard</span>
        </button>

        <div className="create-quiz-page__heading">
          <div>
            <p className="create-quiz-page__eyebrow">
              <Sparkles size={15} strokeWidth={2} aria-hidden="true" />
              New quiz
            </p>

            <h1>Create a quiz</h1>

            <p className="create-quiz-page__description">
              Start with the basics. You can add and configure your
              questions after creating the quiz.
            </p>
          </div>
        </div>
      </header>

      <div className="create-quiz-page__layout">
        <Card
          padding="lg"
          className="create-quiz-form-card"
        >
          <div className="create-quiz-form-card__header">
            <div className="create-quiz-form-card__icon" aria-hidden="true">
              <FileQuestion size={21} strokeWidth={1.9} />
            </div>

            <div>
              <h2>Quiz details</h2>
              <p>Give your quiz a clear name and description.</p>
            </div>
          </div>

          {errors.form && (
            <div
              className="create-quiz-form__error"
              role="alert"
            >
              <Info size={18} strokeWidth={2} aria-hidden="true" />
              <span>{errors.form}</span>
            </div>
          )}

          <form
            className="create-quiz-form"
            onSubmit={handleSubmit}
            noValidate
          >
            <Input
              id="title"
              name="title"
              type="text"
              label="Quiz title"
              placeholder="e.g. Python Fundamentals"
              maxLength={255}
              value={form.title}
              error={errors.title}
              disabled={isSubmitting}
              onChange={(event) =>
                updateField("title", event.target.value)
              }
            />

            <div className="create-quiz-form__field">
              <div className="create-quiz-form__label-row">
                <label htmlFor="description">
                  Description
                </label>

                <span>Optional</span>
              </div>

              <textarea
                id="description"
                name="description"
                placeholder="What is this quiz about?"
                maxLength={1000}
                value={form.description}
                disabled={isSubmitting}
                aria-invalid={Boolean(errors.description)}
                aria-describedby={
                  errors.description
                    ? "description-error"
                    : "description-count"
                }
                onChange={(event) =>
                  updateField("description", event.target.value)
                }
              />

              <div className="create-quiz-form__field-footer">
                <div>
                  {errors.description && (
                    <span
                      id="description-error"
                      className="create-quiz-form__field-error"
                    >
                      {errors.description}
                    </span>
                  )}
                </div>

                <span
                  id="description-count"
                  className="create-quiz-form__character-count"
                >
                  {form.description.length}/1000
                </span>
              </div>
            </div>

            <div className="create-quiz-form__actions">
              <Button
                type="button"
                variant="secondary"
                size="lg"
                disabled={isSubmitting}
                onClick={() => navigate("/dashboard")}
              >
                Cancel
              </Button>

              <Button
                type="submit"
                size="lg"
                loading={isSubmitting}
                className="create-quiz-form__submit"
              >
                Create & continue
              </Button>
            </div>
          </form>
        </Card>

        <aside className="create-quiz-page__aside">
          <Card
            padding="md"
            className="create-quiz-tip"
          >
            <div className="create-quiz-tip__icon" aria-hidden="true">
              <Sparkles size={18} strokeWidth={2} />
            </div>

            <div>
              <h2>What happens next?</h2>

              <p>
                After creating your quiz, you'll continue to the quiz
                editor where you can add questions and prepare it for
                taking.
              </p>
            </div>
          </Card>
        </aside>
      </div>
    </div>
  );
}

export default CreateQuizPage;