from datetime import datetime, timezone
from tests.conftest import register_verified_user

def register_and_login(
    client,
    email="audit-log-user@example.com",
    password="Testing123!",
    display_name="Audit User",
):
    register_verified_user(
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

    return {
        "Authorization": (
            f"Bearer {login_response.json()['access_token']}"
        ),
    }


def test_audit_logs_require_authentication(client):
    response = client.get("/api/v1/audit-logs")

    assert response.status_code == 401


def test_audit_logs_return_only_current_users_activity(client):
    first_headers = register_and_login(
        client,
        email="audit-first@example.com",
        display_name="First User",
    )

    second_headers = register_and_login(
        client,
        email="audit-second@example.com",
        display_name="Second User",
    )

    first_quiz_response = client.post(
        "/api/v1/quizzes",
        headers=first_headers,
        json={
            "title": "First User Quiz",
            "visibility": "public",
        },
    )
    assert first_quiz_response.status_code == 201

    second_quiz_response = client.post(
        "/api/v1/quizzes",
        headers=second_headers,
        json={
            "title": "Second User Quiz",
            "visibility": "public",
        },
    )
    assert second_quiz_response.status_code == 201

    response = client.get(
        "/api/v1/audit-logs",
        headers=first_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["total_pages"] == 1
    assert len(data["audit_logs"]) == 1

    audit_log = data["audit_logs"][0]

    assert audit_log["action"] == "quiz_created"
    assert audit_log["quiz_title"] == "First User Quiz"
    assert audit_log["creator_name"] == "First User"

    titles = {
        item["quiz_title"]
        for item in data["audit_logs"]
    }

    assert "Second User Quiz" not in titles


def test_audit_logs_are_paginated(client):
    headers = register_and_login(
        client,
        email="audit-pagination@example.com",
        display_name="Pagination User",
    )

    for index in range(21):
        response = client.post(
            "/api/v1/quizzes",
            headers=headers,
            json={
                "title": f"Audit Quiz {index + 1:02d}",
                "visibility": "public",
            },
        )
        assert response.status_code == 201

    page_one_response = client.get(
        "/api/v1/audit-logs",
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
    assert len(page_one["audit_logs"]) == 10

    page_two_response = client.get(
        "/api/v1/audit-logs",
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
    assert len(page_two["audit_logs"]) == 10

    page_three_response = client.get(
        "/api/v1/audit-logs",
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
    assert len(page_three["audit_logs"]) == 1

    page_one_ids = {
        log["id"]
        for log in page_one["audit_logs"]
    }
    page_two_ids = {
        log["id"]
        for log in page_two["audit_logs"]
    }
    page_three_ids = {
        log["id"]
        for log in page_three["audit_logs"]
    }

    assert page_one_ids.isdisjoint(page_two_ids)
    assert page_one_ids.isdisjoint(page_three_ids)
    assert page_two_ids.isdisjoint(page_three_ids)


def test_audit_logs_can_be_filtered_by_action(client):
    headers = register_and_login(
        client,
        email="audit-action-filter@example.com",
        display_name="Action Filter User",
    )

    create_response = client.post(
        "/api/v1/quizzes",
        headers=headers,
        json={
            "title": "Audit Filter Quiz",
            "visibility": "public",
        },
    )
    assert create_response.status_code == 201
    quiz = create_response.json()

    update_response = client.patch(
        f"/api/v1/quizzes/{quiz['id']}",
        headers=headers,
        json={
            "title": "Updated Audit Filter Quiz",
        },
    )
    assert update_response.status_code == 200

    response = client.get(
        "/api/v1/audit-logs",
        headers=headers,
        params={
            "action": "quiz_updated",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["page"] == 1
    assert data["total_pages"] == 1
    assert len(data["audit_logs"]) == 1

    audit_log = data["audit_logs"][0]

    assert audit_log["action"] == "quiz_updated"
    assert audit_log["quiz_title"] == "Updated Audit Filter Quiz"
    assert audit_log["creator_name"] == "Action Filter User"


def test_audit_logs_reject_invalid_action_filter(client):
    headers = register_and_login(
        client,
        email="audit-invalid-action@example.com",
    )

    response = client.get(
        "/api/v1/audit-logs",
        headers=headers,
        params={
            "action": "something_fake",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid audit action"


def test_audit_logs_can_be_searched_by_quiz_title(client):
    headers = register_and_login(
        client,
        email="audit-search-title@example.com",
        display_name="Search User",
    )

    first_response = client.post(
        "/api/v1/quizzes",
        headers=headers,
        json={
            "title": "Python Fundamentals",
            "visibility": "public",
        },
    )
    assert first_response.status_code == 201

    second_response = client.post(
        "/api/v1/quizzes",
        headers=headers,
        json={
            "title": "World History",
            "visibility": "public",
        },
    )
    assert second_response.status_code == 201

    response = client.get(
        "/api/v1/audit-logs",
        headers=headers,
        params={
            "search": "python",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["audit_logs"]) == 1
    assert data["audit_logs"][0]["quiz_title"] == "Python Fundamentals"


def test_audit_log_search_is_case_insensitive(client):
    headers = register_and_login(
        client,
        email="audit-search-case@example.com",
        display_name="Nurlan Creator",
    )

    response = client.post(
        "/api/v1/quizzes",
        headers=headers,
        json={
            "title": "Machine Learning Basics",
            "visibility": "public",
        },
    )
    assert response.status_code == 201

    search_response = client.get(
        "/api/v1/audit-logs",
        headers=headers,
        params={
            "search": "nUrLaN",
        },
    )

    assert search_response.status_code == 200

    data = search_response.json()

    assert data["total"] == 1
    assert len(data["audit_logs"]) == 1
    assert data["audit_logs"][0]["creator_name"] == "Nurlan Creator"
    assert data["audit_logs"][0]["quiz_title"] == "Machine Learning Basics"


def test_audit_logs_can_be_filtered_by_date_range(client):
    headers = register_and_login(
        client,
        email="audit-date-filter@example.com",
        display_name="Date Filter User",
    )

    create_response = client.post(
        "/api/v1/quizzes",
        headers=headers,
        json={
            "title": "Date Filter Quiz",
            "visibility": "public",
        },
    )
    assert create_response.status_code == 201

    response = client.get(
        "/api/v1/audit-logs",
        headers=headers,
        params={
            "date_from": "2020-01-01",
            "date_to": "2100-12-31",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["audit_logs"]) == 1
    assert data["audit_logs"][0]["quiz_title"] == "Date Filter Quiz"


def test_audit_logs_date_range_can_exclude_activity(client):
    headers = register_and_login(
        client,
        email="audit-date-exclude@example.com",
        display_name="Date Exclude User",
    )

    create_response = client.post(
        "/api/v1/quizzes",
        headers=headers,
        json={
            "title": "Excluded Date Quiz",
            "visibility": "public",
        },
    )
    assert create_response.status_code == 201

    response = client.get(
        "/api/v1/audit-logs",
        headers=headers,
        params={
            "date_from": "2000-01-01",
            "date_to": "2000-01-02",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 0
    assert data["total_pages"] == 0
    assert data["audit_logs"] == []


def test_audit_logs_reject_invalid_date_range(client):
    headers = register_and_login(
        client,
        email="audit-invalid-date@example.com",
    )

    response = client.get(
        "/api/v1/audit-logs",
        headers=headers,
        params={
            "date_from": "2026-08-25",
            "date_to": "2026-08-20",
        },
    )

    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "date_from cannot be after date_to"
    )


def test_audit_logs_can_be_searched_by_quiz_title_and_creator(client):
    headers = register_and_login(
        client,
        email="audit-search@example.com",
        display_name="Search Test Creator",
    )

    first_response = client.post(
        "/api/v1/quizzes",
        headers=headers,
        json={
            "title": "Python Fundamentals",
            "visibility": "public",
        },
    )
    assert first_response.status_code == 201

    second_response = client.post(
        "/api/v1/quizzes",
        headers=headers,
        json={
            "title": "JavaScript Basics",
            "visibility": "public",
        },
    )
    assert second_response.status_code == 201

    title_response = client.get(
        "/api/v1/audit-logs",
        headers=headers,
        params={
            "search": "python",
        },
    )

    assert title_response.status_code == 200

    title_data = title_response.json()

    assert title_data["total"] == 1
    assert len(title_data["audit_logs"]) == 1
    assert (
        title_data["audit_logs"][0]["quiz_title"]
        == "Python Fundamentals"
    )

    creator_response = client.get(
        "/api/v1/audit-logs",
        headers=headers,
        params={
            "search": "search test",
        },
    )

    assert creator_response.status_code == 200

    creator_data = creator_response.json()

    assert creator_data["total"] == 2
    assert len(creator_data["audit_logs"]) == 2

    assert all(
        log["creator_name"] == "Search Test Creator"
        for log in creator_data["audit_logs"]
    )


def test_audit_logs_can_be_filtered_by_date(client):
    headers = register_and_login(
        client,
        email="audit-date-filter@example.com",
        display_name="Date Filter User",
    )

    create_response = client.post(
        "/api/v1/quizzes",
        headers=headers,
        json={
            "title": "Date Filter Quiz",
            "visibility": "public",
        },
    )

    assert create_response.status_code == 201

    today = datetime.now(timezone.utc).date().isoformat()

    response = client.get(
        "/api/v1/audit-logs",
        headers=headers,
        params={
            "date_from": today,
            "date_to": today,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["audit_logs"]) == 1
    assert data["audit_logs"][0]["quiz_title"] == "Date Filter Quiz"


def test_audit_logs_reject_invalid_date_range(client):
    headers = register_and_login(
        client,
        email="audit-invalid-date@example.com",
        display_name="Invalid Date User",
    )

    response = client.get(
        "/api/v1/audit-logs",
        headers=headers,
        params={
            "date_from": "2026-08-23",
            "date_to": "2026-08-22",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "date_from cannot be after date_to"
    )


def test_audit_logs_are_isolated_between_users(client):
    first_headers = register_and_login(
        client,
        email="audit-user-a@example.com",
        display_name="Audit User A",
    )

    second_headers = register_and_login(
        client,
        email="audit-user-b@example.com",
        display_name="Audit User B",
    )

    first_quiz_response = client.post(
        "/api/v1/quizzes",
        headers=first_headers,
        json={
            "title": "User A Private Activity",
            "visibility": "public",
        },
    )

    assert first_quiz_response.status_code == 201

    second_quiz_response = client.post(
        "/api/v1/quizzes",
        headers=second_headers,
        json={
            "title": "User B Private Activity",
            "visibility": "public",
        },
    )

    assert second_quiz_response.status_code == 201

    first_logs_response = client.get(
        "/api/v1/audit-logs",
        headers=first_headers,
    )

    assert first_logs_response.status_code == 200

    first_data = first_logs_response.json()

    assert first_data["total"] == 1
    assert len(first_data["audit_logs"]) == 1

    assert (
        first_data["audit_logs"][0]["quiz_title"]
        == "User A Private Activity"
    )

    assert all(
        log["quiz_title"] != "User B Private Activity"
        for log in first_data["audit_logs"]
    )

    second_logs_response = client.get(
        "/api/v1/audit-logs",
        headers=second_headers,
    )

    assert second_logs_response.status_code == 200

    second_data = second_logs_response.json()

    assert second_data["total"] == 1
    assert len(second_data["audit_logs"]) == 1

    assert (
        second_data["audit_logs"][0]["quiz_title"]
        == "User B Private Activity"
    )

    assert all(
        log["quiz_title"] != "User A Private Activity"
        for log in second_data["audit_logs"]
    )


def test_audit_log_filters_can_be_combined(client):
    headers = register_and_login(
        client,
        email="audit-combined@example.com",
        display_name="Combined Filter User",
    )

    python_response = client.post(
        "/api/v1/quizzes",
        headers=headers,
        json={
            "title": "Python Advanced",
            "visibility": "public",
        },
    )
    assert python_response.status_code == 201

    javascript_response = client.post(
        "/api/v1/quizzes",
        headers=headers,
        json={
            "title": "JavaScript Advanced",
            "visibility": "public",
        },
    )
    assert javascript_response.status_code == 201

    python_quiz = python_response.json()

    update_response = client.patch(
        f"/api/v1/quizzes/{python_quiz['id']}",
        headers=headers,
        json={
            "description": "Updated Python description",
        },
    )
    assert update_response.status_code == 200

    response = client.get(
        "/api/v1/audit-logs",
        headers=headers,
        params={
            "search": "python",
            "action": "quiz_updated",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["audit_logs"]) == 1

    log = data["audit_logs"][0]

    assert log["quiz_title"] == "Python Advanced"
    assert log["action"] == "quiz_updated"