from openai import OpenAI
import base64

from app.core.config import settings
from app.core.quiz_categories import QUIZ_CATEGORIES
from app.schemas.ai import (
    CategorySuggestionResponse,
    ExtractedQuiz,
    ImportedQuiz,
    QuizAIContext,
    TagSuggestionResponse,
)


class QuizImportQuestionLimitError(Exception):
    pass


QUIZ_IMPORT_PROMPT = """
Extract the quiz from the uploaded document or image.

Rules:

1. Extract every quiz question in the order it appears.

2. Supported question types are:
   - multiple_choice
   - written_answer
   - math_work

3. For multiple-choice questions:
   - extract every visible answer choice
   - choices must contain at least 2 answer choices
   - expected_answer MUST always be null
   - NEVER copy the correct choice text into expected_answer
   - the correct answer is represented ONLY by choices[].is_correct
   - if the document explicitly identifies the correct answer,
     mark exactly that choice as correct and use
     answer_source="document"
   - if no answer is marked, solve the question yourself
   - if you can confidently determine the correct answer,
     mark exactly one choice as correct and use
     answer_source="ai_inferred"
   - if you cannot confidently determine the answer,
     mark every choice as incorrect,
     set expected_answer=null,
     use answer_source="unavailable",
     needs_review=true,
     and explain why in review_reason

4. For written-answer and math questions:
   - choices MUST always be an empty list
   - the answer belongs ONLY in expected_answer
   - if the document explicitly provides the expected answer,
     put it in expected_answer and use answer_source="document"
   - otherwise determine the expected answer yourself when
     reasonably confident, put it in expected_answer,
     and use answer_source="ai_inferred"
   - if the answer cannot be determined confidently,
     set expected_answer=null,
     use answer_source="unavailable",
     needs_review=true,
     and explain why in review_reason

5. Do not invent questions that are not present in the file.

6. Preserve the meaning of question and answer text.

7. Extract a title and description only when they are actually
   present in the uploaded file. Otherwise return null for them.

8. Choose exactly one category from this approved list:
{categories}

9. Generate up to 3 concise and relevant tags.

10. A tag must contain no more than 50 characters.

11. If an answer was inferred by you rather than explicitly shown
    in the uploaded file, it MUST use answer_source="ai_inferred".

12. needs_review should normally be false for document answers and
    confident AI-inferred answers.

Return only the structured quiz extraction.

13. Question field rules are strict:
    - multiple_choice:
      expected_answer=null and choices contains the answers
    - written_answer:
      choices=[] and expected_answer contains the answer when known
    - math_work:
      choices=[] and expected_answer contains the answer when known
""".strip()


def validate_extracted_quiz(
    extracted_quiz: ExtractedQuiz,
) -> ImportedQuiz:
    if len(extracted_quiz.questions) > 30:
        raise QuizImportQuestionLimitError(
            "This quiz contains more than 30 questions. "
            "Keep only 30 questions and try again."
        )

    if extracted_quiz.category not in QUIZ_CATEGORIES:
        raise RuntimeError(
            "OpenAI returned an unsupported category"
        )

    return ImportedQuiz.model_validate(
        extracted_quiz.model_dump()
    )


def extract_quiz_from_file(
    *,
    contents: bytes,
    content_type: str,
) -> ImportedQuiz:
    if not settings.openai_api_key:
        raise RuntimeError("OpenAI API key is not configured")

    client = OpenAI(api_key=settings.openai_api_key)

    categories = "\n".join(
        f"- {category}" for category in QUIZ_CATEGORIES
    )

    prompt = QUIZ_IMPORT_PROMPT.format(
        categories=categories,
    )

    encoded_file = base64.b64encode(contents).decode("utf-8")

    if content_type == "application/pdf":
        file_content = {
            "type": "input_file",
            "filename": "quiz.pdf",
            "file_data": (
                f"data:application/pdf;base64,{encoded_file}"
            ),
        }
    else:
        file_content = {
            "type": "input_image",
            "image_url": (
                f"data:{content_type};base64,{encoded_file}"
            ),
            "detail": "high",
        }

    response = client.responses.parse(
        model="gpt-5-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "You extract structured quizzes from uploaded "
                    "documents and images. Carefully distinguish "
                    "answers explicitly shown in the source from "
                    "answers you infer yourself."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt,
                    },
                    file_content,
                ],
            },
        ],
        text_format=ExtractedQuiz,
    )

    result = response.output_parsed

    if result is None:
        raise RuntimeError(
            "OpenAI did not return a quiz extraction"
        )

    return validate_extracted_quiz(result)


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