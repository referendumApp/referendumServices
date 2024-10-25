import random
from typing import Dict, Generator

import pytest
from _pytest.fixtures import SubRequest
from starlette.testclient import TestClient
from api.tests.test_utils import assert_status_code, generate_random_string

from api.config import settings
from api.main import app
from api.security import create_access_token
from common.database.referendum.models import VoteChoice


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def system_headers() -> dict:
    return {"X-API_Key": settings.API_ACCESS_TOKEN}


@pytest.fixture(scope="session")
def create_test_entity(client: TestClient, system_headers: Dict[str, str]):
    def create_entity(endpoint: str, payload: Dict):
        response = client.post(endpoint, json=payload, headers=system_headers)
        assert_status_code(response, 201)
        return response.json()

    return create_entity


@pytest.fixture(scope="session")
def delete_test_entity(client: TestClient, system_headers: Dict):
    def delete_entity(resource: str, entity_id: str):
        response = client.delete(f"/{resource}/{entity_id}", headers=system_headers)
        if response.status_code != 404:
            assert_status_code(response, 204)

    return delete_entity


@pytest.fixture(scope="module")
def test_state(create_test_entity, delete_test_entity, request: SubRequest):
    state_data = {"name": "Washington"}
    state = create_test_entity("/states", state_data)
    # request.addfinalizer(lambda: delete_test_entity("states", state["id"]))
    yield state
    delete_test_entity("states", state["id"])


@pytest.fixture
def test_user_session(create_test_entity, delete_test_entity, request: SubRequest):
    user_data = {
        "email": f"{generate_random_string()}@example.com",
        "password": "testpassword",
        "name": "Test User",
    }
    user = create_test_entity("/users", user_data)
    token = create_access_token(data={"sub": user["email"]})
    headers = {"Authorization": f"Bearer {token}"}
    # request.addfinalizer(lambda: delete_test_entity("users", user["id"]))
    yield user, headers
    delete_test_entity("users", user["id"])


@pytest.fixture
def test_topic(create_test_entity, delete_test_entity, request: SubRequest):
    topic = create_test_entity("/topics", {"name": generate_random_string()})
    # request.addfinalizer(lambda: delete_test_entity("topics", topic["id"]))
    yield topic
    delete_test_entity("topics", topic["id"])


@pytest.fixture
def test_role(create_test_entity, delete_test_entity, request: SubRequest):
    role_data = {"name": "House"}
    role = create_test_entity("/roles", role_data)
    # request.addfinalizer(lambda: delete_test_entity("roles", role["id"]))
    yield role
    delete_test_entity("roles", role["id"])


@pytest.fixture(scope="module")
def test_legislative_body(
    create_test_entity, delete_test_entity, test_state, test_role, request: SubRequest
):
    legislative_body_data = {"state_id": test_state["id"], "role_id": test_role["id"]}
    legislative_body = create_test_entity("/legislative_bodys", legislative_body_data)
    # request.addfinalizer(lambda: delete_test_entity("legislative_bodys", legislative_body["id"]))
    yield legislative_body
    delete_test_entity("legislative_bodys", legislative_body["id"])


@pytest.fixture(scope="module")
def test_committee(
    create_test_entity, delete_test_entity, test_legislative_body, request: SubRequest
):
    committee_data = {
        "name": f"Test Committee {generate_random_string()}",
        "legislative_body_id": test_legislative_body["id"],
    }
    committee = create_test_entity("/committees", committee_data)
    # request.addfinalizer(lambda: delete_test_entity("committees", committee["id"]))
    yield committee
    delete_test_entity("committees", committee["id"])


@pytest.fixture(scope="module")
def test_bill(
    create_test_entity,
    delete_test_entity,
    test_state,
    test_legislative_body,
    request: SubRequest,
):
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
    bill = create_test_entity("/bills", bill_data)
    # request.addfinalizer(lambda: delete_test_entity("bills", bill["id"]))
    yield bill
    delete_test_entity("bills", bill["id"])


@pytest.fixture(scope="module")
def test_get_bills(client, system_headers, test_bill):
    bills = client.get("/bills", headers=system_headers)
    assert_status_code(bills, 200)
    return bills.json()


@pytest.fixture(scope="module")
def test_bill_action(
    create_test_entity,
    delete_test_entity,
    test_bill: Dict,
    request: SubRequest,
):
    bill_action_data = {"bill_id": test_bill["id"], "date": "2024-01-01", "type": 1}
    bill_action = create_test_entity("/bill_actions", bill_action_data)
    # request.addfinalizer(lambda: delete_test_entity("bill_actions", bill_action["id"]))
    yield bill_action
    delete_test_entity("bill_actions", bill_action["id"])


@pytest.fixture
def test_party(create_test_entity, delete_test_entity, request: SubRequest):
    party_data = {"name": "Independent"}
    party = create_test_entity("/partys", party_data)
    # request.addfinalizer(lambda: delete_test_entity("partys", party["id"]))
    yield party
    delete_test_entity("partys", party["id"])


@pytest.fixture
def test_legislator(create_test_entity, delete_test_entity, test_party, request: SubRequest):
    legislator_data = {
        "legiscan_id": f"{random.randint(100,999)}",
        "name": f"John Doe {generate_random_string()}",
        "image_url": "example.com/image.png",
        "district": f"DC-{random.randint(100,999)}",
        "address": "100 Senate Office Building Washington, DC 20510",
        "instagram": f"@sen{generate_random_string()}",
        "phone": f"(202) {random.randint(100,999)}-{random.randint(1000,9999)}",
        "party_id": test_party["id"],
    }
    legislator = create_test_entity("/legislators", legislator_data)
    # request.addfinalizer(lambda: delete_test_entity("legislators", legislator["id"]))
    yield legislator
    delete_test_entity("legislators", legislator["id"])


@pytest.fixture
def test_get_legislators(client, system_headers, test_legislator):
    legislators = client.get("/legislators", headers=system_headers)
    assert_status_code(legislators, 200)
    return legislators.json()


@pytest.fixture
def test_vote(
    client: TestClient,
    test_user_session: Dict,
    test_bill_action: Dict,
):
    user, headers = test_user_session
    vote_data = {
        "bill_id": test_bill_action["bill_id"],
        "bill_action_id": test_bill_action["id"],
        "vote_choice": VoteChoice.YES.value,
    }
    response = client.put(f"/users/{user['id']}/votes/", json=vote_data, headers=headers)
    assert_status_code(response, 200)
    return response.json()
