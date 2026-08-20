import { useEffect, useState } from "react"
import type { FormEvent } from "react"
import axios from "axios"
import { useNavigate, useParams } from "react-router-dom"

import MathWhiteboard from "../../components/quizzes/MathWhiteboard"

import apiClient from "../../api/client"
import "../../styles/pages/quizzes/TakeQuizPage.css"

type AnswerChoice = {
  id: string
  text: string
  position: number
}

type Question = {
  id: string
  text: string
  question_type: string
  position: number
  answer_choices: AnswerChoice[]
}

type Quiz = {
  id: string
  title: string
  description: string | null
  questions: Question[]
}

type Answers = Record<string, string>

function TakeQuizPage() {
  const { quizId } = useParams()
  const navigate = useNavigate()

  const [quiz, setQuiz] = useState<Quiz | null>(null)
  const [answers, setAnswers] = useState<Answers>({})
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    const loadQuiz = async () => {
      if (!quizId) {
        setError("Quiz not found")
        setIsLoading(false)
        return
      }

      try {
        const response = await apiClient.get<Quiz>(
          `/quizzes/${quizId}/take`,
        )

        setQuiz(response.data)
      } catch (requestError) {
        if (
          axios.isAxiosError(requestError) &&
          requestError.response?.status === 404
        ) {
          setError("Quiz not found")
        } else {
          setError("Unable to load quiz")
        }
      } finally {
        setIsLoading(false)
      }
    }

    void loadQuiz()
  }, [quizId])

  const updateAnswer = (questionId: string, value: string) => {
    setAnswers((current) => ({
      ...current,
      [questionId]: value,
    }))
  }


  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (!quiz || !quizId) {
      return
    }

    const unansweredQuestion = quiz.questions.find(
      (question) => !answers[question.id]?.trim(),
    )

    if (unansweredQuestion) {
      setError("Please answer every question before submitting.")
      return
    }

    const submittedAnswers = quiz.questions.map((question) => {
      if (question.question_type === "multiple_choice") {
        return {
          question_id: question.id,
          selected_choice_id: answers[question.id],
          text_answer: null,
        }
      }

      return {
        question_id: question.id,
        selected_choice_id: null,
        text_answer: answers[question.id].trim(),
      }
    })

    setIsSubmitting(true)
    setError("")

    try {
      const response = await apiClient.post(
        `/quizzes/${quizId}/attempts`,
        {
          answers: submittedAnswers,
        },
      )

      navigate(
        `/quizzes/${quizId}/attempts/${response.data.id}/results`,
        { replace: true },
      )
    } catch (requestError) {
      if (axios.isAxiosError(requestError)) {
        const detail = requestError.response?.data?.detail

        setError(
          typeof detail === "string"
            ? detail
            : "Unable to submit quiz.",
        )
      } else {
        setError("Unable to submit quiz.")
      }
    } finally {
      setIsSubmitting(false)
    }
  }



  if (isLoading) {
    return <main>Loading quiz...</main>
  }

  if (error || !quiz) {
    return <main>{error || "Quiz not found"}</main>
  }

  return (
    <main className="take-quiz-page">
      <div className="take-quiz-navigation">
        <button
          className="take-quiz-back-button"
          type="button"
          onClick={() => navigate("/dashboard")}
        >
          ← Back to dashboard
        </button>

        <button
          className="take-quiz-history-button"
          type="button"
          onClick={() => navigate(`/quizzes/${quizId}/history`)}
        >
          View attempt history
        </button>
      </div>

      <header>
        <p>Quiz</p>
        <h1>{quiz.title}</h1>

        {quiz.description && <p>{quiz.description}</p>}

        <p>
          {quiz.questions.length}{" "}
          {quiz.questions.length === 1 ? "question" : "questions"}
        </p>
      </header>

      {error && (
        <p role="alert">
          {error}
        </p>
      )}

      {quiz.questions.length === 0 ? (
        <p>This quiz doesn't have any questions yet.</p>
      ) : (
        <form onSubmit={handleSubmit}>
          {quiz.questions.map((question, index) => (
            <section
              className="take-question"
              key={question.id}
            >
              <h2>
                {index + 1}. {question.text}
              </h2>

              {question.question_type === "multiple_choice" && (
                <div>
                  {question.answer_choices.map((choice) => (
                    <label key={choice.id}>
                      <input
                        type="radio"
                        name={question.id}
                        value={choice.id}
                        checked={
                          answers[question.id] === choice.id
                        }
                        onChange={(event) =>
                          updateAnswer(
                            question.id,
                            event.target.value,
                          )
                        }
                      />

                      {choice.text}
                    </label>
                  ))}
                </div>
              )}

              {question.question_type === "written_answer" && (
                <textarea
                  placeholder="Type your answer..."
                  value={answers[question.id] ?? ""}
                  onChange={(event) =>
                    updateAnswer(
                      question.id,
                      event.target.value,
                    )
                  }
                />
              )}

              {question.question_type === "math_work" && (
                <div className="math-work-answer">
                  <MathWhiteboard />

                  <div className="math-final-answer">
                    <label htmlFor={`math-answer-${question.id}`}>
                      Final answer
                    </label>

                    <input
                      id={`math-answer-${question.id}`}
                      type="text"
                      placeholder="Enter your final answer..."
                      value={answers[question.id] ?? ""}
                      onChange={(event) =>
                        updateAnswer(
                          question.id,
                          event.target.value,
                        )
                      }
                    />

                    <p>
                      Your final answer will be used for grading.
                    </p>
                  </div>
                </div>
              )}
            </section>
          ))}

          <button
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting ? "Submitting..." : "Submit quiz"}
          </button>
        </form>
      )}
    </main>
  )
}

export default TakeQuizPage