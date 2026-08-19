import uuid
from types import SimpleNamespace

from app.services.quiz_grading import grade_attempt_answer


def test_grades_correct_multiple_choice_answer():
    correct_choice_id = uuid.uuid4()

    question = SimpleNamespace(
        question_type="multiple_choice",
        answer_choices=[
            SimpleNamespace(id=correct_choice_id, is_correct=True),
            SimpleNamespace(id=uuid.uuid4(), is_correct=False),
        ],
    )
    answer = SimpleNamespace(
        selected_choice_id=correct_choice_id,
        text_answer=None,
    )

    assert grade_attempt_answer(question, answer) is True


def test_grades_incorrect_multiple_choice_answer():
    correct_choice_id = uuid.uuid4()
    incorrect_choice_id = uuid.uuid4()

    question = SimpleNamespace(
        question_type="multiple_choice",
        answer_choices=[
            SimpleNamespace(id=correct_choice_id, is_correct=True),
            SimpleNamespace(id=incorrect_choice_id, is_correct=False),
        ],
    )
    answer = SimpleNamespace(
        selected_choice_id=incorrect_choice_id,
        text_answer=None,
    )

    assert grade_attempt_answer(question, answer) is False


def test_grades_equivalent_math_answer():
    question = SimpleNamespace(
        question_type="math_work",
        expected_answer="4*x",
    )
    answer = SimpleNamespace(
        selected_choice_id=None,
        text_answer="2*x + 2*x",
    )

    assert grade_attempt_answer(question, answer) is True


def test_grades_incorrect_math_answer():
    question = SimpleNamespace(
        question_type="math_work",
        expected_answer="4*x",
    )
    answer = SimpleNamespace(
        selected_choice_id=None,
        text_answer="5*x",
    )

    assert grade_attempt_answer(question, answer) is False


def test_written_answer_is_not_automatically_graded():
    question = SimpleNamespace(
        question_type="written_answer",
    )
    answer = SimpleNamespace(
        selected_choice_id=None,
        text_answer="Closures preserve access to their lexical scope.",
    )

    assert grade_attempt_answer(question, answer) is None