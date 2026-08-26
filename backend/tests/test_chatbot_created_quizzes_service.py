import uuid

from app.models.quiz import Quiz
from app.models.user import User
from app.services.chatbot_created_quizzes_service import (
    count_user_created_quizzes,
    list_user_created_quizzes,
)


def _create_user(
    db,
    *,
    email: str,
    display_name: str,
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


def _create_quiz(
    db,
    *,
    owner_id: uuid.UUID,
    title: str,
    visibility: str = "unlisted",
) -> Quiz:
    quiz = Quiz(
        owner_id=owner_id,
        title=title,
        visibility=visibility,
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    return quiz


def test_count_user_created_quizzes_only_counts_owned_quizzes(
    db,
):
    user = _create_user(
        db,
        email="creator@example.com",
        display_name="Creator",
    )
    other_user = _create_user(
        db,
        email="other@example.com",
        display_name="Other",
    )

    _create_quiz(
        db,
        owner_id=user.id,
        title="Quiz 1",
    )
    _create_quiz(
        db,
        owner_id=user.id,
        title="Quiz 2",
    )
    _create_quiz(
        db,
        owner_id=other_user.id,
        title="Someone Else's Quiz",
    )

    result = count_user_created_quizzes(
        db,
        user_id=user.id,
    )

    assert result == 2


def test_count_user_created_quizzes_returns_zero(
    db,
):
    user = _create_user(
        db,
        email="empty@example.com",
        display_name="Empty",
    )

    result = count_user_created_quizzes(
        db,
        user_id=user.id,
    )

    assert result == 0


def test_list_user_created_quizzes_only_returns_owned_quizzes(
    db,
):
    user = _create_user(
        db,
        email="list-creator@example.com",
        display_name="List Creator",
    )
    other_user = _create_user(
        db,
        email="list-other@example.com",
        display_name="List Other",
    )

    _create_quiz(
        db,
        owner_id=user.id,
        title="My First Quiz",
    )
    _create_quiz(
        db,
        owner_id=user.id,
        title="My Second Quiz",
    )
    _create_quiz(
        db,
        owner_id=other_user.id,
        title="Someone Else's Quiz",
    )

    result = list_user_created_quizzes(
        db,
        user_id=user.id,
        limit=10,
    )

    assert len(result) == 2
    assert {
        quiz.title
        for quiz in result
    } == {
        "My First Quiz",
        "My Second Quiz",
    }
    assert all(
        quiz.owner_id == user.id
        for quiz in result
    )


def test_list_user_created_quizzes_respects_limit(
    db,
):
    user = _create_user(
        db,
        email="limit-creator@example.com",
        display_name="Limit Creator",
    )

    for index in range(5):
        _create_quiz(
            db,
            owner_id=user.id,
            title=f"Quiz {index + 1}",
        )

    result = list_user_created_quizzes(
        db,
        user_id=user.id,
        limit=3,
    )

    assert len(result) == 3


def test_list_user_created_quizzes_returns_empty_list(
    db,
):
    user = _create_user(
        db,
        email="no-quizzes@example.com",
        display_name="No Quizzes",
    )

    result = list_user_created_quizzes(
        db,
        user_id=user.id,
    )

    assert result == []




def test_count_user_created_quizzes_filters_by_visibility(
    db,
):
    user = _create_user(
        db,
        email="visibility-count@example.com",
        display_name="Visibility Count",
    )

    _create_quiz(
        db,
        owner_id=user.id,
        title="Public Quiz 1",
        visibility="public",
    )
    _create_quiz(
        db,
        owner_id=user.id,
        title="Public Quiz 2",
        visibility="public",
    )
    _create_quiz(
        db,
        owner_id=user.id,
        title="Unlisted Quiz",
        visibility="unlisted",
    )

    public_count = count_user_created_quizzes(
        db,
        user_id=user.id,
        visibility="public",
    )

    unlisted_count = count_user_created_quizzes(
        db,
        user_id=user.id,
        visibility="unlisted",
    )

    assert public_count == 2
    assert unlisted_count == 1


def test_list_user_created_quizzes_filters_by_visibility(
    db,
):
    user = _create_user(
        db,
        email="visibility-list@example.com",
        display_name="Visibility List",
    )

    _create_quiz(
        db,
        owner_id=user.id,
        title="Public Quiz 1",
        visibility="public",
    )
    _create_quiz(
        db,
        owner_id=user.id,
        title="Public Quiz 2",
        visibility="public",
    )
    _create_quiz(
        db,
        owner_id=user.id,
        title="Unlisted Quiz",
        visibility="unlisted",
    )

    result = list_user_created_quizzes(
        db,
        user_id=user.id,
        visibility="public",
        limit=10,
    )

    assert len(result) == 2

    assert {
        quiz.title
        for quiz in result
    } == {
        "Public Quiz 1",
        "Public Quiz 2",
    }

    assert all(
        quiz.visibility == "public"
        for quiz in result
    )


def test_list_created_quizzes_filters_by_category(db):
    user = _create_user(
        db,
        email="category@example.com",
        display_name="Category User",
    )

    language = _create_quiz(
        db,
        owner_id=user.id,
        title="English Grammar",
    )
    language.category = "Language"

    science = _create_quiz(
        db,
        owner_id=user.id,
        title="Human Body",
    )
    science.category = "Science"

    db.commit()

    result = list_user_created_quizzes(
        db,
        user_id=user.id,
        category="language",
    )

    assert len(result) == 1
    assert result[0].title == "English Grammar"


def test_count_created_quizzes_filters_by_category(db):
    user = _create_user(
        db,
        email="category-count@example.com",
        display_name="Category Count",
    )

    first = _create_quiz(
        db,
        owner_id=user.id,
        title="English 1",
    )
    first.category = "Language"

    second = _create_quiz(
        db,
        owner_id=user.id,
        title="English 2",
    )
    second.category = "Language"

    third = _create_quiz(
        db,
        owner_id=user.id,
        title="Science",
    )
    third.category = "Science"

    db.commit()

    result = count_user_created_quizzes(
        db,
        user_id=user.id,
        category="Language",
    )

    assert result == 2


def test_list_created_quizzes_combines_filters(db):
    user = _create_user(
        db,
        email="combined@example.com",
        display_name="Combined User",
    )

    matching = _create_quiz(
        db,
        owner_id=user.id,
        title="Public English",
    )
    matching.category = "Language"
    matching.visibility = "public"

    wrong_visibility = _create_quiz(
        db,
        owner_id=user.id,
        title="Private English",
    )
    wrong_visibility.category = "Language"
    wrong_visibility.visibility = "unlisted"

    wrong_category = _create_quiz(
        db,
        owner_id=user.id,
        title="Public Science",
    )
    wrong_category.category = "Science"
    wrong_category.visibility = "public"

    db.commit()

    result = list_user_created_quizzes(
        db,
        user_id=user.id,
        visibility="public",
        category="Language",
    )

    assert len(result) == 1
    assert result[0].title == "Public English"


def test_list_created_quizzes_searches_title(db):
    user = _create_user(
        db,
        email="title-search@example.com",
        display_name="Title Search",
    )

    _create_quiz(
        db,
        owner_id=user.id,
        title="Python Fundamentals",
    )
    _create_quiz(
        db,
        owner_id=user.id,
        title="JavaScript Fundamentals",
    )

    result = list_user_created_quizzes(
        db,
        user_id=user.id,
        title_search="python",
    )

    assert len(result) == 1
    assert result[0].title == "Python Fundamentals"


def test_list_created_quizzes_supports_oldest_first(db):
    user = _create_user(
        db,
        email="ordering@example.com",
        display_name="Ordering User",
    )

    first = _create_quiz(
        db,
        owner_id=user.id,
        title="First Quiz",
    )
    second = _create_quiz(
        db,
        owner_id=user.id,
        title="Second Quiz",
    )

    from datetime import datetime, timezone

    first.created_at = datetime(
        2026, 1, 1,
        tzinfo=timezone.utc,
    )
    second.created_at = datetime(
        2026, 2, 1,
        tzinfo=timezone.utc,
    )
    db.commit()

    result = list_user_created_quizzes(
        db,
        user_id=user.id,
        sort_direction="asc",
        limit=1,
    )

    assert len(result) == 1
    assert result[0].title == "First Quiz"
