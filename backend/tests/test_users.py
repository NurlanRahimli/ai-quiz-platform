import uuid
from tests.conftest import register_verified_user


def register_and_login(
    client,
    email="user@example.com",
    password="Testing123!",
    display_name="Quiz User",
):
    user = register_verified_user(
        client,
        email=email,
        display_name=display_name,
        password=password,
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return user, {
        "Authorization": f"Bearer {token}",
    }


def test_public_user_profile_returns_only_public_quizzes(client):
    creator, creator_headers = register_and_login(
        client,
        email="public-profile-creator@example.com",
        display_name="Public Creator",
    )

    public_response = client.post(
        "/api/v1/quizzes",
        headers=creator_headers,
        json={
            "title": "Visible Public Quiz",
            "description": "Everyone can discover this quiz.",
            "category": "Programming",
            "tags": ["Python", "Public"],
            "visibility": "public",
        },
    )
    assert public_response.status_code == 201

    unlisted_response = client.post(
        "/api/v1/quizzes",
        headers=creator_headers,
        json={
            "title": "Hidden Unlisted Quiz",
            "visibility": "unlisted",
        },
    )
    assert unlisted_response.status_code == 201

    _, viewer_headers = register_and_login(
        client,
        email="public-profile-viewer@example.com",
        display_name="Profile Viewer",
    )

    response = client.get(
        f"/api/v1/users/{creator['id']}/profile",
        headers=viewer_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == creator["id"]
    assert data["display_name"] == "Public Creator"
    assert "created_at" in data
    assert data["public_quiz_count"] == 1
    assert data["is_following"] is False

    assert "email" not in data
    assert "is_active" not in data

    assert len(data["quizzes"]) == 1

    quiz = data["quizzes"][0]

    assert quiz["title"] == "Visible Public Quiz"
    assert quiz["visibility"] == "public"
    assert quiz["creator_name"] == "Public Creator"
    assert quiz["category"] == "Programming"
    assert quiz["tags"] == ["Python", "Public"]
    assert quiz["question_count"] == 0
    assert quiz["attempt_count"] == 0

    quiz_titles = {
        item["title"]
        for item in data["quizzes"]
    }

    assert "Hidden Unlisted Quiz" not in quiz_titles


def test_public_user_profile_returns_404_for_unknown_user(client):
    _, headers = register_and_login(
        client,
        email="unknown-profile-viewer@example.com",
    )

    response = client.get(
        f"/api/v1/users/{uuid.uuid4()}/profile",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_public_user_profile_paginates_public_quizzes(client):
    creator, creator_headers = register_and_login(
        client,
        email="paginated-profile-creator@example.com",
        display_name="Pagination Creator",
    )

    for index in range(21):
        response = client.post(
            "/api/v1/quizzes",
            headers=creator_headers,
            json={
                "title": f"Public Quiz {index + 1:02d}",
                "visibility": "public",
            },
        )
        assert response.status_code == 201

    unlisted_response = client.post(
        "/api/v1/quizzes",
        headers=creator_headers,
        json={
            "title": "Unlisted Quiz",
            "visibility": "unlisted",
        },
    )
    assert unlisted_response.status_code == 201

    _, viewer_headers = register_and_login(
        client,
        email="paginated-profile-viewer@example.com",
        display_name="Pagination Viewer",
    )

    page_one_response = client.get(
        f"/api/v1/users/{creator['id']}/profile",
        headers=viewer_headers,
        params={
            "page": 1,
            "page_size": 10,
        },
    )

    assert page_one_response.status_code == 200

    page_one = page_one_response.json()

    assert page_one["public_quiz_count"] == 21
    assert page_one["page"] == 1
    assert page_one["page_size"] == 10
    assert page_one["total_pages"] == 3
    assert len(page_one["quizzes"]) == 10

    page_two_response = client.get(
        f"/api/v1/users/{creator['id']}/profile",
        headers=viewer_headers,
        params={
            "page": 2,
            "page_size": 10,
        },
    )

    assert page_two_response.status_code == 200

    page_two = page_two_response.json()

    assert page_two["public_quiz_count"] == 21
    assert page_two["page"] == 2
    assert page_two["page_size"] == 10
    assert page_two["total_pages"] == 3
    assert len(page_two["quizzes"]) == 10

    page_three_response = client.get(
        f"/api/v1/users/{creator['id']}/profile",
        headers=viewer_headers,
        params={
            "page": 3,
            "page_size": 10,
        },
    )

    assert page_three_response.status_code == 200

    page_three = page_three_response.json()

    assert page_three["public_quiz_count"] == 21
    assert page_three["page"] == 3
    assert page_three["page_size"] == 10
    assert page_three["total_pages"] == 3
    assert len(page_three["quizzes"]) == 1

    page_one_ids = {
        quiz["id"]
        for quiz in page_one["quizzes"]
    }
    page_two_ids = {
        quiz["id"]
        for quiz in page_two["quizzes"]
    }
    page_three_ids = {
        quiz["id"]
        for quiz in page_three["quizzes"]
    }

    assert page_one_ids.isdisjoint(page_two_ids)
    assert page_one_ids.isdisjoint(page_three_ids)
    assert page_two_ids.isdisjoint(page_three_ids)

    all_titles = {
        quiz["title"]
        for quiz in (
            page_one["quizzes"]
            + page_two["quizzes"]
            + page_three["quizzes"]
        )
    }

    assert "Unlisted Quiz" not in all_titles


def test_current_user_quizzes_are_paginated(client):
    _, headers = register_and_login(
        client,
        email="private-profile-pagination@example.com",
        display_name="Private Profile Creator",
    )

    for index in range(21):
        response = client.post(
            "/api/v1/quizzes",
            headers=headers,
            json={
                "title": f"My Quiz {index + 1:02d}",
                "visibility": (
                    "public"
                    if index % 2 == 0
                    else "unlisted"
                ),
            },
        )
        assert response.status_code == 201

    page_one_response = client.get(
        "/api/v1/users/me/quizzes",
        headers=headers,
        params={
            "page": 1,
            "page_size": 10,
        },
    )

    assert page_one_response.status_code == 200

    page_one = page_one_response.json()

    assert page_one["total"] == 21
    assert page_one["page"] == 1
    assert page_one["page_size"] == 10
    assert page_one["total_pages"] == 3
    assert len(page_one["quizzes"]) == 10

    page_two_response = client.get(
        "/api/v1/users/me/quizzes",
        headers=headers,
        params={
            "page": 2,
            "page_size": 10,
        },
    )

    assert page_two_response.status_code == 200

    page_two = page_two_response.json()

    assert page_two["total"] == 21
    assert page_two["page"] == 2
    assert page_two["page_size"] == 10
    assert page_two["total_pages"] == 3
    assert len(page_two["quizzes"]) == 10

    page_three_response = client.get(
        "/api/v1/users/me/quizzes",
        headers=headers,
        params={
            "page": 3,
            "page_size": 10,
        },
    )

    assert page_three_response.status_code == 200

    page_three = page_three_response.json()

    assert page_three["total"] == 21
    assert page_three["page"] == 3
    assert page_three["page_size"] == 10
    assert page_three["total_pages"] == 3
    assert len(page_three["quizzes"]) == 1

    page_one_ids = {
        quiz["id"]
        for quiz in page_one["quizzes"]
    }
    page_two_ids = {
        quiz["id"]
        for quiz in page_two["quizzes"]
    }
    page_three_ids = {
        quiz["id"]
        for quiz in page_three["quizzes"]
    }

    assert page_one_ids.isdisjoint(page_two_ids)
    assert page_one_ids.isdisjoint(page_three_ids)
    assert page_two_ids.isdisjoint(page_three_ids)

    all_quizzes = (
        page_one["quizzes"]
        + page_two["quizzes"]
        + page_three["quizzes"]
    )

    assert len(all_quizzes) == 21

    visibilities = {
        quiz["visibility"]
        for quiz in all_quizzes
    }

    assert visibilities == {"public", "unlisted"}


def test_user_can_follow_creator_and_duplicate_follow_is_idempotent(client):
    creator, _ = register_and_login(
        client,
        email="follow-creator@example.com",
        display_name="Follow Creator",
    )
    follower, follower_headers = register_and_login(
        client,
        email="follower@example.com",
        display_name="Follower",
    )

    response = client.post(
        f"/api/v1/users/{creator['id']}/follow",
        headers=follower_headers,
    )

    assert response.status_code == 200
    assert response.json() == {
        "user_id": creator["id"],
        "is_following": True,
    }

    duplicate_response = client.post(
        f"/api/v1/users/{creator['id']}/follow",
        headers=follower_headers,
    )

    assert duplicate_response.status_code == 200
    assert duplicate_response.json() == {
        "user_id": creator["id"],
        "is_following": True,
    }

    assert follower["id"] != creator["id"]


def test_user_cannot_follow_themselves(client):
    user, headers = register_and_login(
        client,
        email="self-follow@example.com",
        display_name="Self Follow User",
    )

    response = client.post(
        f"/api/v1/users/{user['id']}/follow",
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "You cannot follow yourself"


def test_follow_returns_404_for_unknown_user(client):
    _, headers = register_and_login(
        client,
        email="unknown-follow@example.com",
        display_name="Unknown Follow User",
    )

    response = client.post(
        f"/api/v1/users/{uuid.uuid4()}/follow",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_follow_requires_authentication(client):
    response = client.post(
        f"/api/v1/users/{uuid.uuid4()}/follow",
    )

    assert response.status_code in {401, 403}


def test_user_can_unfollow_creator_and_duplicate_unfollow_is_idempotent(client):
    creator, _ = register_and_login(
        client,
        email="unfollow-creator@example.com",
        display_name="Unfollow Creator",
    )
    _, follower_headers = register_and_login(
        client,
        email="unfollow-follower@example.com",
        display_name="Unfollow Follower",
    )

    follow_response = client.post(
        f"/api/v1/users/{creator['id']}/follow",
        headers=follower_headers,
    )

    assert follow_response.status_code == 200
    assert follow_response.json()["is_following"] is True

    unfollow_response = client.delete(
        f"/api/v1/users/{creator['id']}/follow",
        headers=follower_headers,
    )

    assert unfollow_response.status_code == 200
    assert unfollow_response.json() == {
        "user_id": creator["id"],
        "is_following": False,
    }

    duplicate_unfollow_response = client.delete(
        f"/api/v1/users/{creator['id']}/follow",
        headers=follower_headers,
    )

    assert duplicate_unfollow_response.status_code == 200
    assert duplicate_unfollow_response.json() == {
        "user_id": creator["id"],
        "is_following": False,
    }


def test_user_cannot_unfollow_themselves(client):
    user, headers = register_and_login(
        client,
        email="self-unfollow@example.com",
        display_name="Self Unfollow User",
    )

    response = client.delete(
        f"/api/v1/users/{user['id']}/follow",
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "You cannot unfollow yourself"


def test_public_profile_reflects_follow_state(client):
    creator, _ = register_and_login(
        client,
        email="follow-state-creator@example.com",
        display_name="Follow State Creator",
    )
    _, viewer_headers = register_and_login(
        client,
        email="follow-state-viewer@example.com",
        display_name="Follow State Viewer",
    )

    profile_before_follow = client.get(
        f"/api/v1/users/{creator['id']}/profile",
        headers=viewer_headers,
    )

    assert profile_before_follow.status_code == 200
    assert profile_before_follow.json()["is_following"] is False
    assert profile_before_follow.json()["follower_count"] == 0

    follow_response = client.post(
        f"/api/v1/users/{creator['id']}/follow",
        headers=viewer_headers,
    )

    assert follow_response.status_code == 200
    assert follow_response.json()["is_following"] is True

    profile_after_follow = client.get(
        f"/api/v1/users/{creator['id']}/profile",
        headers=viewer_headers,
    )

    assert profile_after_follow.status_code == 200
    assert profile_after_follow.json()["is_following"] is True
    assert profile_after_follow.json()["follower_count"] == 1

    unfollow_response = client.delete(
        f"/api/v1/users/{creator['id']}/follow",
        headers=viewer_headers,
    )

    assert unfollow_response.status_code == 200
    assert unfollow_response.json()["is_following"] is False

    profile_after_unfollow = client.get(
        f"/api/v1/users/{creator['id']}/profile",
        headers=viewer_headers,
    )

    assert profile_after_unfollow.status_code == 200
    assert profile_after_unfollow.json()["is_following"] is False
    assert profile_after_unfollow.json()["follower_count"] == 0