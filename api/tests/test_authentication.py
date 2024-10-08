import pytest
import random
import string
from api.tests.test_utils import client, assert_status_code, system_headers
from api.security import create_access_token


# Shared utility functions


def generate_random_string(length=5):
    return "".join(random.choice(string.ascii_lowercase) for _ in range(length))


def create_test_entity(endpoint, payload_func):
    response = client.post(endpoint, json=payload_func(), headers=system_headers)
    assert_status_code(response, 201)
    return response.json()


# Fixtures


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
def test_bill():
    bill_data = {
        "legiscan_id": random.randint(100000, 999999),
        "identifier": f"H.B.{random.randint(1, 999)}",
        "title": f"Test Bill {generate_random_string()}",
        "description": "This is a test bill",
        "state": "CA",
        "body": "House",
        "session": "118",
        "briefing": "yadayadayada",
        "status": "introduced",
        "latest_action": "none",
    }
    bill = create_test_entity("/bills", lambda: bill_data)
    yield bill
    client.delete(f"/bills/{bill['id']}", headers=system_headers)


@pytest.fixture(scope="function")
def test_legislator():
    legislator_data = {
        "name": f"John Doe {generate_random_string()}",
        "image_url": "example.com/image.png",
        "district": f"DC-{random.randint(100,999)}",
        "address": "100 Senate Office Building Washington, DC 20510",
        "instagram": f"@sen{generate_random_string()}",
        "phone": f"(202) {random.randint(100,999)}-{random.randint(1000,9999)}",
    }
    legislator = create_test_entity("/legislators", lambda: legislator_data)
    yield legislator
    client.delete(f"/legislators/{legislator['id']}", headers=system_headers)
