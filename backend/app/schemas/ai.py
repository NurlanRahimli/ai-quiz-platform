from typing import Literal

from pydantic import BaseModel, Field, model_validator


class QuizAIContext(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    questions: list[str] = Field(min_length=1, max_length=30)


class QuizIconContext(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    category: str | None = Field(default=None, max_length=100)
    tags: list[str] = Field(default_factory=list, max_length=3)


class QuizIconSuggestionResponse(BaseModel):
    icon: str


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


class AnswerEvaluationResponse(BaseModel):
    is_correct: bool
    explanation: str = Field(
        min_length=1,
        max_length=4000,
    )


class IncorrectAnswerExplanationResponse(BaseModel):
    explanation: str = Field(
        min_length=1,
        max_length=4000,
    )


class MathAnswerEvaluationResponse(BaseModel):
    is_correct: bool
    explanation: str = Field(
        min_length=1,
        max_length=4000,
    )


class ChatbotQueryFiltersPlan(BaseModel):
    quiz_title: str | None = Field(
        default=None,
        max_length=255,
    )
    category: str | None = Field(
        default=None,
        max_length=100,
    )
    creator_name: str | None = Field(
        default=None,
        max_length=255,
    )
    date_from: str | None = None
    date_to: str | None = None


class ChatbotQueryPlan(BaseModel):
    metrics: list[
        Literal[
            "attempt_count",
            "quiz_count",
            "average_score",
        ]
    ] = Field(
        min_length=1,
        max_length=3,
    )
    group_by: Literal[
        "quiz",
        "category",
        "creator",
    ] | None = None
    filters: ChatbotQueryFiltersPlan = Field(
        default_factory=ChatbotQueryFiltersPlan,
    )
    sort_by: Literal[
        "attempt_count",
        "quiz_count",
        "average_score",
    ] | None = None
    sort_direction: Literal[
        "asc",
        "desc",
    ] = "desc"
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
    )

    @model_validator(mode="after")
    def validate_query_plan(self):
        if len(set(self.metrics)) != len(self.metrics):
            raise ValueError(
                "Chatbot query metrics must be unique"
            )

        if (
            self.sort_by is not None
            and self.sort_by not in self.metrics
        ):
            raise ValueError(
                "sort_by must be included in metrics"
            )

        return self

class ChatbotUserConnectionsPlan(BaseModel):

    direction: Literal[
        "followers",
        "following",
    ]

    operation: Literal[
        "count",
        "list",
    ]

    limit: int = Field(
        default=10,
        ge=1,
        le=50,
    )


class ChatbotCreatedQuizzesPlan(BaseModel):

    operation: Literal[
        "count",
        "list",
    ]

    visibility: Literal[
        "public",
        "unlisted",
    ] | None = None

    category: str | None = Field(
        default=None,
        max_length=100,
    )

    title_search: str | None = Field(
        default=None,
        max_length=255,
    )

    sort_direction: Literal[
        "asc",
        "desc",
    ] = "desc"

    limit: int = Field(
        default=10,
        ge=1,
        le=50,
    )


class ChatbotQuestionPerformancePlan(BaseModel):
    quiz_title: str | None = Field(
        default=None,
        max_length=255,
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
    )


class ChatbotStudyRecommendationPlan(BaseModel):

    quiz_title: str | None = Field(
        default=None,
        max_length=255,
    )

    limit: int = Field(
        default=5,
        ge=1,
        le=10,
    )


class ChatbotPerformanceTrendPlan(BaseModel):
    quiz_title: str | None = Field(
        default=None,
        max_length=255,
    )
    category: str | None = Field(
        default=None,
        max_length=100,
    )


class ChatbotAttemptComparisonPlan(BaseModel):
    quiz_title: str | None = Field(
        default=None,
        max_length=255,
    )
    category: str | None = Field(
        default=None,
        max_length=100,
    )
    limit: int = Field(
        default=3,
        ge=1,
        le=20,
    )


class ChatbotMonthlyReportPlan(BaseModel):
    period: Literal[
        "this_month",
        "last_month",
    ]


class ChatbotPlan(BaseModel):
    intent: Literal[
        "query",
        "monthly_report",
        "created_quizzes",
        "user_connections",
        "question_performance",
        "study_recommendation",
        "performance_trend",
        "attempt_comparison",
    ]
    query: ChatbotQueryPlan | None = None
    monthly_report: ChatbotMonthlyReportPlan | None = None
    created_quizzes: ChatbotCreatedQuizzesPlan | None = None
    user_connections: ChatbotUserConnectionsPlan | None = None
    question_performance: ChatbotQuestionPerformancePlan | None = None
    study_recommendation: ChatbotStudyRecommendationPlan | None = None
    performance_trend: ChatbotPerformanceTrendPlan | None = None
    attempt_comparison: ChatbotAttemptComparisonPlan | None = None

    @model_validator(mode="after")
    def validate_chatbot_plan(self):
        plans = {
            "query": self.query,
            "monthly_report": self.monthly_report,
            "created_quizzes": self.created_quizzes,
            "user_connections": self.user_connections,
            "question_performance": self.question_performance,
            "study_recommendation": self.study_recommendation,
            "performance_trend": self.performance_trend,
            "attempt_comparison": self.attempt_comparison,
        }

        selected_plan = plans[self.intent]

        if selected_plan is None:
            messages = {
                "query": "Query intent requires a query plan",
                "monthly_report": (
                    "Monthly report intent requires a report plan"
                ),
                "created_quizzes": (
                    "Created quizzes intent requires "
                    "a created quizzes plan"
                ),
                "user_connections": (
                    "User connections intent requires "
                    "a user connections plan"
                ),
                "question_performance": (
                    "Question performance intent requires "
                    "a performance plan"
                ),
                "study_recommendation": (
                    "Study recommendation intent requires "
                    "a recommendation plan"
                ),
                "performance_trend": (
                    "Performance trend intent requires a trend plan"
                ),
                "attempt_comparison": (
                    "Attempt comparison intent requires "
                    "a comparison plan"
                ),
            }
            raise ValueError(messages[self.intent])

        other_plans = [
            plan
            for intent, plan in plans.items()
            if intent != self.intent and plan is not None
        ]

        if other_plans:
            labels = {
                "query": "Query",
                "monthly_report": "Monthly report",
                "created_quizzes": "Created quizzes",
                "user_connections": "User connections",
                "question_performance": "Question performance",
                "study_recommendation": "Study recommendation",
                "performance_trend": "Performance trend",
                "attempt_comparison": "Attempt comparison",
            }
            raise ValueError(
                f"{labels[self.intent]} intent cannot include "
                "another intent plan"
            )

        return self

