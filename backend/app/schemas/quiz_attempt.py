import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class QuizAnswerSubmit(BaseModel):
    question_id: uuid.UUID
    selected_choice_id: uuid.UUID | None = None
    text_answer: str | None = None


class QuizAttemptSubmit(BaseModel):
    answers: list[QuizAnswerSubmit]


class QuizAttemptAnswerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_id: uuid.UUID
    selected_choice_id: uuid.UUID | None
    text_answer: str | None


class QuizAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    quiz_id: uuid.UUID
    user_id: uuid.UUID
    submitted_at: datetime
    answers: list[QuizAttemptAnswerResponse]

class QuizAttemptResultChoice(BaseModel):
    id: uuid.UUID
    text: str
    is_correct: bool
    was_selected: bool
    position: int

class QuizAttemptResultAnswer(BaseModel):
    question_id: uuid.UUID
    question_text: str
    question_type: str
    is_correct: bool | None
    submitted_answer: str
    correct_answer: str | None
    answer_choices: list[QuizAttemptResultChoice] = []


class QuizAttemptResultResponse(BaseModel):
    attempt_id: uuid.UUID
    quiz_id: uuid.UUID
    score: int
    gradable_questions: int
    total_questions: int
    answers: list[QuizAttemptResultAnswer]


class GuestQuizAttemptResultResponse(BaseModel):
    quiz_id: uuid.UUID
    score: int
    gradable_questions: int
    total_questions: int
    answers: list[QuizAttemptResultAnswer]


class QuizAttemptHistoryItem(BaseModel):
    attempt_id: uuid.UUID
    submitted_at: datetime
    score: int
    gradable_questions: int
    total_questions: int


class UserAttemptQuizItem(BaseModel):
    quiz_id: uuid.UUID
    quiz_title: str
    quiz_category: str | None
    latest_attempt_id: uuid.UUID
    latest_submitted_at: datetime
    latest_score: int
    latest_gradable_questions: int
    latest_total_questions: int
    attempt_count: int
    average_score: float | None


class UserAttemptQuizPage(BaseModel):
    quizzes: list[UserAttemptQuizItem]
    total: int
    page: int
    page_size: int
    total_pages: int