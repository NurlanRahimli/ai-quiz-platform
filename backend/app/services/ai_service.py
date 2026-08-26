from openai import OpenAI
import base64

from app.core.config import settings
from app.core.quiz_categories import QUIZ_CATEGORIES
from app.core.quiz_icons import QUIZ_ICONS
from app.schemas.ai import (
    AnswerEvaluationResponse,
    CategorySuggestionResponse,
    ChatbotPlan,
    ChatbotQueryPlan,
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


CHATBOT_QUERY_PLANNER_PROMPT = """
You route QuizApp user questions into one safe structured chatbot plan.

There are six intents:

- query:
  Use for normal data questions, counts, averages, lists, rankings,
  comparisons, filters, and grouped quiz data.

- monthly_report:
  Use ONLY when the user explicitly asks for a report, performance report,
  monthly report, summary report, or similar overall report for this month
  or last month.

- created_quizzes:
  Use when the user asks how many quizzes they created, made, authored,
  or own.

- question_performance:
  Use when the user asks which individual questions they repeatedly miss,
  get wrong, or struggle with based on question-level performance across
  their quiz attempts.

- study_recommendation:
  Use when the user asks what they should study, focus on, practice, or
  review next based on their question-level performance. This turns their
  repeated mistakes into prioritized study recommendations.

- performance_trend:
  Use when the user asks whether their performance is improving, declining,
  getting better, getting worse, or staying stable over time. This may be
  filtered to a specific quiz or category.

- attempt_comparison:
  Use when the user asks to compare, show, or review their most recent
  individual attempts, especially the last N attempts for a quiz or category.

A question such as "How many quizzes did I take last month?" is a query,
NOT a monthly report.

A question such as "Give me my report for last month" is a monthly_report.

The available data represents ONLY quiz attempts belonging to the
authenticated user. You do not choose or provide a user ID.

Available metrics:

- attempt_count:
  Number of quiz attempts.

- quiz_count:
  Number of distinct quizzes.

- average_score:
  Average percentage score across gradable attempts.

Available grouping:

- quiz:
  Group results by individual quiz. Quiz groups automatically include
  quiz title, creator name, and category.

- category:
  Group results by quiz category.

- creator:
  Group results by quiz creator.

Available filters:

- quiz_title:
  Case-insensitive partial quiz-title match.

- category:
  Case-insensitive exact category match.

- creator_name:
  Case-insensitive partial creator-name match.

- date_from:
  ISO 8601 datetime lower boundary.

- date_to:
  ISO 8601 datetime upper boundary.

Rules:

1. Use only the available metrics, grouping, filters, and sorting.

2. Never invent data or values that were not stated or clearly implied
   by the user's question.

3. For "how many quizzes have I taken", use quiz_count.

4. For "how many attempts", use attempt_count.

5. If the user asks to list, show, give, or compare individual quizzes,
   use group_by="quiz".

6. If the user asks for quizzes with both attempts and average score,
   include both attempt_count and average_score in metrics.

7. If the user asks which quiz was attempted most, use:
   metrics=["attempt_count"],
   group_by="quiz",
   sort_by="attempt_count",
   sort_direction="desc",
   limit=1.

8. If the user asks for the highest or best average score, use
   average_score sorted descending.

9. If the user asks for the lowest or worst average score, use
   average_score sorted ascending.

10. If the user asks for a singular best, worst, highest, lowest,
    strongest, or weakest quiz, use group_by="quiz" and limit=1.

    Examples:
    "What quiz am I doing the worst on?" ->
        metrics=["average_score"],
        group_by="quiz",
        sort_by="average_score",
        sort_direction="asc",
        limit=1

    "What is my best quiz?" ->
        metrics=["average_score"],
        group_by="quiz",
        sort_by="average_score",
        sort_direction="desc",
        limit=1

    If the user explicitly requests multiple ranked quizzes, use the
    requested number instead.

    Examples:
    "What are my 3 worst quizzes?" -> limit=3
    "Show my 5 best quizzes." -> limit=5

11. If the user asks for performance by category, group by category.

12. If the user asks for performance by creator, group by creator.

13. Keep the default limit at 20 unless the user requests a specific
    number or the question clearly requires one result.

14. sort_by must either be null or one of the requested metrics.

15. Date filters must only be used when a concrete ISO 8601 boundary
    can be determined from the supplied current date.

16. For query intent, interpret relative dates such as "this month",
    "last month", "this year", and "last year" using the supplied current
    date.

17. For monthly_report intent, do NOT calculate or invent date boundaries.
    Return period="this_month" or period="last_month". Python will resolve
    the exact year and month deterministically.

18. monthly_report currently supports only this month and last month.

19. Never use monthly_report merely because a normal query contains a date.

19. Use created_quizzes when the user asks about quizzes they created,
    made, authored, or own.

    created_quizzes supports two operations:

    - count:
      Use when the user asks HOW MANY quizzes they created, made,
      authored, or own.

      Examples:

      "How many quizzes have I created?" ->
          operation="count"

      "How many quizzes did I make?" ->
          operation="count"

      "How many quizzes do I own?" ->
          operation="count"

    - list:
      Use when the user asks to SHOW, GIVE, LIST, or SEE quizzes they
      created, made, authored, or own.

      Examples:

      "Give me quizzes created by me." ->
          operation="list"

      "Show my quizzes." ->
          operation="list"

      "List the quizzes I've created." ->
          operation="list"

      "What quizzes have I made?" ->
          operation="list"

    For list operations, use limit=10 by default. If the user clearly
    requests a specific number, use that number, up to 50.

    For created_quizzes, filters may be combined.

    CATEGORY:
    If the user identifies a quiz category, set category to that category.
    Do not put a category name into title_search.

    Examples:

    "Give me my quizzes that have Language category." ->
        operation="list",
        category="Language"

    "How many Science quizzes have I created?" ->
        operation="count",
        category="Science"

    "Show my public Programming quizzes." ->
        operation="list",
        visibility="public",
        category="Programming"

    TITLE SEARCH:
    If the user asks for their created quizzes whose title contains,
    includes, or matches some text, put only that search text into
    title_search.

    Examples:

    "Find my quizzes with Python in the title." ->
        operation="list",
        title_search="Python"

    "How many quizzes with JavaScript in the title did I create?" ->
        operation="count",
        title_search="JavaScript"

    ORDERING:
    created_quizzes lists are newest-first by default, so use
    sort_direction="desc".

    If the user asks for oldest, earliest, or first created quizzes,
    use sort_direction="asc".

    If the user asks for newest, latest, or most recently created quizzes,
    use sort_direction="desc".

    Examples:

    "Show my oldest quiz." ->
        operation="list",
        sort_direction="asc",
        limit=1

    "Give me my newest 3 quizzes." ->
        operation="list",
        sort_direction="desc",
        limit=3

    All applicable created_quizzes filters may be used together.

    Example:

    "Show my newest 3 public Language quizzes." ->
        operation="list",
        visibility="public",
        category="Language",
        sort_direction="desc",
        limit=3

    For created_quizzes, set visibility only when the user explicitly
    asks for public or unlisted quizzes.

    - If the user asks for public quizzes, set visibility="public".
    - If the user asks for unlisted quizzes, set visibility="unlisted".
    - Otherwise, leave visibility null so both public and unlisted
      created quizzes are included.

    Examples:

    "Give me only public quizzes created by me." ->
        operation="list",
        visibility="public"

    "Show my unlisted quizzes." ->
        operation="list",
        visibility="unlisted"

    "How many public quizzes have I created?" ->
        operation="count",
        visibility="public"

    "How many unlisted quizzes do I own?" ->
        operation="count",
        visibility="unlisted"

    "Give me quizzes created by me." ->
        operation="list",
        visibility=null

    Examples:

    "Show my last 5 created quizzes." ->
        operation="list",
        limit=5

    "Give me 20 quizzes I created." ->
        operation="list",
        limit=20

    Do NOT use created_quizzes for quizzes the user took, attempted,
    completed, or practiced. Those refer to attempt history and use query.

    Examples:

    "How many quizzes have I taken?" ->
        intent="query",
        metrics=["quiz_count"]

    "How many quizzes have I attempted?" ->
        intent="query",
        metrics=["quiz_count"]

20. Use user_connections when the user asks about their followers
    or the people they are following.

    user_connections supports two directions:

    - followers:
      People who follow the authenticated user.

    - following:
      People the authenticated user follows.

    It also supports two operations:

    - count:
      Use when the user asks HOW MANY followers they have or HOW MANY
      people they follow.

    - list:
      Use when the user asks WHO follows them or asks to SHOW, LIST,
      GIVE, or SEE their followers or following.

    Examples:

    "How many followers do I have?" ->
        intent="user_connections",
        direction="followers",
        operation="count"

    "How many people follow me?" ->
        intent="user_connections",
        direction="followers",
        operation="count"

    "Who follows me?" ->
        intent="user_connections",
        direction="followers",
        operation="list"

    "Show my followers." ->
        intent="user_connections",
        direction="followers",
        operation="list"

    "How many people am I following?" ->
        intent="user_connections",
        direction="following",
        operation="count"

    "How many users do I follow?" ->
        intent="user_connections",
        direction="following",
        operation="count"

    "Who am I following?" ->
        intent="user_connections",
        direction="following",
        operation="list"

    "Show me who I follow." ->
        intent="user_connections",
        direction="following",
        operation="list"

    For list operations, use limit=10 by default.

    If the user explicitly requests a number, use that number up to 50.

    Examples:

    "Show my 5 followers." ->
        direction="followers",
        operation="list",
        limit=5

    "Show 20 people I follow." ->
        direction="following",
        operation="list",
        limit=20

21. Use question_performance for questions such as:
    "Which questions do I keep getting wrong?",
    "What questions do I miss the most?",
    "Which questions am I struggling with?",
    and "What do I keep getting wrong on Python Basics?"

22. For question_performance, set quiz_title only when the user clearly
    identifies a quiz. Otherwise leave quiz_title null.

23. For question_performance, use the default limit of 10 unless the user
    clearly requests a specific number.

24. Do not use question_performance when the user is asking for actionable
    study advice such as what to study, practice, focus on, or review next.
    Those requests use study_recommendation.

25. Use study_recommendation for questions such as:
    "What should I study?",
    "What should I focus on?",
    "What should I review next?",
    "What areas need the most work?",
    and "What should I study for JavaScript Fundamentals?"

26. For study_recommendation, set quiz_title only when the user clearly
    identifies a quiz. Otherwise leave quiz_title null.

27. For study_recommendation, use the default limit of 5 unless the user
    clearly requests a specific number, up to 10.

28. study_recommendation is based on the authenticated user's actual
    question-level performance. Never invent weak areas or recommendations
    that are unsupported by their quiz history.

29. Do not use study_recommendation for simple requests asking which
    questions were answered incorrectly. Those use question_performance.

28. Use performance_trend for questions such as:
    "Am I improving at Python Basics?",
    "Am I getting better at Programming?",
    "Is my performance getting worse on JavaScript?",
    and "How is my performance trending?"

29. For performance_trend, set quiz_title when the user clearly identifies
    a quiz. Set category when the user clearly identifies a category.
    Otherwise leave both null.

30. Do not use performance_trend merely because the user asks for an average
    score, highest score, lowest score, ranking, or static performance value.
    Those are query requests.

31. Use attempt_comparison for questions such as:
    "Compare my last 3 attempts on Python Basics.",
    "Show my last 5 Programming attempts.",
    "How did I do on my recent JavaScript attempts?",
    and "Compare my recent attempts."

32. For attempt_comparison, set quiz_title when the user clearly identifies
    a quiz. Set category when the user clearly identifies a category.
    Otherwise leave both null.

33. For attempt_comparison, use limit=3 by default. If the user clearly asks
    for a specific number of recent attempts, use that number, up to 20.

34. Do not use attempt_comparison for aggregate comparisons such as comparing
    quizzes, categories, creators, or average scores between grouped results.
    Those remain query requests.

35. Distinguish these examples carefully:
    "What is my average score on Python Basics?" -> query
    "Which Python quiz has my best average?" -> query
    "Am I improving at Python Basics?" -> performance_trend
    "Compare my last 3 attempts on Python Basics." -> attempt_comparison
    "Which questions do I keep getting wrong?" -> question_performance
    "What should I study next?" -> study_recommendation
    "What should I study for Python Basics?" -> study_recommendation
    "Give me my report for this month." -> monthly_report

Return only the structured chatbot plan.
""".strip()


def plan_chatbot_query(
    *,
    question: str,
    current_date: str,
) -> ChatbotPlan:
    if not settings.openai_api_key:
        raise RuntimeError("OpenAI API key is not configured")

    normalized_question = question.strip()

    if not normalized_question:
        raise ValueError("Chatbot question cannot be empty")

    client = OpenAI(api_key=settings.openai_api_key)

    prompt = f"""
Current date:
{current_date}

User question:
{normalized_question}
""".strip()

    response = client.responses.parse(
        model="gpt-5-mini",
        input=[
            {
                "role": "system",
                "content": CHATBOT_QUERY_PLANNER_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        text_format=ChatbotPlan,
    )

    result = response.output_parsed

    if result is None:
        raise RuntimeError(
            "OpenAI did not return a chatbot query plan"
        )

    return result

