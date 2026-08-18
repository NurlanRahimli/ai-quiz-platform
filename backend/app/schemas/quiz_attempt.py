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