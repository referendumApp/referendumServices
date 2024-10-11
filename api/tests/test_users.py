from api.tests.test_utils import *  # Import everything to initialize all fixtures


def test_create_user(test_user_session):
    user, _ = test_user_session
    assert "id" in user


def test_create_user_duplicate_email(test_user_session):
    user, _ = test_user_session
    user_data = {
        "email": user["email"],
        "password": "password",
        "name": "Duplicate User",
    }

    response = client.post("/users", json=user_data, headers=system_headers)
    assert_status_code(response, 409)
    assert "Email already registered" in response.json()["detail"]


def test_get_user(test_user_session):
    user, user_headers = test_user_session

    response = client.get(f"/users/{user['id']}", headers=system_headers)
    assert_status_code(response, 200)
    assert response.json()["email"] == user["email"]

    response = client.get(f"/users/{user['id']}", headers=user_headers)
    assert_status_code(response, 200)
    assert response.json()["email"] == user["email"]


def test_update_user(test_user_session):
    user, user_headers = test_user_session

    update_data = {
        "email": user["email"],
        "password": "newpassword",
        "name": "Updated User",
    }
    response = client.put("/users", json=update_data, headers=user_headers)
    assert_status_code(response, 200)
    updated_user = response.json()
    assert updated_user["name"] == update_data["name"]


def test_update_user_unauthorized(test_user_session):
    _, user_headers = test_user_session

    user_data = {
        "email": "unauthorizedupdate@example.com",
        "password": "password",
        "name": "Unauthorized Update User",
    }
    create_response = client.post("/users", json=user_data, headers=system_headers)
    assert_status_code(create_response, 201)
    created_user = create_response.json()

    update_data = {
        "email": user_data["email"],
        "password": "newpassword",
        "name": "Updated User",
    }
    response = client.put("/users", json=update_data, headers=user_headers)
    assert_status_code(response, 403)

    response = client.delete(f"/users/{created_user['id']}", headers=system_headers)
    assert_status_code(response, 204)


def test_delete_user():
    user_data = {
        "email": "deleteuser@example.com",
        "password": "password",
        "name": "Delete User",
    }
    create_response = client.post("/users", json=user_data, headers=system_headers)
    assert_status_code(create_response, 201)
    created_user = create_response.json()

    response = client.delete(f"/users/{created_user['id']}", headers=system_headers)
    assert_status_code(response, 204)

    response = client.get(f"/users/{created_user['id']}", headers=system_headers)
    assert_status_code(response, 404)


def test_delete_user_unauthorized(test_user_session):
    _, user_headers = test_user_session

    user_data = {
        "email": "unauthorizeddelete@example.com",
        "password": "password",
        "name": "Unauthorized Delete User",
    }
    create_response = client.post("/users", json=user_data, headers=system_headers)
    assert_status_code(create_response, 201)
    created_user = create_response.json()

    response = client.delete(f"/users/{created_user['id']}", headers=user_headers)
    assert_status_code(response, 403)

    response = client.delete(f"/users/{created_user['id']}", headers=system_headers)
    assert_status_code(response, 204)


def test_get_non_existent_user():
    response = client.get("/users/99999", headers=system_headers)
    assert_status_code(response, 404)


def test_user_login(test_user_session):
    user, _ = test_user_session

    login_data = {"username": user["email"], "password": "testpassword"}
    response = client.post("/auth/token", data=login_data)
    assert_status_code(response, 200)
    assert "access_token" in response.json()


def test_user_login_invalid_credentials():
    login_data = {"username": "nonexistent@example.com", "password": "wrongpassword"}
    response = client.post("/auth/token", data=login_data)
    assert_status_code(response, 401)


def test_get_user_topics(test_user_session):
    user, user_headers = test_user_session

    response = client.get(f"/users/{user['id']}/topics", headers=user_headers)
    assert_status_code(response, 200)
    assert isinstance(response.json(), list)


def test_follow_topic(test_user_session, test_topic):
    user, user_headers = test_user_session
    topic = test_topic

    response = client.post(f"/follow/topic/{topic['id']}", headers=user_headers)
    assert_status_code(response, 204)

    # Verify that the topic is in the user's topics
    topics_response = client.get(f"/users/{user['id']}/topics", headers=user_headers)
    assert_status_code(topics_response, 200)
    user_topics = topics_response.json()
    assert any(t["id"] == topic["id"] for t in user_topics)

    # Now, unfollow the topic
    unfollow_response = client.delete(
        f"/follow/topic/{topic['id']}", headers=user_headers
    )
    assert_status_code(unfollow_response, 204)

    # Verify that the topic is no longer in the user's topics
    topics_response = client.get(f"/users/{user['id']}/topics", headers=user_headers)
    assert_status_code(topics_response, 200)
    user_topics = topics_response.json()
    assert not any(t["id"] == topic["id"] for t in user_topics)


def test_follow_nonexistent_topic(test_user_session):
    user, user_headers = test_user_session

    response = client.post("/follow/topic/99999", headers=user_headers)
    assert_status_code(response, 404)


def test_unfollow_nonexistent_topic(test_user_session):
    user, user_headers = test_user_session

    response = client.delete("/follow/topic/99999", headers=user_headers)
    assert_status_code(response, 404)


def test_get_user_bills(test_user_session):
    user, user_headers = test_user_session

    response = client.get(f"/users/{user['id']}/bills", headers=user_headers)
    assert_status_code(response, 200)
    assert isinstance(response.json(), list)


def test_follow_bill(test_user_session, test_bill):
    user, user_headers = test_user_session

    response = client.post(f"/follow/bill/{test_bill['id']}", headers=user_headers)
    assert_status_code(response, 204)

    # Verify that the bill is in the user's bills
    response = client.get(f"/users/{user['id']}/bills", headers=user_headers)
    assert_status_code(response, 200)
    user_topics = response.json()
    assert any(t["id"] == test_bill["id"] for t in user_topics)

    # Now, unfollow the bill
    unfollow_response = client.delete(
        f"/follow/bill/{test_bill['id']}", headers=user_headers
    )
    assert_status_code(unfollow_response, 204)

    # Verify that the topic is no longer in the user's topics
    response = client.get(f"/users/{user['id']}/bills", headers=user_headers)
    assert_status_code(response, 200)
    user_topics = response.json()
    assert not any(t["id"] == test_bill["id"] for t in user_topics)


def test_follow_nonexistent_bill(test_user_session):
    user, user_headers = test_user_session

    response = client.post("/follow/bill/99999", headers=user_headers)
    assert_status_code(response, 404)


def test_unfollow_nonexistent_bill(test_user_session):
    user, user_headers = test_user_session

    response = client.delete("/follow/bill/99999", headers=user_headers)
    assert_status_code(response, 404)


def test_add_remove_comment(test_user_session, test_bill):
    user, user_headers = test_user_session

    # Create a parent comment
    parent_comment_data = {
        "user_id": user["id"],
        "bill_id": test_bill["id"],
        "parent_id": None,  # Null for top-level comments
        "comment": "This is a parent comment.",
    }
    response = client.post("/comments", json=parent_comment_data, headers=user_headers)
    assert_status_code(response, 201)
    parent_comment = response.json()
    assert parent_comment["comment"] == parent_comment_data["comment"]
    assert parent_comment["parent_id"] is None

    # Create a child comment
    child_comment_data = {
        "user_id": user["id"],
        "bill_id": test_bill["id"],
        "parent_id": parent_comment["id"],
        "comment": "This is a child comment.",
    }
    response = client.post("/comments", json=child_comment_data, headers=user_headers)
    assert_status_code(response, 201)
    child_comment = response.json()
    assert child_comment["comment"] == child_comment_data["comment"]
    assert child_comment["parent_id"] == parent_comment["id"]

    # Verify both comments were added
    response = client.get(f"/comments/{parent_comment['id']}", headers=user_headers)
    assert_status_code(response, 200)
    retrieved_parent = response.json()
    assert retrieved_parent["id"] == parent_comment["id"]
    assert retrieved_parent["comment"] == parent_comment_data["comment"]

    response = client.get(f"/comments/{child_comment['id']}", headers=user_headers)
    assert_status_code(response, 200)
    retrieved_child = response.json()
    assert retrieved_child["id"] == child_comment["id"]
    assert retrieved_child["parent_id"] == parent_comment["id"]
    assert retrieved_child["comment"] == child_comment_data["comment"]

    # Attempt to remove the parent comment
    response = client.delete(f"/comments/{parent_comment['id']}", headers=user_headers)
    assert_status_code(response, 422)

    # Remove the child comment
    response = client.delete(f"/comments/{child_comment['id']}", headers=user_headers)
    assert_status_code(response, 204)

    # Remove the parent comment
    response = client.delete(f"/comments/{parent_comment['id']}", headers=user_headers)
    assert_status_code(response, 204)

    # Verify both comments were removed
    response = client.get(f"/comments/{child_comment['id']}", headers=user_headers)
    assert_status_code(response, 404)

    response = client.get(f"/comments/{parent_comment['id']}", headers=user_headers)
    assert_status_code(response, 404)
