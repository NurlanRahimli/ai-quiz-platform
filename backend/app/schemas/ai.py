from pydantic import BaseModel, Field


class QuizAIContext(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    questions: list[str] = Field(min_length=1, max_length=30)


class CategorySuggestionResponse(BaseModel):
    category: str


class TagSuggestionResponse(BaseModel):
    tags: list[str] = Field(max_length=3)