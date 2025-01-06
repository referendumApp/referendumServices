from api.tests.conftest import TestManager
from api.tests.test_utils import assert_status_code
from api.security import create_access_token
import logging


async def test_create_user(test_manager: TestManager):
    user, _ = await test_manager.start_user_session()
    assert "id" in user


async def test_create_user_duplicate_email(test_manager: TestManager):
    user, _ = await test_manager.start_user_session()
    user_data = {
        "email": user["email"],
        "password": "password",
        "name": "Duplicate User",
    }

    response = await test_manager.client.post(
        "/users/", json=user_data, headers=test_manager.headers
    )
    assert_status_code(response, 409)
    assert "Email already registered" in response.json()["detail"]


async def test_get_user(test_manager: TestManager):
    user, user_headers = await test_manager.start_user_session()

    test_error = None
    try:
        # Admin access
        response = await test_manager.client.get(
            f"/users/admin/{user['id']}", headers=test_manager.headers
        )
        assert_status_code(response, 200)
        assert response.json()["email"] == user["email"]

        # User access
        response = await test_manager.client.get("/users/", headers=user_headers)
        assert_status_code(response, 200)
        assert response.json()["email"] == user["email"]
    except Exception as e:
        test_error = str(e)
        logging.error(f"Test failed with {test_error}")
        raise Exception(test_error)


async def test_update_user(test_manager: TestManager):
    user, user_headers = await test_manager.start_user_session()

    update_data = {
        "email": user["email"],
        "password": "newpassword",
        "name": "Updated User",
        "settings": {"feature_flag": True},
    }
    response = await test_manager.client.put("/users/", json=update_data, headers=user_headers)
    assert_status_code(response, 200)
    updated_user = response.json()
    assert updated_user["name"] == update_data["name"]
    assert updated_user["settings"] == {"feature_flag": True}


async def test_update_user_unauthorized(test_manager: TestManager):
    _, user_headers = await test_manager.start_user_session()

    # Create a new user
    user_data = {
        "email": "unauthorizedupdate@example.com",
        "password": "password",
        "name": "Unauthorized Update User",
    }
    create_response = await test_manager.client.post(
        "/users/", json=user_data, headers=test_manager.headers
    )
    assert_status_code(create_response, 201)
    created_user = create_response.json()

    test_error = None
    try:
        # Attempt unauthorized update
        update_data = {
            "email": user_data["email"],
            "password": "newpassword",
            "name": "Updated User",
        }
        response = await test_manager.client.put("/users/", json=update_data, headers=user_headers)
        assert_status_code(response, 403)
    except Exception as e:
        test_error = str(e)
        logging.error(f"Test failed with {test_error}")

    # Cleanup
    response = await test_manager.client.delete(
        f"/users/admin/{created_user['id']}", headers=test_manager.headers
    )
    assert_status_code(response, 204)

    if test_error:
        raise Exception(test_error)


async def test_admin_delete_user(test_manager: TestManager):
    user_data = {
        "email": "deleteuser@example.com",
        "password": "password",
        "name": "Delete User",
    }
    create_response = await test_manager.client.post(
        "/users/", json=user_data, headers=test_manager.headers
    )
    assert_status_code(create_response, 201)
    created_user = create_response.json()

    test_error = None
    try:
        response = await test_manager.client.delete(
            f"/users/admin/{created_user['id']}", headers=test_manager.headers
        )
        assert_status_code(response, 204)

        response = await test_manager.client.get(
            f"/users/admin/{created_user['id']}", headers=test_manager.headers
        )
        assert_status_code(response, 404)
    except Exception as e:
        test_error = str(e)
        logging.error(f"Test failed with {test_error}")
        # No cleanup needed since we're testing deletion
        raise Exception(test_error)


async def test_delete_user(test_manager: TestManager):
    user_data = {
        "email": "deleteuser@example.com",
        "password": "password",
        "name": "Delete User",
    }
    create_response = await test_manager.client.post(
        "/users/", json=user_data, headers=test_manager.headers
    )
    assert_status_code(create_response, 201)
    created_user = create_response.json()

    token = create_access_token(data={"sub": created_user["email"]})
    user_headers = {"Authorization": f"Bearer {token}"}

    test_error = None
    try:
        response = await test_manager.client.delete("/users/", headers=user_headers)
        assert_status_code(response, 204)

        response = await test_manager.client.get(
            f"/users/admin/{created_user['id']}", headers=test_manager.headers
        )
        assert_status_code(response, 404)
    except Exception as e:
        test_error = str(e)
        logging.error(f"Test failed with {test_error}")
        # Cleanup if test failed
        await test_manager.client.delete(
            f"/users/admin/{created_user['id']}", headers=test_manager.headers
        )
        raise Exception(test_error)


async def test_get_non_existent_user(test_manager: TestManager):
    response = await test_manager.client.get("/users/admin/99999", headers=test_manager.headers)
    assert_status_code(response, 404)


async def test_user_login(test_manager: TestManager):
    user, _ = await test_manager.start_user_session()

    login_data = {"username": user["email"], "password": "testpassword"}
    response = await test_manager.client.post("/auth/login", data=login_data)
    assert_status_code(response, 200)
    assert "accessToken" in response.json()


async def test_user_login_invalid_credentials(test_manager: TestManager):
    login_data = {"username": "nonexistent@example.com", "password": "wrongpassword"}
    response = await test_manager.client.post("/auth/login", data=login_data)
    assert_status_code(response, 401)


async def test_get_user_topics(test_manager: TestManager):
    _, user_headers = await test_manager.start_user_session()

    response = await test_manager.client.get("/users/topics", headers=user_headers)
    assert_status_code(response, 200)
    assert isinstance(response.json(), list)


async def test_follow_topic(test_manager: TestManager):
    _, user_headers = await test_manager.start_user_session()
    topic = await test_manager.create_topic()

    test_error = None
    try:
        # Follow topic
        response = await test_manager.client.post(
            f"/users/topics/{topic['id']}", headers=user_headers
        )
        assert_status_code(response, 204)

        # Verify follow
        topics_response = await test_manager.client.get("/users/topics", headers=user_headers)
        assert_status_code(topics_response, 200)
        user_topics = topics_response.json()
        assert any(t["id"] == topic["id"] for t in user_topics)

        # Unfollow topic
        unfollow_response = await test_manager.client.delete(
            f"/users/topics/{topic['id']}", headers=user_headers
        )
        assert_status_code(unfollow_response, 204)

        # Verify unfollow
        topics_response = await test_manager.client.get("/users/topics", headers=user_headers)
        assert_status_code(topics_response, 200)
        user_topics = topics_response.json()
        assert not any(t["id"] == topic["id"] for t in user_topics)
    except Exception as e:
        test_error = str(e)
        logging.error(f"Test failed with {test_error}, marking and cleaning up")

        # Cleanup any remaining follow
        await test_manager.client.delete(f"/users/topics/{topic['id']}", headers=user_headers)

        raise Exception(test_error)


async def test_follow_nonexistent_topic(test_manager: TestManager):
    _, user_headers = await test_manager.start_user_session()

    response = await test_manager.client.post("/users/topics/99999", headers=user_headers)
    assert_status_code(response, 404)


async def test_unfollow_nonexistent_topic(test_manager: TestManager):
    _, user_headers = await test_manager.start_user_session()

    response = await test_manager.client.delete("/users/topics/99999", headers=user_headers)
    assert_status_code(response, 404)


async def test_get_user_bills(test_manager: TestManager):
    _, user_headers = await test_manager.start_user_session()

    response = await test_manager.client.get("/users/bills", headers=user_headers)
    assert_status_code(response, 200)
    assert isinstance(response.json(), list)


async def test_follow_bill(test_manager: TestManager):
    _, user_headers = await test_manager.start_user_session()
    test_bill = await test_manager.create_bill()

    test_error = None
    try:
        # Follow bill
        response = await test_manager.client.post(
            f"/users/bills/{test_bill['id']}", headers=user_headers
        )
        assert_status_code(response, 204)

        # Verify follow
        response = await test_manager.client.get("/users/bills", headers=user_headers)
        assert_status_code(response, 200)
        user_bills = response.json()
        assert any(b["id"] == test_bill["id"] for b in user_bills)

        # Unfollow bill
        unfollow_response = await test_manager.client.delete(
            f"/users/bills/{test_bill['id']}", headers=user_headers
        )
        assert_status_code(unfollow_response, 204)

        # Verify unfollow
        response = await test_manager.client.get("/users/bills", headers=user_headers)
        assert_status_code(response, 200)
        user_bills = response.json()
        assert not any(b["id"] == test_bill["id"] for b in user_bills)
    except Exception as e:
        test_error = str(e)
        logging.error(f"Test failed with {test_error}, marking and cleaning up")

        # Cleanup any remaining follow
        await test_manager.client.delete(f"/users/bills/{test_bill['id']}", headers=user_headers)

        raise Exception(test_error)


async def test_follow_nonexistent_bill(test_manager: TestManager):
    _, user_headers = await test_manager.start_user_session()

    response = await test_manager.client.post("/users/bills/99999", headers=user_headers)
    assert_status_code(response, 404)


async def test_unfollow_nonexistent_bill(test_manager: TestManager):
    _, user_headers = await test_manager.start_user_session()

    response = await test_manager.client.delete("/users/bills/99999", headers=user_headers)
    assert_status_code(response, 404)


async def test_follow_legislator(test_manager: TestManager):
    _, user_headers = await test_manager.start_user_session()
    test_legislator = await test_manager.create_legislator()

    test_error = None
    try:
        # Follow legislator
        response = await test_manager.client.post(
            f"/users/legislators/{test_legislator['id']}", headers=user_headers
        )
        assert_status_code(response, 204)

        # Verify follow
        response = await test_manager.client.get("/users/legislators", headers=user_headers)
        assert_status_code(response, 200)
        user_legislators = response.json()
        assert any(l["id"] == test_legislator["id"] for l in user_legislators)

        # Unfollow legislator
        unfollow_response = await test_manager.client.delete(
            f"/users/legislators/{test_legislator['id']}", headers=user_headers
        )
        assert_status_code(unfollow_response, 204)

        # Verify unfollow
        response = await test_manager.client.get("/users/legislators", headers=user_headers)
        assert_status_code(response, 200)
        user_legislators = response.json()
        assert not any(l["id"] == test_legislator["id"] for l in user_legislators)
    except Exception as e:
        test_error = str(e)
        logging.error(f"Test failed with {test_error}, marking and cleaning up")

        # Cleanup any remaining follow
        await test_manager.client.delete(
            f"/users/legislators/{test_legislator['id']}", headers=user_headers
        )

        raise Exception(test_error)
