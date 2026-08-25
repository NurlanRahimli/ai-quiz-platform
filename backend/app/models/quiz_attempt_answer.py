import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.answer_choice import AnswerChoice
    from app.models.question import Question
    from app.models.quiz_attempt import QuizAttempt


class QuizAttemptAnswer(Base):
    __tablename__ = "quiz_attempt_answers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quiz_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    selected_choice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("answer_choices.id", ondelete="SET NULL"),
        nullable=True,
    )

    text_answer: Mapped[str | None] = mapped_column(
        String(10000),
        nullable=True,
    )

    ai_explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    whiteboard_image_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    ai_is_correct: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    attempt: Mapped["QuizAttempt"] = relationship(
        back_populates="answers",
    )

    question: Mapped["Question"] = relationship()

    selected_choice: Mapped["AnswerChoice | None"] = relationship()