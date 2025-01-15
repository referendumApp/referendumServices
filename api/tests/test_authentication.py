from api.tests.test_utils import assert_status_code


async def test_signup_success(client):
    user_data = {
        "email": "newuser@example.com",
        "name": "Test User",
        "password": "strongpassword",
    }
    response = await client.post("/auth/signup", json=user_data)
    assert_status_code(response, 201)

    created_user = response.json()
    assert created_user["email"] == user_data["email"]
    assert "id" in created_user


async def test_signup_existing_email(client):
    user_data = {
        "email": "existinguser@example.com",
        "name": "Test User",
        "password": "password123",
    }

    # Create a user first
    await client.post("/auth/signup", json=user_data)

    # Try to create another user with the same email
    response = await client.post("/auth/signup", json=user_data)
    assert_status_code(response, 409)
    assert {"field": "email", "message": "Email already registered"} == response.json()["detail"]


async def test_signup_invalid_email(client):
    user_data = {
        "email": "invalidemailstring",
        "name": "Test User",
        "password": "password123",
    }

    response = await client.post("/auth/signup", json=user_data)
    assert_status_code(response, 422)
    assert "@" in str(response.json()["detail"])


async def test_signup_invalid_password(client):
    user_data = {
        "email": "invalidpassworduser@example.com",
        "name": "Test User",
        "password": "short",
    }

    response = await client.post("/auth/signup", json=user_data)
    assert_status_code(response, 422)
    assert "8 characters" in str(response.json()["detail"])


async def test_login_success(client):
    # First, create a user
    user_data = {
        "email": "loginuser@example.com",
        "name": "Test User",
        "password": "correctpassword",
    }
    await client.post("/auth/signup", json=user_data)

    # Now try to login
    login_data = {"username": user_data["email"], "password": user_data["password"]}
    response = await client.post("/auth/login", data=login_data)
    assert_status_code(response, 200)
    token_data = response.json()
    assert "id" in token_data
    assert "accessToken" in token_data
    assert token_data["tokenType"] == "bearer"


async def test_login_incorrect_password(client):
    # First, create a user
    user_data = {
        "email": "wrongpass@example.com",
        "name": "Test User",
        "password": "correctpassword",
    }
    await client.post("/auth/signup", json=user_data)

    # Now try to login with wrong password
    login_data = {"username": user_data["email"], "password": "wrongpassword"}
    response = await client.post("/auth/login", data=login_data)
    assert_status_code(response, 401)
    assert {
        "field": "username",
        "message": "Username or password not found",
    } == response.json()["detail"]


async def test_login_nonexistent_user(client):
    login_data = {
        "username": "nonexistent@example.com",
        "name": "Test User",
        "password": "anypassword",
    }
    response = await client.post("/auth/login", data=login_data)
    assert_status_code(response, 401)
    assert {
        "field": "username",
        "message": "Username or password not found",
    } == response.json()["detail"]


async def test_login_missing_fields(client):
    response = await client.post("/auth/login", data={})
    assert_status_code(response, 422)  # Unprocessable Entity
