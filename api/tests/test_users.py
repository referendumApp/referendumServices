import pytest

from api.security import create_access_token
from api.tests.test_utils import client, system_headers, assert_status_code


@pytest.fixture(scope="function")
def test_user_session():
    user_data = {
        "email": "testuser@example.com",
        "password": "testpassword",
        "name": "Test User",
    }

    response = client.post("/users", json=user_data, headers=system_headers)
    assert_status_code(response, 200)
    user = response.json()
    token = create_access_token(data={"sub": user["email"]})
    headers = {"Authorization": f"Bearer {token}"}

    yield user, headers

    response = client.delete(f"/users/{user['id']}", headers=system_headers)
    assert_status_code(response, 200)


def test_create_user(test_user_session):
    user, _ = test_user_session
    assert user["email"] == "testuser@example.com"
    assert user["name"] == "Test User"
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
    assert_status_code(create_response, 200)
    created_user = create_response.json()

    update_data = {
        "email": user_data["email"],
        "password": "newpassword",
        "name": "Updated User",
    }
    response = client.put("/users", json=update_data, headers=user_headers)
    assert_status_code(response, 403)

    response = client.delete(f"/users/{created_user['id']}", headers=system_headers)
    assert_status_code(response, 200)


def test_delete_user():
    user_data = {
        "email": "deleteuser@example.com",
        "password": "password",
        "name": "Delete User",
    }
    create_response = client.post("/users", json=user_data, headers=system_headers)
    assert_status_code(create_response, 200)
    created_user = create_response.json()

    response = client.delete(f"/users/{created_user['id']}", headers=system_headers)
    assert_status_code(response, 200)

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
    assert_status_code(create_response, 200)
    created_user = create_response.json()

    response = client.delete(f"/users/{created_user['id']}", headers=user_headers)
    assert_status_code(response, 403)

    response = client.delete(f"/users/{created_user['id']}", headers=system_headers)
    assert_status_code(response, 200)


def test_get_non_existent_user():
    response = client.get("/users/99999", headers=system_headers)
    assert_status_code(response, 404)


def test_user_login(test_user_session):
    user, _ = test_user_session

    login_data = {"username": user["email"], "password": "testpassword"}
    response = client.post("/token", data=login_data)
    assert_status_code(response, 501)
    # Uncomment the following line when the login endpoint is implemented
    # assert "access_token" in response.json()


def test_user_login_invalid_credentials():
    login_data = {"username": "nonexistent@example.com", "password": "wrongpassword"}
    response = client.post("/token", data=login_data)
    assert_status_code(response, 401)
