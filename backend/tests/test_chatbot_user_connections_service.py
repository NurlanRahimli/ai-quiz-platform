from app.models.user import User
from app.models.user_follow import UserFollow
from app.services.chatbot_user_connections_service import (
    count_user_connections,
    list_user_connections,
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


def _follow(
    db,
    *,
    follower: User,
    following: User,
) -> None:
    db.add(
        UserFollow(
            follower_id=follower.id,
            following_id=following.id,
        )
    )
    db.commit()


def test_count_user_connections_counts_followers(db):
    user = _create_user(
        db,
        email="target@example.com",
        display_name="Target",
    )
    follower_one = _create_user(
        db,
        email="follower1@example.com",
        display_name="Follower One",
    )
    follower_two = _create_user(
        db,
        email="follower2@example.com",
        display_name="Follower Two",
    )

    _follow(
        db,
        follower=follower_one,
        following=user,
    )
    _follow(
        db,
        follower=follower_two,
        following=user,
    )

    result = count_user_connections(
        db,
        user_id=user.id,
        direction="followers",
    )

    assert result == 2


def test_count_user_connections_counts_following(db):
    user = _create_user(
        db,
        email="following-target@example.com",
        display_name="Target",
    )
    person_one = _create_user(
        db,
        email="person1@example.com",
        display_name="Person One",
    )
    person_two = _create_user(
        db,
        email="person2@example.com",
        display_name="Person Two",
    )

    _follow(
        db,
        follower=user,
        following=person_one,
    )
    _follow(
        db,
        follower=user,
        following=person_two,
    )

    result = count_user_connections(
        db,
        user_id=user.id,
        direction="following",
    )

    assert result == 2


def test_list_user_connections_returns_followers(db):
    user = _create_user(
        db,
        email="list-followers@example.com",
        display_name="Target",
    )
    follower_one = _create_user(
        db,
        email="list-follower1@example.com",
        display_name="Follower One",
    )
    follower_two = _create_user(
        db,
        email="list-follower2@example.com",
        display_name="Follower Two",
    )

    _follow(
        db,
        follower=follower_one,
        following=user,
    )
    _follow(
        db,
        follower=follower_two,
        following=user,
    )

    result = list_user_connections(
        db,
        user_id=user.id,
        direction="followers",
    )

    assert len(result) == 2

    assert {
        item.id
        for item in result
    } == {
        follower_one.id,
        follower_two.id,
    }


def test_list_user_connections_returns_following(db):
    user = _create_user(
        db,
        email="list-following@example.com",
        display_name="Target",
    )
    person_one = _create_user(
        db,
        email="list-person1@example.com",
        display_name="Person One",
    )
    person_two = _create_user(
        db,
        email="list-person2@example.com",
        display_name="Person Two",
    )

    _follow(
        db,
        follower=user,
        following=person_one,
    )
    _follow(
        db,
        follower=user,
        following=person_two,
    )

    result = list_user_connections(
        db,
        user_id=user.id,
        direction="following",
    )

    assert len(result) == 2

    assert {
        item.id
        for item in result
    } == {
        person_one.id,
        person_two.id,
    }


def test_list_user_connections_respects_limit(db):
    user = _create_user(
        db,
        email="limit-target@example.com",
        display_name="Target",
    )

    for index in range(5):
        follower = _create_user(
            db,
            email=f"limit-follower-{index}@example.com",
            display_name=f"Follower {index}",
        )
        _follow(
            db,
            follower=follower,
            following=user,
        )

    result = list_user_connections(
        db,
        user_id=user.id,
        direction="followers",
        limit=3,
    )

    assert len(result) == 3


def test_count_user_connections_returns_zero(db):
    user = _create_user(
        db,
        email="empty-connections@example.com",
        display_name="Empty",
    )

    followers = count_user_connections(
        db,
        user_id=user.id,
        direction="followers",
    )
    following = count_user_connections(
        db,
        user_id=user.id,
        direction="following",
    )

    assert followers == 0
    assert following == 0
