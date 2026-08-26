import pytest

from app.services.chatbot_faq_service import answer_chatbot_faq


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        (
            "How do I create a quiz?",
            "Create Quiz",
        ),
        (
            "How do I create a new quiz?",
            "Create Quiz",
        ),
        (
            "How can I create a new quiz?",
            "Create Quiz",
        ),
        (
            "How do I make a new quiz?",
            "Create Quiz",
        ),
        (
            "How can I make a new quiz?",
            "Create Quiz",
        ),
        (
            "How can I upload a document?",
            "OCR",
        ),
        (
            "What is the difference between public and unlisted?",
            "public quiz",
        ),
        (
            "What is public visibility in a quiz?",
            "public quiz",
        ),
        (
            "What does public visibility mean?",
            "public quiz",
        ),
        (
            "What does public mean for a quiz?",
            "public quiz",
        ),
        (
            "What is visibility on a quiz?",
            "public quiz",
        ),
        (
            "What's visibility on a quiz?",
            "public quiz",
        ),
        (
            "What is quiz visibility?",
            "public quiz",
        ),
        (
            "What's quiz visibility?",
            "public quiz",
        ),
        (
            "What does quiz visibility mean?",
            "public quiz",
        ),
        (
            "How do I edit my quiz?",
            "Edit Quiz",
        ),
        (
            "How can I take a quiz?",
            "Start Quiz",
        ),
        (
            "Where are my quiz results?",
            "attempt",
        ),
        (
            "What are categories and tags?",
            "Categories",
        ),
        (
            "How do I follow a user?",
            "follow",
        ),
        (
            "What can you do?",
            "performance",
        ),
        (
            "What is the monthly report?",
            "monthly report",
        ),
        (
            "What is on dashboard?",
            "dashboard",
        ),
        (
            "What's on dashboard?",
            "dashboard",
        ),
        (
            "What is on settings page?",
            "settings",
        ),
        (
            "What's on settings page?",
            "settings",
        ),
        (
            "What is on import quiz page?",
            "Import Quiz",
        ),
        (
            "What's on import quiz page?",
            "Import Quiz",
        ),
        (
            "What is on my profile page?",
            "profile",
        ),
        (
            "What's on my profile page?",
            "profile",
        ),
        (
            "What is on my dashboard page?",
            "dashboard",
        ),
        (
            "What does the dashboard page show?",
            "dashboard",
        ),
        (
            "What is on my attempts page?",
            "attempt",
        ),
        (
            "What does the attempts page show?",
            "attempt",
        ),
        (
            "What is on the Discover page?",
            "discovery",
        ),
        (
            "What does the Discover page show?",
            "discovery",
        ),
        (
            "What is on my profile page?",
            "profile",
        ),
        (
            "What does the settings page show?",
            "settings",
        ),
        (
            "What is the audit log page?",
            "audit log",
        ),
    ],
)
def test_answer_chatbot_faq_matches_known_questions(
    question,
    expected,
):
    answer = answer_chatbot_faq(question)

    assert answer is not None
    assert expected.lower() in answer.lower()


@pytest.mark.parametrize(
    "question",
    [
        "How many quizzes have I created?",
        "Show my quizzes.",
        "Give me quizzes created by me.",
        "Find my created quizzes.",
        "What is my average score?",
        "What should I study?",
        "What should I study for Python Basics?",
        "Which questions do I struggle with?",
        "Which questions do I keep getting wrong?",
        "What questions am I struggling with?",
        "Compare my recent attempts",
        "Compare my last 3 attempts on Python Basics.",
        "Am I improving at Python Basics?",
        "Who follows me?",
        "Who am I following?",
    ],
)
def test_answer_chatbot_faq_does_not_capture_data_questions(
    question,
):
    assert answer_chatbot_faq(question) is None


@pytest.mark.parametrize(
    ("question", "expected_text", "expected_path"),
    [
        (
            "How do I create a quiz?",
            "Create Quiz",
            "/quizzes/new",
        ),
        (
            "How can I discover quizzes?",
            "discovery",
            "/discover",
        ),
        (
            "Where can I see my attempts?",
            "attempt",
            "/attempts",
        ),
        (
            "What is my dashboard?",
            "dashboard",
            "/dashboard",
        ),
        (
            "How do I change my settings?",
            "settings",
            "/settings",
        ),
    ],
)
def test_faq_links_use_configured_frontend_url(
    monkeypatch,
    question,
    expected_text,
    expected_path,
):
    monkeypatch.setattr(
        "app.services.chatbot_faq_service.settings.frontend_url",
        "https://quizapp.example",
    )

    answer = answer_chatbot_faq(question)

    assert answer is not None
    assert expected_text.lower() in answer.lower()
    assert (
        f"Link: https://quizapp.example{expected_path}"
        in answer
    )


@pytest.mark.parametrize(
    ("question", "expected_text"),
    [
        (
            "What question types are supported?",
            "Multiple Choice",
        ),
        (
            "What are categories and tags?",
            "3 tags",
        ),
        (
            "What is the difference between public and unlisted?",
            "unlisted",
        ),
        (
            "Can I retake a quiz?",
            "retake",
        ),
        (
            "Can I export my results as PDF?",
            "PDF",
        ),
        (
            "What can the chatbot do?",
            "performance",
        ),
        (
            "How do study recommendations work?",
            "study",
        ),
        (
            "How does performance trend work?",
            "performance",
        ),
        (
            "How does attempt comparison work?",
            "attempt",
        ),
    ],
)
def test_major_faq_topics_have_answers(
    question,
    expected_text,
):
    answer = answer_chatbot_faq(question)

    assert answer is not None
    assert expected_text.lower() in answer.lower()
