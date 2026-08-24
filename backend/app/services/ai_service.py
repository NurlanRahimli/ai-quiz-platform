from openai import OpenAI

from app.core.config import settings
from app.core.quiz_categories import QUIZ_CATEGORIES
from app.schemas.ai import (
    CategorySuggestionResponse,
    QuizAIContext,
    TagSuggestionResponse,
)


def suggest_quiz_category(
    quiz_context: QuizAIContext,
) -> CategorySuggestionResponse:
    if not settings.openai_api_key:
        raise RuntimeError("OpenAI API key is not configured")

    client = OpenAI(api_key=settings.openai_api_key)

    categories = "\n".join(
        f"- {category}" for category in QUIZ_CATEGORIES
    )

    questions = "\n".join(
        f"{index}. {question}"
        for index, question in enumerate(
            quiz_context.questions,
            start=1,
        )
    )

    prompt = f"""
Analyze this quiz and choose the single most appropriate category.

You MUST choose exactly one category from this approved list:
{categories}

Use the quiz questions as the primary evidence.
Use the title and description only as supporting context.

Quiz title:
{quiz_context.title}

Quiz description:
{quiz_context.description or "No description provided."}

Quiz questions:
{questions}
""".strip()

    response = client.responses.parse(
        model="gpt-5-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "You classify quizzes into approved categories. "
                    "Never invent a category outside the provided list."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        text_format=CategorySuggestionResponse,
    )

    result = response.output_parsed

    if result is None:
        raise RuntimeError("OpenAI did not return a category suggestion")

    if result.category not in QUIZ_CATEGORIES:
        raise RuntimeError("OpenAI returned an unsupported category")

    return result


def suggest_quiz_tags(
    quiz_context: QuizAIContext,
) -> TagSuggestionResponse:
    if not settings.openai_api_key:
        raise RuntimeError("OpenAI API key is not configured")

    client = OpenAI(api_key=settings.openai_api_key)

    questions = "\n".join(
        f"{index}. {question}"
        for index, question in enumerate(
            quiz_context.questions,
            start=1,
        )
    )

    prompt = f"""
Analyze this quiz and suggest up to 3 concise, relevant tags.

Use the quiz questions as the primary evidence.
Use the title and description only as supporting context.

Tags should:
- be short and specific
- describe the main topics or concepts in the quiz
- not duplicate each other
- contain no more than 50 characters each
- include no more than 3 tags total

Quiz title:
{quiz_context.title}

Quiz description:
{quiz_context.description or "No description provided."}

Quiz questions:
{questions}
""".strip()

    response = client.responses.parse(
        model="gpt-5-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "You generate concise and relevant tags for quizzes. "
                    "Return no more than 3 unique tags."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        text_format=TagSuggestionResponse,
    )

    result = response.output_parsed

    if result is None:
        raise RuntimeError("OpenAI did not return tag suggestions")

    normalized_tags: list[str] = []

    for tag in result.tags:
        normalized_tag = tag.strip()

        if (
            normalized_tag
            and len(normalized_tag) <= 50
            and normalized_tag.lower()
            not in {existing.lower() for existing in normalized_tags}
        ):
            normalized_tags.append(normalized_tag)

    return TagSuggestionResponse(
        tags=normalized_tags[:3],
    )