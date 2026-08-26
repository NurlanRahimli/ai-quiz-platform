from typing import Literal

from pydantic import BaseModel, Field


class ChatbotMessageRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=2000,
    )


class ChatbotQueryResponse(BaseModel):
    type: Literal["text", "table"]
    message: str
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, object]] = Field(default_factory=list)
    total_rows: int = 0

class ChatbotReportInsight(BaseModel):
    status: Literal[
        "positive",
        "warning",
        "negative",
        "neutral",
    ]
    icon: str
    label: str
    value: str
    detail: str | None = None


class ChatbotReportResponse(BaseModel):
    type: Literal["report"] = "report"
    title: str
    message: str
    insights: list[ChatbotReportInsight]

