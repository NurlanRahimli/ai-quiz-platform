from app.models.question import Question
from app.models.quiz_attempt_answer import QuizAttemptAnswer
from app.services.math_validation import are_math_expressions_equivalent


def grade_attempt_answer(
    question: Question,
    answer: QuizAttemptAnswer,
) -> bool | None:
    if question.question_type == "multiple_choice":
        if answer.selected_choice_id is None:
            return False

        return any(
            choice.id == answer.selected_choice_id and choice.is_correct
            for choice in question.answer_choices
        )

    if question.question_type == "math_work":
        if not answer.text_answer or not question.expected_answer:
            return False

        return are_math_expressions_equivalent(
            answer.text_answer,
            question.expected_answer,
        )

    if question.question_type == "written_answer":
        return None

    return None