import uuid

from app.models.answer_choice import AnswerChoice
from app.models.question import Question
from app.models.quiz import Quiz
from app.models.quiz_attempt import QuizAttempt
from app.models.quiz_attempt_answer import QuizAttemptAnswer
from app.models.user import User
from app.services.chatbot_data_service import (
    get_user_attempt_rows,
    get_user_question_performance_rows,
    get_user_quiz_summaries,
)


def create_user(
    db,
    *,
    display_name: str,
    email: str,
) -> User:
    user = User(
        email=email,
        display_name=display_name,
        password_hash="test-password-hash",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def create_quiz(
    db,
    *,
    owner: User,
    title: str,
    category: str,
) -> tuple[Quiz, Question, AnswerChoice, AnswerChoice]:
    quiz = Quiz(
        owner_id=owner.id,
        title=title,
        category=category,
        visibility="public",
    )
    db.add(quiz)
    db.flush()

    question = Question(
        quiz_id=quiz.id,
        text=f"{title} question",
        question_type="multiple_choice",
        position=1,
    )
    db.add(question)
    db.flush()

    correct_choice = AnswerChoice(
        question_id=question.id,
        text="Correct",
        is_correct=True,
        position=1,
    )
    incorrect_choice = AnswerChoice(
        question_id=question.id,
        text="Incorrect",
        is_correct=False,
        position=2,
    )
    db.add_all([correct_choice, incorrect_choice])
    db.commit()

    return quiz, question, correct_choice, incorrect_choice


def create_attempt(
    db,
    *,
    user: User,
    quiz: Quiz,
    question: Question,
    choice: AnswerChoice,
) -> QuizAttempt:
    attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=user.id,
    )
    db.add(attempt)
    db.flush()

    answer = QuizAttemptAnswer(
        attempt_id=attempt.id,
        question_id=question.id,
        selected_choice_id=choice.id,
    )
    db.add(answer)
    db.commit()

    return attempt


def test_get_user_quiz_summaries_returns_empty_for_no_attempts(db):
    user = create_user(
        db,
        display_name="Empty User",
        email="chatbot-empty@example.com",
    )

    summaries = get_user_quiz_summaries(
        db,
        user_id=user.id,
    )

    assert summaries == []


def test_get_user_quiz_summaries_groups_attempts_and_scores(db):
    creator = create_user(
        db,
        display_name="Quiz Creator",
        email="chatbot-creator@example.com",
    )
    learner = create_user(
        db,
        display_name="Quiz Learner",
        email="chatbot-learner@example.com",
    )

    quiz, question, correct_choice, incorrect_choice = create_quiz(
        db,
        owner=creator,
        title="Python Basics",
        category="Programming",
    )

    create_attempt(
        db,
        user=learner,
        quiz=quiz,
        question=question,
        choice=correct_choice,
    )
    create_attempt(
        db,
        user=learner,
        quiz=quiz,
        question=question,
        choice=incorrect_choice,
    )
    create_attempt(
        db,
        user=learner,
        quiz=quiz,
        question=question,
        choice=correct_choice,
    )

    summaries = get_user_quiz_summaries(
        db,
        user_id=learner.id,
    )

    assert len(summaries) == 1

    summary = summaries[0]

    assert summary.quiz_id == quiz.id
    assert summary.title == "Python Basics"
    assert summary.creator_name == "Quiz Creator"
    assert summary.category == "Programming"
    assert summary.attempt_count == 3
    assert summary.average_score == 66.67


def test_get_user_quiz_summaries_only_returns_requested_users_data(db):
    creator = create_user(
        db,
        display_name="Shared Creator",
        email="chatbot-shared-creator@example.com",
    )
    first_user = create_user(
        db,
        display_name="First Learner",
        email="chatbot-first@example.com",
    )
    second_user = create_user(
        db,
        display_name="Second Learner",
        email="chatbot-second@example.com",
    )

    first_quiz, first_question, first_correct, _ = create_quiz(
        db,
        owner=creator,
        title="Python Quiz",
        category="Programming",
    )
    second_quiz, second_question, second_correct, _ = create_quiz(
        db,
        owner=creator,
        title="Biology Quiz",
        category="Science",
    )

    create_attempt(
        db,
        user=first_user,
        quiz=first_quiz,
        question=first_question,
        choice=first_correct,
    )

    create_attempt(
        db,
        user=second_user,
        quiz=second_quiz,
        question=second_question,
        choice=second_correct,
    )

    summaries = get_user_quiz_summaries(
        db,
        user_id=first_user.id,
    )

    assert len(summaries) == 1
    assert summaries[0].quiz_id == first_quiz.id
    assert summaries[0].title == "Python Quiz"

    returned_ids = {
        summary.quiz_id
        for summary in summaries
    }

    assert second_quiz.id not in returned_ids


def test_get_user_quiz_summaries_includes_multiple_quizzes(db):
    creator = create_user(
        db,
        display_name="Multiple Creator",
        email="chatbot-multiple-creator@example.com",
    )
    learner = create_user(
        db,
        display_name="Multiple Learner",
        email="chatbot-multiple-learner@example.com",
    )

    python_quiz, python_question, python_correct, _ = create_quiz(
        db,
        owner=creator,
        title="Python",
        category="Programming",
    )
    math_quiz, math_question, _, math_incorrect = create_quiz(
        db,
        owner=creator,
        title="Algebra",
        category="Mathematics",
    )

    create_attempt(
        db,
        user=learner,
        quiz=python_quiz,
        question=python_question,
        choice=python_correct,
    )
    create_attempt(
        db,
        user=learner,
        quiz=math_quiz,
        question=math_question,
        choice=math_incorrect,
    )

    summaries = get_user_quiz_summaries(
        db,
        user_id=learner.id,
    )

    assert len(summaries) == 2

    summaries_by_title = {
        summary.title: summary
        for summary in summaries
    }

    assert summaries_by_title["Python"].average_score == 100.0
    assert summaries_by_title["Python"].attempt_count == 1

    assert summaries_by_title["Algebra"].average_score == 0.0
    assert summaries_by_title["Algebra"].attempt_count == 1


def test_get_user_attempt_rows_returns_one_row_per_attempt(db):
    creator = create_user(
        db,
        display_name="Attempt Creator",
        email="chatbot-attempt-creator@example.com",
    )
    learner = create_user(
        db,
        display_name="Attempt Learner",
        email="chatbot-attempt-learner@example.com",
    )

    quiz, question, correct_choice, incorrect_choice = create_quiz(
        db,
        owner=creator,
        title="Python Fundamentals",
        category="Programming",
    )

    create_attempt(
        db,
        user=learner,
        quiz=quiz,
        question=question,
        choice=correct_choice,
    )
    create_attempt(
        db,
        user=learner,
        quiz=quiz,
        question=question,
        choice=incorrect_choice,
    )

    rows = get_user_attempt_rows(
        db,
        user_id=learner.id,
    )

    assert len(rows) == 2

    assert all(
        row.quiz_id == quiz.id
        for row in rows
    )
    assert all(
        row.quiz_title == "Python Fundamentals"
        for row in rows
    )
    assert all(
        row.creator_name == "Attempt Creator"
        for row in rows
    )
    assert all(
        row.category == "Programming"
        for row in rows
    )

    scores = sorted(
        row.score_percentage
        for row in rows
        if row.score_percentage is not None
    )

    assert scores == [0.0, 100.0]
    assert all(row.submitted_at is not None for row in rows)


def test_get_user_attempt_rows_only_returns_requested_users_attempts(db):
    creator = create_user(
        db,
        display_name="Isolation Creator",
        email="chatbot-row-creator@example.com",
    )
    first_user = create_user(
        db,
        display_name="Row User One",
        email="chatbot-row-first@example.com",
    )
    second_user = create_user(
        db,
        display_name="Row User Two",
        email="chatbot-row-second@example.com",
    )

    first_quiz, first_question, first_correct, _ = create_quiz(
        db,
        owner=creator,
        title="Private Python History",
        category="Programming",
    )
    second_quiz, second_question, second_correct, _ = create_quiz(
        db,
        owner=creator,
        title="Other User Biology",
        category="Science",
    )

    first_attempt = create_attempt(
        db,
        user=first_user,
        quiz=first_quiz,
        question=first_question,
        choice=first_correct,
    )

    second_attempt = create_attempt(
        db,
        user=second_user,
        quiz=second_quiz,
        question=second_question,
        choice=second_correct,
    )

    rows = get_user_attempt_rows(
        db,
        user_id=first_user.id,
    )

    assert len(rows) == 1
    assert rows[0].attempt_id == first_attempt.id
    assert rows[0].quiz_id == first_quiz.id
    assert rows[0].quiz_title == "Private Python History"

    returned_attempt_ids = {
        row.attempt_id
        for row in rows
    }
    returned_quiz_ids = {
        row.quiz_id
        for row in rows
    }

    assert second_attempt.id not in returned_attempt_ids
    assert second_quiz.id not in returned_quiz_ids


def test_get_user_attempt_rows_returns_empty_for_no_attempts(db):
    learner = create_user(
        db,
        display_name="No Attempt Rows",
        email="chatbot-no-attempt-rows@example.com",
    )

    rows = get_user_attempt_rows(
        db,
        user_id=learner.id,
    )

    assert rows == []

def test_get_user_question_performance_rows_tracks_correct_and_incorrect(db):
    creator = create_user(
        db,
        display_name="Question Creator",
        email="chatbot-question-creator@example.com",
    )
    learner = create_user(
        db,
        display_name="Question Learner",
        email="chatbot-question-learner@example.com",
    )

    quiz, question, correct_choice, incorrect_choice = create_quiz(
        db,
        owner=creator,
        title="Python Questions",
        category="Programming",
    )

    correct_attempt = create_attempt(
        db,
        user=learner,
        quiz=quiz,
        question=question,
        choice=correct_choice,
    )
    incorrect_attempt = create_attempt(
        db,
        user=learner,
        quiz=quiz,
        question=question,
        choice=incorrect_choice,
    )

    rows = get_user_question_performance_rows(
        db,
        user_id=learner.id,
    )

    assert len(rows) == 2

    rows_by_attempt = {
        row.attempt_id: row
        for row in rows
    }

    assert rows_by_attempt[correct_attempt.id].is_correct is True
    assert rows_by_attempt[incorrect_attempt.id].is_correct is False

    assert all(
        row.quiz_id == quiz.id
        for row in rows
    )
    assert all(
        row.quiz_title == "Python Questions"
        for row in rows
    )
    assert all(
        row.question_id == question.id
        for row in rows
    )
    assert all(
        row.question_text == "Python Questions question"
        for row in rows
    )
    assert all(
        row.question_type == "multiple_choice"
        for row in rows
    )
    assert all(
        row.submitted_at is not None
        for row in rows
    )


def test_get_user_question_performance_rows_preserves_repeated_misses(db):
    creator = create_user(
        db,
        display_name="Repeated Miss Creator",
        email="chatbot-repeated-miss-creator@example.com",
    )
    learner = create_user(
        db,
        display_name="Repeated Miss Learner",
        email="chatbot-repeated-miss-learner@example.com",
    )

    quiz, question, correct_choice, incorrect_choice = create_quiz(
        db,
        owner=creator,
        title="JavaScript Fundamentals",
        category="Programming",
    )

    create_attempt(
        db,
        user=learner,
        quiz=quiz,
        question=question,
        choice=incorrect_choice,
    )
    create_attempt(
        db,
        user=learner,
        quiz=quiz,
        question=question,
        choice=incorrect_choice,
    )
    create_attempt(
        db,
        user=learner,
        quiz=quiz,
        question=question,
        choice=correct_choice,
    )

    rows = get_user_question_performance_rows(
        db,
        user_id=learner.id,
    )

    assert len(rows) == 3

    incorrect_rows = [
        row
        for row in rows
        if not row.is_correct
    ]

    assert len(incorrect_rows) == 2
    assert all(
        row.question_id == question.id
        for row in incorrect_rows
    )


def test_get_user_question_performance_rows_is_user_scoped(db):
    creator = create_user(
        db,
        display_name="Scoped Question Creator",
        email="chatbot-scoped-question-creator@example.com",
    )
    first_user = create_user(
        db,
        display_name="Scoped Learner One",
        email="chatbot-scoped-question-one@example.com",
    )
    second_user = create_user(
        db,
        display_name="Scoped Learner Two",
        email="chatbot-scoped-question-two@example.com",
    )

    quiz, question, correct_choice, incorrect_choice = create_quiz(
        db,
        owner=creator,
        title="Scoped Quiz",
        category="Science",
    )

    first_attempt = create_attempt(
        db,
        user=first_user,
        quiz=quiz,
        question=question,
        choice=incorrect_choice,
    )
    second_attempt = create_attempt(
        db,
        user=second_user,
        quiz=quiz,
        question=question,
        choice=correct_choice,
    )

    rows = get_user_question_performance_rows(
        db,
        user_id=first_user.id,
    )

    assert len(rows) == 1
    assert rows[0].attempt_id == first_attempt.id
    assert rows[0].is_correct is False

    returned_attempt_ids = {
        row.attempt_id
        for row in rows
    }

    assert second_attempt.id not in returned_attempt_ids

