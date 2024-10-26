import asyncio
import random
from typing import AsyncGenerator, Dict

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from api.tests.test_utils import assert_status_code, generate_random_string

from api.config import settings
from api.main import app
from api.security import create_access_token
from common.database.referendum.models import VoteChoice


transport = ASGITransport(app=app)
base_url = "http://localhost"


@pytest.fixture(scope="session")
def system_headers() -> dict:
    return {"X-API_Key": settings.API_ACCESS_TOKEN}


@pytest_asyncio.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(base_url=base_url, transport=transport) as client:
        yield client


@pytest_asyncio.fixture(scope="session")
async def create_test_entity(system_headers: Dict[str, str]):
    async def create_entity(endpoint: str, payload: Dict):
        async with AsyncClient(base_url=base_url, transport=transport) as client:
            response = await client.post(endpoint, json=payload, headers=system_headers)
            assert_status_code(response, 201)
            return response.json()

    return create_entity


@pytest_asyncio.fixture(scope="session")
async def delete_test_entity(system_headers: Dict):
    async def delete_entity(resource: str, entity_id: str):
        async with AsyncClient(base_url=base_url, transport=transport) as client:
            response = await client.delete(f"/{resource}/{entity_id}", headers=system_headers)
            if response.status_code != 404:
                assert_status_code(response, 204)

    return delete_entity


@pytest_asyncio.fixture(scope="function")
async def test_user_session(create_test_entity, delete_test_entity):
    user_data = {
        "email": f"{generate_random_string()}@example.com",
        "password": "testpassword",
        "name": "Test User",
    }
    user = await create_test_entity("/users/", user_data)
    token = create_access_token(data={"sub": user["email"]})
    headers = {"Authorization": f"Bearer {token}"}
    yield user, headers
    await delete_test_entity("users", user["id"])


@pytest_asyncio.fixture(scope="function")
async def test_topic(create_test_entity, delete_test_entity):
    topic = await create_test_entity("/topics/", {"name": generate_random_string()})
    yield topic
    await delete_test_entity("topics", topic["id"])


@pytest_asyncio.fixture(scope="function")
async def test_role(create_test_entity, delete_test_entity):
    role_data = {"name": "House"}
    role = await create_test_entity("/roles/", role_data)
    yield role
    await delete_test_entity("roles", role["id"])


@pytest_asyncio.fixture(scope="function")
async def test_legislative_body(create_test_entity, delete_test_entity, session_cache, test_role):
    test_state = session_cache.state
    legislative_body_data = {"state_id": test_state["id"], "role_id": test_role["id"]}
    legislative_body = await create_test_entity("/legislative_bodys/", legislative_body_data)
    yield legislative_body
    await delete_test_entity("legislative_bodys", legislative_body["id"])


@pytest_asyncio.fixture(scope="function")
async def test_committee(create_test_entity, delete_test_entity, test_legislative_body):
    committee_data = {
        "name": f"Test Committee {generate_random_string()}",
        "legislative_body_id": test_legislative_body["id"],
    }
    committee = await create_test_entity("/committees/", committee_data)
    yield committee
    await delete_test_entity("committees", committee["id"])


@pytest_asyncio.fixture(scope="function")
async def test_bill(create_test_entity, delete_test_entity, session_cache, test_legislative_body):
    test_state = session_cache.state
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
    bill = await create_test_entity("/bills/", bill_data)
    yield bill
    await delete_test_entity("bills", bill["id"])


@pytest_asyncio.fixture(scope="function")
async def test_get_bills(client, system_headers, test_bill):
    bills = await client.get("/bills/", headers=system_headers)
    assert_status_code(bills, 200)
    return bills.json()


@pytest_asyncio.fixture(scope="function")
async def test_bill_action(
    create_test_entity,
    delete_test_entity,
    test_bill: Dict,
):
    bill_action_data = {"bill_id": test_bill["id"], "date": "2024-01-01", "type": 1}
    bill_action = await create_test_entity("/bill_actions/", bill_action_data)
    yield bill_action
    await delete_test_entity("bill_actions", bill_action["id"])


@pytest_asyncio.fixture(scope="function")
async def test_legislator(create_test_entity, delete_test_entity, session_cache):
    test_party = session_cache.party
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
    legislator = await create_test_entity("/legislators/", legislator_data)
    yield legislator
    await delete_test_entity("legislators", legislator["id"])


@pytest_asyncio.fixture(scope="function")
async def test_get_legislators(client, system_headers, test_legislator):
    legislators = await client.get("/legislators/", headers=system_headers)
    assert_status_code(legislators, 200)
    return legislators.json()


@pytest_asyncio.fixture(scope="function")
async def test_vote(
    client: AsyncClient,
    test_user_session: Dict,
    test_bill_action: Dict,
):
    user, headers = test_user_session
    vote_data = {
        "bill_id": test_bill_action["bill_id"],
        "bill_action_id": test_bill_action["id"],
        "vote_choice": VoteChoice.YES.value,
    }
    response = await client.put(f"/users/{user['id']}/votes/", json=vote_data, headers=headers)
    assert_status_code(response, 200)
    return response.json()
