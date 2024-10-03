from api.tests.test_utils import client, assert_status_code


def test_signup_success():
    user_data = {
        "email": "newuser@example.com",
        "name": "Test User",
        "password": "strongpassword",
    }
    response = client.post("/signup", json=user_data)
    assert_status_code(response, 201)

    created_user = response.json()
    assert created_user["email"] == user_data["email"]
    assert "id" in created_user


def test_signup_existing_email():
    user_data = {
        "email": "existinguser@example.com",
        "name": "Test User",
        "password": "password123",
    }

    # Create a user first
    client.post("/signup", json=user_data)

    # Try to create another user with the same email
    response = client.post("/signup", json=user_data)
    assert_status_code(response, 400)
    assert "Email already registered" in response.json()["detail"]


def test_signup_invalid_email():
    user_data = {
        "email": "invalidemailstring",
        "name": "Test User",
        "password": "password123",
    }

    response = client.post("/signup", json=user_data)
    assert_status_code(response, 422)
    assert "@" in str(response.json()["detail"])


def test_signup_invalid_password():
    user_data = {
        "email": "invalidpassworduser@example.com",
        "name": "Test User",
        "password": "short",
    }

    response = client.post("/signup", json=user_data)
    assert_status_code(response, 422)
    assert "8 characters" in str(response.json()["detail"])


def test_login_success():
    # First, create a user
    user_data = {
        "email": "loginuser@example.com",
        "name": "Test User",
        "password": "correctpassword",
    }
    client.post("/signup", json=user_data)

    # Now try to login
    login_data = {"username": user_data["email"], "password": user_data["password"]}
    response = client.post("/token", data=login_data)
    assert_status_code(response, 501)  # Not Implemented

    # When implemented, this should be:
    # assert_status_code(response, 200)
    # token_data = response.json()
    # assert "access_token" in token_data
    # assert token_data["token_type"] == "bearer"


def test_login_incorrect_password():
    # First, create a user
    user_data = {
        "email": "wrongpass@example.com",
        "name": "Test User",
        "password": "correctpassword",
    }
    client.post("/signup", json=user_data)

    # Now try to login with wrong password
    login_data = {"username": user_data["email"], "password": "wrongpassword"}
    response = client.post("/token", data=login_data)
    assert_status_code(response, 401)
    assert "Incorrect username or password" in response.json()["detail"]


def test_login_nonexistent_user():
    login_data = {
        "username": "nonexistent@example.com",
        "name": "Test User",
        "password": "anypassword",
    }
    response = client.post("/token", data=login_data)
    assert_status_code(response, 401)
    assert "Incorrect username or password" in response.json()["detail"]


def test_login_missing_fields():
    response = client.post("/token", data={})
    assert_status_code(response, 422)  # Unprocessable Entity
