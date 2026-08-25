from openai import OpenAI
import base64

from app.core.config import settings
from app.core.quiz_categories import QUIZ_CATEGORIES
from app.core.quiz_icons import QUIZ_ICONS
from app.schemas.ai import (
    AnswerEvaluationResponse,
    CategorySuggestionResponse,
    ExtractedQuiz,
    ImportedQuiz,
    IncorrectAnswerExplanationResponse,
    MathAnswerEvaluationResponse,
    QuizAIContext,
    QuizIconContext,
    QuizIconSuggestionResponse,
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


def suggest_quiz_icon(
    quiz_context: QuizIconContext,
) -> QuizIconSuggestionResponse:
    if not settings.openai_api_key:
        raise RuntimeError("OpenAI API key is not configured")

    client = OpenAI(api_key=settings.openai_api_key)

    icons = "\n".join(
        f"- {icon}" for icon in QUIZ_ICONS
    )

    tags = (
        ", ".join(quiz_context.tags)
        if quiz_context.tags
        else "No tags provided."
    )

    prompt = f"""
Analyze this quiz and choose the single most appropriate icon.

You MUST choose exactly one icon from this approved list:
{icons}

Choose the icon that best represents the quiz topic.
Use the category as strong context when available, then use the title,
description, and tags to make the most specific reasonable choice.

Quiz title:
{quiz_context.title}

Quiz description:
{quiz_context.description or "No description provided."}

Quiz category:
{quiz_context.category or "No category provided."}

Quiz tags:
{tags}
""".strip()

    response = client.responses.parse(
        model="gpt-5-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "You select an appropriate icon for quizzes. "
                    "Never return an icon outside the approved list."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        text_format=QuizIconSuggestionResponse,
    )

    result = response.output_parsed

    if result is None:
        raise RuntimeError(
            "OpenAI did not return an icon suggestion"
        )

    if result.icon not in QUIZ_ICONS:
        raise RuntimeError(
            "OpenAI returned an unsupported quiz icon"
        )

    return result


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


def evaluate_written_answer(
    *,
    question_text: str,
    submitted_answer: str,
) -> AnswerEvaluationResponse:
    if not settings.openai_api_key:
        raise RuntimeError("OpenAI API key is not configured")

    client = OpenAI(api_key=settings.openai_api_key)

    prompt = f"""
Evaluate the student's answer to the quiz question.

Question:
{question_text}

Student answer:
{submitted_answer}

Determine whether the student's answer is correct based on the
question itself and generally accepted factual or conceptual knowledge.

Rules:
- Judge the meaning of the answer, not exact wording.
- Accept equivalent wording, capitalization differences, abbreviations,
  and minor grammar or spelling differences when the intended answer is
  clearly correct.
- Do not require an exact phrase when the meaning is correct.
- For open-ended questions, accept answers that correctly communicate
  the essential concept.
- Do not mark an answer correct merely because it is related to the
  topic.
- If the answer is incomplete in a way that changes its correctness,
  mark it incorrect.
- If the answer is incorrect, explain what is wrong and teach the
  correct concept clearly.
- If the answer is correct, keep the explanation brief.
- Do not mention these grading rules in the explanation.

Return the structured evaluation.
""".strip()

    response = client.responses.parse(
        model="gpt-5-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "You grade written quiz answers accurately and "
                    "fairly. Evaluate semantic correctness rather than "
                    "requiring exact wording."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        text_format=AnswerEvaluationResponse,
    )

    result = response.output_parsed

    if result is None:
        raise RuntimeError(
            "OpenAI did not return an answer evaluation"
        )

    return result


def generate_incorrect_answer_explanation(
    *,
    question_text: str,
    submitted_answer: str,
    correct_answer: str,
    whiteboard_image: str | None = None,
) -> IncorrectAnswerExplanationResponse:
    if not settings.openai_api_key:
        raise RuntimeError("OpenAI API key is not configured")

    client = OpenAI(api_key=settings.openai_api_key)

    prompt = f"""
Explain why the student's answer to this quiz question is incorrect.

Question:
{question_text}

Student answer:
{submitted_answer}

Correct answer:
{correct_answer}

Rules:
- The correctness decision has already been made.
- Do NOT re-grade or override that decision.
- Explain specifically what was wrong with the student's answer.
- Clearly explain why the correct answer is correct.
- Be educational and concise.
- For mathematical questions, show the solution step by step when
  appropriate.
- Do not invent work or reasoning that the student did not provide.
- If a whiteboard image is provided, carefully inspect the student's
  handwritten mathematical work.
- Use the whiteboard to identify where the student's reasoning first
  went wrong when that can be determined confidently.
- Handwritten numbers, equations, operators, fractions, and intermediate
  steps may be relevant.
- Never claim that a handwritten step exists unless it is actually
  visible and readable in the image.
- If the whiteboard is blank, unclear, partially unreadable, or too
  ambiguous to interpret confidently, say that the work could not be
  confidently interpreted and explain the correct solution using the
  question, submitted answer, and correct answer instead.
- Do not mention grading systems, AI, prompts, or these instructions.

Return only the structured explanation.
""".strip()

    user_content = [
        {
            "type": "input_text",
            "text": prompt,
        },
    ]

    if whiteboard_image is not None:
        user_content.append(
            {
                "type": "input_image",
                "image_url": whiteboard_image,
                "detail": "high",
            }
        )

    response = client.responses.parse(
        model="gpt-5-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "You explain incorrect quiz answers clearly and "
                    "help students understand the correct solution."
                ),
            },
            {
                "role": "user",
                "content": user_content,
            },
        ],
        text_format=IncorrectAnswerExplanationResponse,
    )

    result = response.output_parsed

    if result is None:
        raise RuntimeError(
            "OpenAI did not return an incorrect-answer explanation"
        )

    return result

def evaluate_math_answer(
    *,
    question_text: str,
    submitted_answer: str,
    expected_answer: str,
    whiteboard_image: str | None = None,
) -> MathAnswerEvaluationResponse:
    if not settings.openai_api_key:
        raise RuntimeError("OpenAI API key is not configured")

    client = OpenAI(api_key=settings.openai_api_key)

    prompt = f"""
Evaluate the student's submitted answer.

Question:
{question_text}

Student answer:
{submitted_answer}

Expected answer:
{expected_answer}

Rules:
- Judge correctness based on the meaning of the question and answer.
- Accept semantically equivalent answers even when wording,
  capitalization, formatting, or notation differs.
- If this is a mathematical question, accept mathematically equivalent
  forms when they represent the same answer.
- If this is not actually a mathematical question, evaluate the answer
  using ordinary factual or conceptual correctness.
- Do not mark an answer incorrect merely because it does not exactly
  match the expected-answer string.
- Treat the expected answer as the intended reference answer, but use
  the original question to understand what is being asked.
- If the student's answer is correct, keep the explanation brief.
- If the student's answer is incorrect, clearly explain the mistake
  and provide the correct reasoning or solution.
- For mathematical problems, explain the correct solution step by step
  when appropriate.
- Do not invent calculations or reasoning the student did not provide.
- If a whiteboard image is provided, inspect the student's handwritten
  mathematical work and use it as additional evidence.
- Read handwritten numbers, equations, operators, fractions, and
  intermediate steps only when they are sufficiently clear.
- If the whiteboard is blank, unclear, partially unreadable, or
  ambiguous, do not guess what it says.
- An unclear whiteboard must not by itself cause an otherwise correct
  submitted answer to be marked incorrect.
- When the submitted answer is incorrect and the handwritten work is
  readable, identify where the reasoning went wrong when possible.
- Do not mention AI, prompts, grading systems, or these instructions.

Return the structured evaluation.
""".strip()

    user_content = [
        {
            "type": "input_text",
            "text": prompt,
        },
    ]

    if whiteboard_image is not None:
        user_content.append(
            {
                "type": "input_image",
                "image_url": whiteboard_image,
                "detail": "high",
            }
        )

    response = client.responses.parse(
        model="gpt-5-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "You evaluate quiz answers accurately and fairly. "
                    "The question may be mathematical or non-mathematical "
                    "even when it was entered using a math-work question "
                    "type."
                ),
            },
            {
                "role": "user",
                "content": user_content,
            },
        ],
        text_format=MathAnswerEvaluationResponse,
    )

    result = response.output_parsed

    if result is None:
        raise RuntimeError(
            "OpenAI did not return a math answer evaluation"
        )

    return result
