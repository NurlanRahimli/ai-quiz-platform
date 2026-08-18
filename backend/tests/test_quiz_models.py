from sqlalchemy import select

from app.models.answer_choice import AnswerChoice
from app.models.question import Question
from app.models.quiz import Quiz
from app.models.user import User
from app.core.security import hash_password


def create_user(db):
    user = User(
        email="quiz-owner@example.com",
        password_hash=hash_password("Testing123!"),
        display_name="Quiz Owner",
    )
    db.add(user)
    db.flush()
    return user


def test_create_quiz_with_question_and_answer_choices(db):
    user = create_user(db)

    quiz = Quiz(
        owner_id=user.id,
        title="Math Quiz",
        description="Basic arithmetic",
    )

    question = Question(
        text="What is 2 + 2?",
        question_type="multiple_choice",
        position=1,
    )

    question.answer_choices = [
        AnswerChoice(
            text="3",
            is_correct=False,
            position=1,
        ),
        AnswerChoice(
            text="4",
            is_correct=True,
            position=2,
        ),
    ]

    quiz.questions.append(question)

    db.add(quiz)
    db.commit()

    saved_quiz = db.scalar(
        select(Quiz).where(Quiz.id == quiz.id)
    )

    assert saved_quiz is not None
    assert saved_quiz.owner_id == user.id
    assert saved_quiz.title == "Math Quiz"
    assert len(saved_quiz.questions) == 1

    saved_question = saved_quiz.questions[0]

    assert saved_question.text == "What is 2 + 2?"
    assert saved_question.question_type == "multiple_choice"
    assert len(saved_question.answer_choices) == 2

    correct_choice = next(
        choice
        for choice in saved_question.answer_choices
        if choice.is_correct
    )

    assert correct_choice.text == "4"


def test_deleting_quiz_deletes_questions_and_choices(db):
    user = create_user(db)

    quiz = Quiz(
        owner_id=user.id,
        title="Delete Me",
    )

    question = Question(
        text="Temporary question",
        question_type="multiple_choice",
        position=1,
    )

    choice = AnswerChoice(
        text="Temporary answer",
        is_correct=True,
        position=1,
    )

    question.answer_choices.append(choice)
    quiz.questions.append(question)

    db.add(quiz)
    db.commit()

    question_id = question.id
    choice_id = choice.id

    db.delete(quiz)
    db.commit()

    assert db.get(Question, question_id) is None
    assert db.get(AnswerChoice, choice_id) is None