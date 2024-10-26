from api.tests.test_utils import assert_status_code


async def test_create_user(test_user_session):
    user, _ = test_user_session
    assert "id" in user


async def test_create_user_duplicate_email(client, system_headers, test_user_session):
    user, _ = test_user_session
    user_data = {
        "email": user["email"],
        "password": "password",
        "name": "Duplicate User",
    }

    response = await client.post("/users/", json=user_data, headers=system_headers)
    assert_status_code(response, 409)
    assert "Email already registered" in response.json()["detail"]


async def test_get_user(client, system_headers, test_user_session):
    user, user_headers = test_user_session

    response = await client.get(f"/users/{user['id']}", headers=system_headers)
    assert_status_code(response, 200)
    assert response.json()["email"] == user["email"]

    response = await client.get(f"/users/{user['id']}", headers=user_headers)
    assert_status_code(response, 200)
    assert response.json()["email"] == user["email"]


async def test_update_user(client, test_user_session):
    user, user_headers = test_user_session

    update_data = {
        "email": user["email"],
        "password": "newpassword",
        "name": "Updated User",
    }
    response = await client.put("/users/", json=update_data, headers=user_headers)
    assert_status_code(response, 200)
    updated_user = response.json()
    assert updated_user["name"] == update_data["name"]


async def test_update_user_unauthorized(client, system_headers, test_user_session):
    _, user_headers = test_user_session

    user_data = {
        "email": "unauthorizedupdate@example.com",
        "password": "password",
        "name": "Unauthorized Update User",
    }
    create_response = await client.post("/users/", json=user_data, headers=system_headers)
    assert_status_code(create_response, 201)
    created_user = create_response.json()

    update_data = {
        "email": user_data["email"],
        "password": "newpassword",
        "name": "Updated User",
    }
    response = await client.put("/users/", json=update_data, headers=user_headers)
    assert_status_code(response, 403)

    response = await client.delete(f"/users/{created_user['id']}", headers=system_headers)
    assert_status_code(response, 204)


async def test_delete_user(client, system_headers):
    user_data = {
        "email": "deleteuser@example.com",
        "password": "password",
        "name": "Delete User",
    }
    create_response = await client.post("/users/", json=user_data, headers=system_headers)
    assert_status_code(create_response, 201)
    created_user = create_response.json()

    response = await client.delete(f"/users/{created_user['id']}", headers=system_headers)
    assert_status_code(response, 204)

    response = await client.get(f"/users/{created_user['id']}", headers=system_headers)
    assert_status_code(response, 404)


async def test_delete_user_unauthorized(client, system_headers, test_user_session):
    _, user_headers = test_user_session

    user_data = {
        "email": "unauthorizeddelete@example.com",
        "password": "password",
        "name": "Unauthorized Delete User",
    }
    create_response = await client.post("/users/", json=user_data, headers=system_headers)
    assert_status_code(create_response, 201)
    created_user = create_response.json()

    response = await client.delete(f"/users/{created_user['id']}", headers=user_headers)
    assert_status_code(response, 403)

    response = await client.delete(f"/users/{created_user['id']}", headers=system_headers)
    assert_status_code(response, 204)


async def test_get_non_existent_user(client, system_headers):
    response = await client.get("/users/99999", headers=system_headers)
    assert_status_code(response, 404)


async def test_user_login(client, test_user_session):
    user, _ = test_user_session

    login_data = {"username": user["email"], "password": "testpassword"}
    response = await client.post("/auth/login", data=login_data)
    assert_status_code(response, 200)
    assert "accessToken" in response.json()


async def test_user_login_invalid_credentials(client):
    login_data = {"username": "nonexistent@example.com", "password": "wrongpassword"}
    response = await client.post("/auth/login", data=login_data)
    assert_status_code(response, 401)


async def test_get_user_topics(client, test_user_session):
    user, user_headers = test_user_session

    response = await client.get(f"/users/{user['id']}/topics", headers=user_headers)
    assert_status_code(response, 200)
    assert isinstance(response.json(), list)


async def test_follow_topic(client, test_user_session, test_topic):
    user, user_headers = test_user_session
    topic = test_topic

    response = await client.post(f"/users/{user['id']}/topics/{topic['id']}", headers=user_headers)
    assert_status_code(response, 204)

    # Verify that the topic is in the user's topics
    topics_response = await client.get(f"/users/{user['id']}/topics", headers=user_headers)
    assert_status_code(topics_response, 200)
    user_topics = topics_response.json()
    assert any(t["id"] == topic["id"] for t in user_topics)

    # Now, unfollow the topic
    unfollow_response = await client.delete(
        f"/users/{user['id']}/topics/{topic['id']}", headers=user_headers
    )
    assert_status_code(unfollow_response, 204)

    # Verify that the topic is no longer in the user's topics
    topics_response = await client.get(f"/users/{user['id']}/topics", headers=user_headers)
    assert_status_code(topics_response, 200)
    user_topics = topics_response.json()
    assert not any(t["id"] == topic["id"] for t in user_topics)


async def test_follow_nonexistent_topic(client, test_user_session):
    user, user_headers = test_user_session

    response = await client.post(f"/users/{user['id']}/topics/99999", headers=user_headers)
    assert_status_code(response, 404)


async def test_unfollow_nonexistent_topic(client, test_user_session):
    user, user_headers = test_user_session

    response = await client.delete(f"/users/{user['id']}/topics/99999", headers=user_headers)
    assert_status_code(response, 404)


async def test_get_user_bills(client, test_user_session):
    user, user_headers = test_user_session

    response = await client.get(f"/users/{user['id']}/bills", headers=user_headers)
    assert_status_code(response, 200)
    assert isinstance(response.json(), list)


async def test_follow_bill(client, test_user_session, test_bill):
    user, user_headers = test_user_session

    response = await client.post(
        f"/users/{user['id']}/bills/{test_bill['id']}", headers=user_headers
    )
    assert_status_code(response, 204)

    # Verify that the bill is in the user's bills
    response = await client.get(f"/users/{user['id']}/bills", headers=user_headers)
    assert_status_code(response, 200)
    user_topics = response.json()
    assert any(t["id"] == test_bill["id"] for t in user_topics)

    # Now, unfollow the bill
    unfollow_response = await client.delete(
        f"/users/{user['id']}/bills/{test_bill['id']}", headers=user_headers
    )
    assert_status_code(unfollow_response, 204)

    # Verify that the topic is no longer in the user's topics
    response = await client.get(f"/users/{user['id']}/bills", headers=user_headers)
    assert_status_code(response, 200)
    user_topics = response.json()
    assert not any(t["id"] == test_bill["id"] for t in user_topics)


async def test_follow_nonexistent_bill(client, test_user_session):
    user, user_headers = test_user_session

    response = await client.post(f"/users/{user['id']}/bills/99999", headers=user_headers)
    assert_status_code(response, 404)


async def test_unfollow_nonexistent_bill(client, test_user_session):
    user, user_headers = test_user_session

    response = await client.delete(f"/users/{user['id']}/bills/99999", headers=user_headers)
    assert_status_code(response, 404)


async def test_follow_legislator(client, test_user_session, test_legislator):
    user, user_headers = test_user_session

    response = await client.post(
        f"/users/{user['id']}/legislators/{test_legislator['id']}", headers=user_headers
    )
    assert_status_code(response, 204)

    # Verify that the legislator is in the user's followed legislators
    response = await client.get(f"/users/{user['id']}/legislators", headers=user_headers)
    assert_status_code(response, 200)
    user_legislators = response.json()
    assert any(l["id"] == test_legislator["id"] for l in user_legislators)

    # Now, unfollow the legislator
    unfollow_response = await client.delete(
        f"/users/{user['id']}/legislators/{test_legislator['id']}", headers=user_headers
    )
    assert_status_code(unfollow_response, 204)

    # Verify that the legislator is no longer in the user's followed legislators
    response = await client.get(f"/users/{user['id']}/legislators", headers=user_headers)
    assert_status_code(response, 200)
    user_legislators = response.json()
    assert not any(l["id"] == test_legislator["id"] for l in user_legislators)
