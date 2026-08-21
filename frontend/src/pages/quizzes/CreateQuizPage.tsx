import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import axios from "axios";
import {
  ArrowLeft,
  Calculator,
  Check,
  FileQuestion,
  Info,
  ListChecks,
  PenLine,
  Plus,
  Sparkles,
  Trash2,
  X,
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

type NewQuestionType =
  | "multiple_choice"
  | "written_answer"
  | "math_work";

type NewQuestionChoice = {
  id: string;
  text: string;
  is_correct: boolean;
};

type CreateQuizDraft = {
  form: QuizForm;
  questions: DraftQuestion[];
  isAddingQuestion: boolean;
  newQuestionType: NewQuestionType;
  newQuestionText: string;
  newExpectedAnswer: string;
  newQuestionChoices: NewQuestionChoice[];
};

const CREATE_QUIZ_DRAFT_KEY = "create-quiz-draft";

const defaultChoices: NewQuestionChoice[] = [
  {
    id: "choice-1",
    text: "",
    is_correct: true,
  },
  {
    id: "choice-2",
    text: "",
    is_correct: false,
  },
];

const loadCreateQuizDraft = (): CreateQuizDraft | null => {
  const savedDraft = localStorage.getItem(CREATE_QUIZ_DRAFT_KEY);

  if (!savedDraft) {
    return null;
  }

  try {
    return JSON.parse(savedDraft) as CreateQuizDraft;
  } catch {
    localStorage.removeItem(CREATE_QUIZ_DRAFT_KEY);
    return null;
  }
};

type DraftQuestion = {
  id: string;
  question_type: NewQuestionType;
  text: string;
  expected_answer: string;
  choices: NewQuestionChoice[];
};


function CreateQuizPage() {
  const navigate = useNavigate();
  const [initialDraft] = useState(loadCreateQuizDraft);

  const [form, setForm] = useState<QuizForm>(
    initialDraft?.form ?? {
      title: "",
      description: "",
    },
  );

  const [errors, setErrors] = useState<QuizErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [questions, setQuestions] = useState<DraftQuestion[]>(
    initialDraft?.questions ?? [],
  );
  const [isAddingQuestion, setIsAddingQuestion] = useState(
    initialDraft?.isAddingQuestion ?? false,
  );

  const [newQuestionType, setNewQuestionType] =
    useState<NewQuestionType>(
      initialDraft?.newQuestionType ?? "multiple_choice",
    );

  const [newQuestionText, setNewQuestionText] = useState(
    initialDraft?.newQuestionText ?? "",
  );
  const [newExpectedAnswer, setNewExpectedAnswer] = useState(
    initialDraft?.newExpectedAnswer ?? "",
  );

  const [newQuestionChoices, setNewQuestionChoices] = useState<
    NewQuestionChoice[]
  >(
    initialDraft &&
      Array.isArray(initialDraft.newQuestionChoices) &&
      initialDraft.newQuestionChoices.length >= 2
      ? initialDraft.newQuestionChoices
      : defaultChoices,
  );

  const [newQuestionError, setNewQuestionError] = useState("");


  useEffect(() => {
    const draft: CreateQuizDraft = {
      form,
      questions,
      isAddingQuestion,
      newQuestionType,
      newQuestionText,
      newExpectedAnswer,
      newQuestionChoices,
    };

    localStorage.setItem(
      CREATE_QUIZ_DRAFT_KEY,
      JSON.stringify(draft),
    );
  }, [
    form,
    questions,
    isAddingQuestion,
    newQuestionType,
    newQuestionText,
    newExpectedAnswer,
    newQuestionChoices,
  ]);


  const resetNewQuestion = () => {
    setIsAddingQuestion(false);
    setNewQuestionType("multiple_choice");
    setNewQuestionText("");
    setNewExpectedAnswer("");
    setNewQuestionChoices(defaultChoices);
    setNewQuestionError("");
  };

  const updateNewChoiceText = (choiceId: string, text: string) => {
    setNewQuestionChoices((current) =>
      current.map((choice) =>
        choice.id === choiceId
          ? {
            ...choice,
            text,
          }
          : choice,
      ),
    );

    setNewQuestionError("");
  };

  const selectNewCorrectChoice = (choiceId: string) => {
    setNewQuestionChoices((current) =>
      current.map((choice) => ({
        ...choice,
        is_correct: choice.id === choiceId,
      })),
    );

    setNewQuestionError("");
  };

  const addNewChoice = () => {
    if (newQuestionChoices.length >= 8) {
      return;
    }

    setNewQuestionChoices((current) => [
      ...current,
      {
        id: crypto.randomUUID(),
        text: "",
        is_correct: false,
      },
    ]);

    setNewQuestionError("");
  };

  const removeNewChoice = (choiceId: string) => {
    if (newQuestionChoices.length <= 2) {
      return;
    }

    setNewQuestionChoices((current) => {
      const choiceToRemove = current.find(
        (choice) => choice.id === choiceId,
      );

      const remaining = current.filter(
        (choice) => choice.id !== choiceId,
      );

      if (choiceToRemove?.is_correct && remaining.length > 0) {
        return remaining.map((choice, index) => ({
          ...choice,
          is_correct: index === 0,
        }));
      }

      return remaining;
    });

    setNewQuestionError("");
  };

  const addQuestion = () => {
    const trimmedText = newQuestionText.trim();

    if (!trimmedText) {
      setNewQuestionError("Question text is required.");
      return;
    }

    if (newQuestionType === "multiple_choice") {
      const trimmedChoices = newQuestionChoices.map((choice) => ({
        ...choice,
        text: choice.text.trim(),
      }));

      if (trimmedChoices.some((choice) => !choice.text)) {
        setNewQuestionError("Every answer choice needs text.");
        return;
      }

      if (!trimmedChoices.some((choice) => choice.is_correct)) {
        setNewQuestionError("Select the correct answer.");
        return;
      }

      setQuestions((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          question_type: newQuestionType,
          text: trimmedText,
          expected_answer: "",
          choices: trimmedChoices,
        },
      ]);

      resetNewQuestion();
      return;
    }

    if (
      newQuestionType === "math_work" &&
      !newExpectedAnswer.trim()
    ) {
      setNewQuestionError(
        "Expected answer is required for a math question.",
      );
      return;
    }

    setQuestions((current) => [
      ...current,
      {
        id: crypto.randomUUID(),
        question_type: newQuestionType,
        text: trimmedText,
        expected_answer:
          newQuestionType === "math_work"
            ? newExpectedAnswer.trim()
            : "",
        choices: [],
      },
    ]);

    resetNewQuestion();
  };

  const deleteDraftQuestion = (questionId: string) => {
    setQuestions((current) =>
      current.filter((question) => question.id !== questionId),
    );
  };

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

    if (questions.length === 0) {
      nextErrors.form =
        "Add at least one question before creating the quiz.";
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

      const quizId = response.data.id;

      for (const question of questions) {
        if (question.question_type === "multiple_choice") {
          await apiClient.post(`/quizzes/${quizId}/questions`, {
            text: question.text,
            choices: question.choices.map((choice) => ({
              text: choice.text,
              is_correct: choice.is_correct,
            })),
          });

          continue;
        }

        if (question.question_type === "written_answer") {
          await apiClient.post(`/quizzes/${quizId}/questions/written`, {
            text: question.text,
          });

          continue;
        }

        await apiClient.post(`/quizzes/${quizId}/questions/math-work`, {
          text: question.text,
          expected_answer: question.expected_answer,
        });
      }

      localStorage.removeItem(CREATE_QUIZ_DRAFT_KEY);

      navigate("/dashboard", {
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
              Add your quiz details and build your questions before creating
              the quiz.
            </p>
          </div>
        </div>
      </header>

      <div className="create-quiz-page__layout">
        <div className="create-quiz-page__main">
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
                  Create quiz
                </Button>
              </div>
            </form>
          </Card>

          <section className="create-quiz-questions">
            <div className="create-quiz-questions__header">
              <div>
                <h2>Questions</h2>
                <p>
                  {questions.length === 0
                    ? "Add your first question to this quiz."
                    : `${questions.length} ${questions.length === 1 ? "question" : "questions"
                    } added`}
                </p>
              </div>

              {!isAddingQuestion && (
                <Button
                  type="button"
                  onClick={() => {
                    setIsAddingQuestion(true);
                    setNewQuestionError("");
                  }}
                >
                  <Plus size={17} />
                  Add question
                </Button>
              )}
            </div>

            {questions.length > 0 && (
              <div className="create-quiz-question-list">
                {questions.map((question, index) => (
                  <article
                    className="create-quiz-question-card"
                    key={question.id}
                  >
                    <div className="create-quiz-question-card__content">
                      <div className="create-quiz-question-card__heading">
                        <span>{index + 1}</span>

                        <div>
                          <strong>{question.text}</strong>
                          <small>
                            {question.question_type === "multiple_choice"
                              ? "Multiple choice"
                              : question.question_type === "written_answer"
                                ? "Written answer"
                                : "Math work"}
                          </small>
                        </div>
                      </div>

                      <button
                        type="button"
                        className="create-quiz-question-card__delete"
                        aria-label={`Delete question ${index + 1}`}
                        onClick={() => deleteDraftQuestion(question.id)}
                      >
                        <Trash2 size={17} />
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            )}

            {questions.length === 0 && !isAddingQuestion && (
              <div className="create-quiz-questions__empty">
                <FileQuestion size={28} aria-hidden="true" />
                <strong>No questions yet</strong>
                <p>Add a question to start building your quiz.</p>
              </div>
            )}

            {isAddingQuestion && (
              <div className="new-question-card">
                <div className="new-question-card__header">
                  <div>
                    <span className="new-question-card__eyebrow">
                      <Plus size={14} />
                      New question
                    </span>

                    <h3>Add a question</h3>
                    <p>
                      Choose the question type and enter the question
                      details.
                    </p>
                  </div>

                  <button
                    type="button"
                    className="new-question-card__close"
                    onClick={resetNewQuestion}
                    aria-label="Close question builder"
                  >
                    <X size={18} />
                  </button>
                </div>

                {newQuestionError && (
                  <div className="create-quiz-form__error" role="alert">
                    <Info size={18} />
                    <span>{newQuestionError}</span>
                  </div>
                )}

                <div className="new-question-type">
                  <span className="new-question-type__label">
                    Question type
                  </span>

                  <div className="new-question-type__options">
                    <button
                      type="button"
                      className={`new-question-type__option ${newQuestionType === "multiple_choice"
                        ? "new-question-type__option--active"
                        : ""
                        }`}
                      onClick={() =>
                        setNewQuestionType("multiple_choice")
                      }
                    >
                      <ListChecks size={19} />

                      <span>
                        <strong>Multiple choice</strong>
                        <small>Choose one correct answer</small>
                      </span>

                      {newQuestionType === "multiple_choice" && (
                        <Check
                          className="new-question-type__check"
                          size={17}
                        />
                      )}
                    </button>

                    <button
                      type="button"
                      className={`new-question-type__option ${newQuestionType === "written_answer"
                        ? "new-question-type__option--active"
                        : ""
                        }`}
                      onClick={() =>
                        setNewQuestionType("written_answer")
                      }
                    >
                      <PenLine size={19} />

                      <span>
                        <strong>Written answer</strong>
                        <small>Student writes a response</small>
                      </span>

                      {newQuestionType === "written_answer" && (
                        <Check
                          className="new-question-type__check"
                          size={17}
                        />
                      )}
                    </button>

                    <button
                      type="button"
                      className={`new-question-type__option ${newQuestionType === "math_work"
                        ? "new-question-type__option--active"
                        : ""
                        }`}
                      onClick={() => setNewQuestionType("math_work")}
                    >
                      <Calculator size={19} />

                      <span>
                        <strong>Math work</strong>
                        <small>Show work and submit an answer</small>
                      </span>

                      {newQuestionType === "math_work" && (
                        <Check
                          className="new-question-type__check"
                          size={17}
                        />
                      )}
                    </button>
                  </div>
                </div>

                <div className="new-question-field">
                  <label htmlFor="new-question-text">Question</label>

                  <textarea
                    id="new-question-text"
                    value={newQuestionText}
                    maxLength={2000}
                    placeholder={
                      newQuestionType === "math_work"
                        ? "e.g. Solve for x: 2x + 6 = 18"
                        : newQuestionType === "written_answer"
                          ? "e.g. Explain what a Python function does."
                          : "e.g. Which keyword defines a function in Python?"
                    }
                    onChange={(event) => {
                      setNewQuestionText(event.target.value);
                      setNewQuestionError("");
                    }}
                  />

                  <span className="new-question-field__count">
                    {newQuestionText.length}/2000
                  </span>
                </div>

                {newQuestionType === "multiple_choice" && (
                  <div className="new-question-choices">
                    <div className="new-question-choices__heading">
                      <div>
                        <h4>Answer choices</h4>
                        <p>Select the correct answer.</p>
                      </div>

                      <Button
                        type="button"
                        variant="secondary"
                        disabled={newQuestionChoices.length >= 8}
                        onClick={addNewChoice}
                      >
                        <Plus size={16} />
                        Add choice
                      </Button>
                    </div>

                    <div className="new-question-choices__list">
                      {newQuestionChoices.map((choice, index) => (
                        <div
                          className={`new-question-choice ${choice.is_correct
                            ? "new-question-choice--correct"
                            : ""
                            }`}
                          key={choice.id}
                        >
                          <label className="new-question-choice__correct">
                            <input
                              type="radio"
                              name="new-correct-choice"
                              checked={choice.is_correct}
                              onChange={() =>
                                selectNewCorrectChoice(choice.id)
                              }
                            />

                            <span className="new-question-choice__number">
                              {index + 1}
                            </span>
                          </label>

                          <input
                            className="new-question-choice__input"
                            type="text"
                            maxLength={1000}
                            placeholder={`Choice ${index + 1}`}
                            value={choice.text}
                            onChange={(event) =>
                              updateNewChoiceText(
                                choice.id,
                                event.target.value,
                              )
                            }
                          />

                          <button
                            type="button"
                            className="new-question-choice__remove"
                            disabled={newQuestionChoices.length <= 2}
                            onClick={() => removeNewChoice(choice.id)}
                            aria-label={`Remove choice ${index + 1}`}
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {newQuestionType === "written_answer" && (
                  <div className="new-question-info">
                    <Info size={18} />

                    <p>
                      Written answers are not automatically graded and can
                      be reviewed after the quiz is submitted.
                    </p>
                  </div>
                )}

                {newQuestionType === "math_work" && (
                  <div className="new-question-field">
                    <label htmlFor="new-expected-answer">
                      Expected answer
                    </label>

                    <input
                      id="new-expected-answer"
                      type="text"
                      maxLength={1000}
                      value={newExpectedAnswer}
                      placeholder="e.g. x = 6"
                      onChange={(event) => {
                        setNewExpectedAnswer(event.target.value);
                        setNewQuestionError("");
                      }}
                    />

                    <small className="new-question-field__help">
                      This answer will be used to automatically grade the
                      student's final answer.
                    </small>
                  </div>
                )}

                <div className="new-question-card__actions">
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={resetNewQuestion}
                  >
                    Cancel
                  </Button>

                  <Button
                    type="button"
                    onClick={addQuestion}
                  >
                    <Plus size={17} />
                    Add question
                  </Button>
                </div>
              </div>
            )}
          </section>
        </div>

        <aside className="create-quiz-page__aside">
          <Card
            padding="md"
            className="create-quiz-tip"
          >
            <div className="create-quiz-page__info-card">
              <div className="create-quiz-page__info-icon">
                <Sparkles size={18} aria-hidden="true" />
              </div>

              <div>
                <strong>Build your quiz</strong>
                <p>
                  Add as many questions as you need, then create the quiz
                  when you're ready.
                </p>
              </div>
            </div>
          </Card>
        </aside>
      </div>
    </div>
  );
}

export default CreateQuizPage;