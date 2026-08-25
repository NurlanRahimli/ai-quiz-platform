import uuid

from app.schemas.quiz_attempt import QuizAttemptResultAnswer
from app.services.quiz_result_pdf import build_quiz_result_pdf


def test_build_quiz_result_pdf_returns_valid_pdf():
    answers = [
        QuizAttemptResultAnswer(
            question_id=uuid.uuid4(),
            question_text="What is 2 + 2?",
            question_type="multiple_choice",
            is_correct=True,
            submitted_answer="4",
            correct_answer="4",
            answer_choices=[],
        ),
        QuizAttemptResultAnswer(
            question_id=uuid.uuid4(),
            question_text="Explain what a variable is.",
            question_type="written_answer",
            is_correct=None,
            submitted_answer="A variable stores a value.",
            correct_answer=None,
            answer_choices=[],
        ),
        QuizAttemptResultAnswer(
            question_id=uuid.uuid4(),
            question_text="Solve x + 5 = 10.",
            question_type="math_work",
            is_correct=False,
            submitted_answer="4",
            correct_answer="5",
            answer_choices=[],
            ai_explanation=(
                "Subtract 5 from both sides to get x = 5."
            ),
        ),
    ]

    pdf = build_quiz_result_pdf(
        quiz_title="Python Fundamentals",
        score=1,
        gradable_questions=2,
        total_questions=3,
        answers=answers,
    )

    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000