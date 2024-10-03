import pytest

from api.security import create_access_token

from .common import client, system_headers


@pytest.fixture(scope="function")
def test_user_session():
    user_data = {"email": "testuser@example.com", "password": "testpassword", "name": "Test User"}

    response = client.post("/users", json=user_data, headers=system_headers)
    assert response.status_code == 200
    user = response.json()
    token = create_access_token(data={"sub": user["email"]})
    headers = {"Authorization": f"Bearer {token}"}

    yield user, headers

    response = client.delete(f"/users/{user['id']}", headers=system_headers)
    assert response.status_code == 200


def test_create_user(test_user_session):
    user, _ = test_user_session
    assert user["email"] == "testuser@example.com"
    assert user["name"] == "Test User"
    assert "id" in user


def test_create_user_duplicate_email(test_user_session):
    user, _ = test_user_session
    user_data = {"email": user["email"], "password": "password", "name": "Duplicate User"}

    # Try to create the user again
    response = client.post("/users", json=user_data, headers=system_headers)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_get_user(test_user_session):
    user, user_headers = test_user_session

    # Get the user with system token
    response = client.get(f"/users/{user['id']}", headers=system_headers)
    assert response.status_code == 200
    assert response.json()["email"] == user["email"]

    # Get the user with user token
    response = client.get(f"/users/{user['id']}", headers=user_headers)
    assert response.status_code == 200
    assert response.json()["email"] == user["email"]


def test_update_user(test_user_session):
    user, user_headers = test_user_session

    # Update the user
    update_data = {"email": user["email"], "password": "newpassword", "name": "Updated User"}
    response = client.put("/users", json=update_data, headers=user_headers)
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["name"] == update_data["name"]


def test_update_user_unauthorized(test_user_session):
    _, user_headers = test_user_session

    # Create another user with system token
    user_data = {"email": "unauthorizedupdate@example.com", "password": "password", "name": "Unauthorized Update User"}
    create_response = client.post("/users", json=user_data, headers=system_headers)
    created_user = create_response.json()

    # Try to update the new user with the test user's token
    update_data = {"email": user_data["email"], "password": "newpassword", "name": "Updated User"}
    response = client.put("/users", json=update_data, headers=user_headers)
    assert response.status_code == 403

    # Clean up
    response = client.delete(f"/users/{created_user['id']}", headers=system_headers)
    assert response.status_code == 200


def test_delete_user():
    # Create a user
    user_data = {"email": "deleteuser@example.com", "password": "password", "name": "Delete User"}
    create_response = client.post("/users", json=user_data, headers=system_headers)
    created_user = create_response.json()

    # Delete the user
    response = client.delete(f"/users/{created_user['id']}", headers=system_headers)
    assert response.status_code == 200

    # Try to get the deleted user
    response = client.get(f"/users/{created_user['id']}", headers=system_headers)
    assert response.status_code == 404


def test_delete_user_unauthorized(test_user_session):
    _, user_headers = test_user_session

    # Create another user with system token
    user_data = {"email": "unauthorizeddelete@example.com", "password": "password", "name": "Unauthorized Delete User"}
    create_response = client.post("/users", json=user_data, headers=system_headers)
    created_user = create_response.json()

    # Try to delete the new user with the test user's token
    response = client.delete(f"/users/{created_user['id']}", headers=user_headers)
    assert response.status_code == 403

    # Clean up
    response = client.delete(f"/users/{created_user['id']}", headers=system_headers)
    assert response.status_code == 200


def test_get_non_existent_user():
    response = client.get("/users/99999", headers=system_headers)
    assert response.status_code == 404


def test_user_login(test_user_session):
    user, _ = test_user_session

    # Login
    login_data = {"username": user["email"], "password": "testpassword"}
    response = client.post("/token", data=login_data)
    assert response.status_code == 501
    # assert "access_token" in response.json()


def test_user_login_invalid_credentials():
    login_data = {"username": "nonexistent@example.com", "password": "wrongpassword"}
    response = client.post("/token", data=login_data)
    assert response.status_code == 401
