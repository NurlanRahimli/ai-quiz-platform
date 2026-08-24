from typing import Literal

from pydantic import BaseModel, Field, model_validator


class QuizAIContext(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    questions: list[str] = Field(min_length=1, max_length=30)


class CategorySuggestionResponse(BaseModel):
    category: str


class TagSuggestionResponse(BaseModel):
    tags: list[str] = Field(max_length=3)


class ImportedAnswerChoice(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    is_correct: bool = False


class ImportedQuestion(BaseModel):
    question_type: Literal[
        "multiple_choice",
        "written_answer",
        "math_work",
    ]

    text: str = Field(min_length=1, max_length=2000)

    choices: list[ImportedAnswerChoice] = Field(
        default_factory=list,
        max_length=8,
    )

    expected_answer: str | None = Field(
        default=None,
        max_length=1000,
    )

    answer_source: Literal[
        "document",
        "ai_inferred",
        "unavailable",
    ]

    needs_review: bool = False

    review_reason: str | None = Field(
        default=None,
        max_length=500,
    )

    @model_validator(mode="after")
    def validate_question(self):
        if self.question_type == "multiple_choice":
            if len(self.choices) < 2:
                raise ValueError(
                    "Multiple-choice questions require at least two choices"
                )

            correct_count = sum(
                choice.is_correct for choice in self.choices
            )

            if self.answer_source == "unavailable":
                if correct_count != 0:
                    raise ValueError(
                        "Unavailable answers cannot have a correct choice"
                    )
            elif correct_count != 1:
                raise ValueError(
                    "Multiple-choice questions require exactly one correct choice"
                )

            if self.expected_answer is not None:
                raise ValueError(
                    "Multiple-choice questions cannot have an expected answer"
                )

        else:
            if self.choices:
                raise ValueError(
                    "Written and math questions cannot have answer choices"
                )

            if (
                self.answer_source != "unavailable"
                and not self.expected_answer
            ):
                raise ValueError(
                    "Written and math questions require an expected answer"
                )

        if self.answer_source == "unavailable":
            if not self.needs_review:
                raise ValueError(
                    "Unavailable answers must be marked for review"
                )

            if not self.review_reason:
                raise ValueError(
                    "Questions needing review require a review reason"
                )

        return self


class ExtractedQuiz(BaseModel):
    title: str | None = Field(default=None, max_length=255)

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    category: str = Field(min_length=1, max_length=100)

    tags: list[str] = Field(
        default_factory=list,
        max_length=3,
    )

    questions: list[ImportedQuestion] = Field(
        min_length=1,
    )


class ImportedQuiz(BaseModel):
    title: str | None = Field(default=None, max_length=255)

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    category: str = Field(min_length=1, max_length=100)

    tags: list[str] = Field(
        default_factory=list,
        max_length=3,
    )

    questions: list[ImportedQuestion] = Field(
        min_length=1,
        max_length=30,
    )