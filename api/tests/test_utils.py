from starlette.testclient import TestClient
import pytest
import random
import string

from api.config import settings
from api.main import app
from api.security import create_access_token

# Shared utility functions

client = TestClient(app)
system_headers = {"X-API_Key": settings.API_ACCESS_TOKEN}


def assert_status_code(response, expected_status_code: int):
    assert (
        response.status_code == expected_status_code
    ), f"Expected status code {expected_status_code}, but got {response.status_code}. Response content: {response.content}"


def generate_random_string(length=5):
    return "".join(random.choice(string.ascii_lowercase) for _ in range(length))


def create_test_entity(endpoint, payload_func):
    response = client.post(endpoint, json=payload_func(), headers=system_headers)
    assert_status_code(response, 201)
    return response.json()


# Fixtures
# NOTE - to add a new fixture as a dependency, be sure to add it explicitly as a dependency


@pytest.fixture(scope="function")
def test_user_session():
    user_data = {
        "email": f"{generate_random_string()}@example.com",
        "password": "testpassword",
        "name": "Test User",
    }
    user = create_test_entity("/users", lambda: user_data)
    token = create_access_token(data={"sub": user["email"]})
    headers = {"Authorization": f"Bearer {token}"}
    yield user, headers
    client.delete(f"/users/{user['id']}", headers=system_headers)


@pytest.fixture(scope="function")
def test_topic():
    topic = create_test_entity("/topics", lambda: {"name": generate_random_string()})
    yield topic
    client.delete(f"/topics/{topic['id']}", headers=system_headers)


@pytest.fixture(scope="function")
def test_state():
    state_data = {"name": "Washington"}
    state = create_test_entity("/states", lambda: state_data)
    yield state
    client.delete(f"/states/{state['id']}", headers=system_headers)


@pytest.fixture(scope="function")
def test_role():
    role_data = {"name": "House"}
    role = create_test_entity("/roles", lambda: role_data)
    yield role
    client.delete(f"/roles/{role['id']}", headers=system_headers)


@pytest.fixture(scope="function")
def test_legislative_body(test_state, test_role):
    legislative_body_data = {"state_id": test_state["id"], "role_id": test_role["id"]}
    legislative_body = create_test_entity(
        "/legislative_bodys", lambda: legislative_body_data
    )
    yield legislative_body
    client.delete(
        f"/legislative_bodys/{legislative_body['id']}", headers=system_headers
    )


@pytest.fixture(scope="function")
def test_bill(test_state, test_legislative_body):
    bill_data = {
        "legiscan_id": random.randint(100000, 999999),
        "identifier": f"H.B.{random.randint(1, 999)}",
        "title": f"Test Bill {generate_random_string()}",
        "description": "This is a test bill",
        "state_id": test_state["id"],
        "legislative_body_id": test_legislative_body["id"],
        "session_id": 118,
        "briefing": "yadayadayada",
        "status_id": 1,
        "status_date": "2024-01-01",
    }
    bill = create_test_entity("/bills", lambda: bill_data)
    yield bill
    client.delete(f"/bills/{bill['id']}", headers=system_headers)


@pytest.fixture(scope="function")
def test_party():
    party_data = {"name": "Independent"}
    party = create_test_entity("/partys", lambda: party_data)
    yield party
    client.delete(f"/partys/{party['id']}", headers=system_headers)


@pytest.fixture(scope="function")
def test_legislator(test_party):
    legislator_data = {
        "name": f"John Doe {generate_random_string()}",
        "image_url": "example.com/image.png",
        "district": f"DC-{random.randint(100,999)}",
        "address": "100 Senate Office Building Washington, DC 20510",
        "instagram": f"@sen{generate_random_string()}",
        "phone": f"(202) {random.randint(100,999)}-{random.randint(1000,9999)}",
        "party_id": test_party["id"],
    }
    legislator = create_test_entity("/legislators", lambda: legislator_data)
    yield legislator
    client.delete(f"/legislators/{legislator['id']}", headers=system_headers)
