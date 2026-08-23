from pydantic import BaseModel
import uuid
from datetime import datetime


class DashboardStats(BaseModel):
    total_quizzes: int
    average_score: float | None
    quizzes_taken: int

class DashboardRecentQuiz(BaseModel):
    quiz_id: uuid.UUID
    quiz_title: str
    quiz_category: str | None
    latest_attempt_id: uuid.UUID
    latest_submitted_at: datetime
    score_percentage: float | None

class DashboardResponse(BaseModel):
    stats: DashboardStats
    recent_quizzes: list[DashboardRecentQuiz]
    performance: list[DashboardPerformancePoint]
    top_categories: list[DashboardCategoryPerformance]

class DashboardPerformancePoint(BaseModel):
    submitted_at: datetime
    score: float
    average_score: float

class DashboardCategoryPerformance(BaseModel):
    category: str
    average_score: float | None
    attempt_count: int
