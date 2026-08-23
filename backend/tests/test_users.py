import uuid


def register_and_login(
    client,
    email="user@example.com",
    password="Testing123!",
    display_name="Quiz User",
):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "display_name": display_name,
            "email": email,
            "password": password,
        },
    )
    assert register_response.status_code == 201

    user = register_response.json()

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