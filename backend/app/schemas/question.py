import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AnswerChoiceCreate(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    is_correct: bool = False

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Answer choice cannot be empty")

        return value


class AnswerChoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    text: str
    is_correct: bool
    position: int


class QuestionCreate(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    choices: list[AnswerChoiceCreate] = Field(min_length=2)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Question cannot be empty")

        return value

    @field_validator("choices")
    @classmethod
    def validate_choices(
        cls,
        choices: list[AnswerChoiceCreate],
    ) -> list[AnswerChoiceCreate]:
        correct_count = sum(choice.is_correct for choice in choices)

        if correct_count != 1:
            raise ValueError(
                "A multiple-choice question must have exactly one correct answer"
            )

        return choices


class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    quiz_id: uuid.UUID
    text: str
    question_type: str
    position: int
    answer_choices: list[AnswerChoiceResponse]