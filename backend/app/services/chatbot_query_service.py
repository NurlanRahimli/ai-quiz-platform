from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from app.services.chatbot_data_service import ChatbotAttemptRow


GroupField = Literal[
    "quiz",
    "category",
    "creator",
]

Metric = Literal[
    "attempt_count",
    "quiz_count",
    "average_score",
]

SortDirection = Literal[
    "asc",
    "desc",
]


@dataclass(frozen=True)
class ChatbotQueryFilters:
    quiz_title: str | None = None
    category: str | None = None
    creator_name: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


@dataclass(frozen=True)
class ChatbotQuery:
    metrics: tuple[Metric, ...]
    group_by: GroupField | None = None
    filters: ChatbotQueryFilters = ChatbotQueryFilters()
    sort_by: Metric | None = None
    sort_direction: SortDirection = "desc"
    limit: int = 20

    def __post_init__(self) -> None:
        if not self.metrics:
            raise ValueError("At least one metric is required")


@dataclass(frozen=True)
class ChatbotQueryResult:
    columns: list[str]
    rows: list[dict[str, object]]
    total_rows: int


def _matches_filters(
    row: ChatbotAttemptRow,
    filters: ChatbotQueryFilters,
) -> bool:
    if (
        filters.quiz_title is not None
        and filters.quiz_title.lower() not in row.quiz_title.lower()
    ):
        return False

    if (
        filters.category is not None
        and (
            row.category is None
            or filters.category.lower() != row.category.lower()
        )
    ):
        return False

    if (
        filters.creator_name is not None
        and filters.creator_name.lower() not in row.creator_name.lower()
    ):
        return False

    if (
        filters.date_from is not None
        and row.submitted_at < filters.date_from
    ):
        return False

    if (
        filters.date_to is not None
        and row.submitted_at > filters.date_to
    ):
        return False

    return True


def _group_key(
    row: ChatbotAttemptRow,
    group_by: GroupField,
) -> tuple[str, dict[str, object]]:
    if group_by == "quiz":
        return (
            str(row.quiz_id),
            {
                "quiz_id": str(row.quiz_id),
                "quiz_title": row.quiz_title,
                "creator_name": row.creator_name,
                "category": row.category,
            },
        )

    if group_by == "category":
        value = row.category or "Uncategorized"

        return (
            value.lower(),
            {
                "category": value,
            },
        )

    return (
        row.creator_name.lower(),
        {
            "creator_name": row.creator_name,
        },
    )


def _calculate_metric(
    rows: list[ChatbotAttemptRow],
    metric: Metric,
) -> int | float | None:
    if metric == "attempt_count":
        return len(rows)

    if metric == "quiz_count":
        return len({
            row.quiz_id
            for row in rows
        })

    scores = [
        row.score_percentage
        for row in rows
        if row.score_percentage is not None
    ]

    if not scores:
        return None

    return round(sum(scores) / len(scores), 2)


def execute_chatbot_query(
    rows: list[ChatbotAttemptRow],
    query: ChatbotQuery,
) -> ChatbotQueryResult:
    filtered_rows = [
        row
        for row in rows
        if _matches_filters(row, query.filters)
    ]

    if query.group_by is None:
        result_row = {
            metric: _calculate_metric(
                filtered_rows,
                metric,
            )
            for metric in query.metrics
        }

        return ChatbotQueryResult(
            columns=list(query.metrics),
            rows=[result_row],
            total_rows=1,
        )

    grouped: dict[
        str,
        tuple[
            dict[str, object],
            list[ChatbotAttemptRow],
        ],
    ] = {}

    for row in filtered_rows:
        key, identity = _group_key(
            row,
            query.group_by,
        )

        if key not in grouped:
            grouped[key] = (
                identity,
                [],
            )

        grouped[key][1].append(row)

    result_rows: list[dict[str, object]] = []

    for identity, group_rows in grouped.values():
        result_row = dict(identity)

        for metric in query.metrics:
            result_row[metric] = _calculate_metric(
                group_rows,
                metric,
            )

        result_rows.append(result_row)

    sort_metric = query.sort_by or query.metrics[0]

    if sort_metric not in query.metrics:
        raise ValueError(
            "sort_by must be included in metrics"
        )

    def sort_value(
        result_row: dict[str, object],
    ) -> tuple[bool, float]:
        value = result_row.get(sort_metric)

        if isinstance(value, (int, float)):
            return (False, float(value))

        return (True, 0.0)

    result_rows.sort(
        key=sort_value,
        reverse=query.sort_direction == "desc",
    )

    total_rows = len(result_rows)

    safe_limit = min(
        max(query.limit, 1),
        100,
    )

    result_rows = result_rows[:safe_limit]

    columns = (
        list(result_rows[0].keys())
        if result_rows
        else list(query.metrics)
    )

    return ChatbotQueryResult(
        columns=columns,
        rows=result_rows,
        total_rows=total_rows,
    )
