import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.question import QuestionResponse

from typing import Literal

class QuizCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    category: str | None = Field(default=None, max_length=100)
    tags: list[str] = Field(default_factory=list, max_length=5)
    visibility: Literal["public", "unlisted"] = "unlisted"

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Quiz title cannot be empty")

        return value

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str]) -> list[str]:
        normalized_tags: list[str] = []

        for tag in value:
            normalized_tag = tag.strip()

            if not normalized_tag:
                continue

            if len(normalized_tag) > 50:
                raise ValueError("Each tag must be 50 characters or fewer")

            if normalized_tag.lower() not in {
                existing.lower() for existing in normalized_tags
            }:
                normalized_tags.append(normalized_tag)

        return normalized_tags


class QuizUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    visibility: Literal["public", "unlisted"] | None = None
    category: str | None = Field(default=None, max_length=100)
    tags: list[str] | None = Field(default=None, max_length=5)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.strip()

        if not value:
            raise ValueError("Quiz title cannot be empty")

        return value
    
    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None

        normalized_tags: list[str] = []

        for tag in value:
            normalized_tag = tag.strip()

            if not normalized_tag:
                continue

            if len(normalized_tag) > 50:
                raise ValueError("Each tag must be 50 characters or fewer")

            if normalized_tag.lower() not in {
                existing.lower() for existing in normalized_tags
            }:
                normalized_tags.append(normalized_tag)

        return normalized_tags


class QuizResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    category: str | None
    tags: list[str]
    visibility: Literal["public", "unlisted"]


class QuizListResponse(QuizResponse):
    creator_name: str


class QuizDetailResponse(QuizResponse):
    questions: list[QuestionResponse]


class QuizTakeAnswerChoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    text: str
    position: int


class QuizTakeQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    text: str
    question_type: str
    position: int
    answer_choices: list[QuizTakeAnswerChoiceResponse]


class QuizTakeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    questions: list[QuizTakeQuestionResponse]


class QuizLandingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    description: str | None
    visibility: Literal["public", "unlisted"]
    creator_name: str
    question_count: int
    category: str | None
    tags: list[str]
    created_at: datetime
    updated_at: datetime