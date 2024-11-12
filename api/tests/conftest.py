import os
import random
from typing import AsyncGenerator, Dict, Tuple

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from api.config import settings
from api.main import app
from api.security import create_access_token
from api.tests.test_utils import assert_status_code, generate_random_string, NO_VOTE_ID
from common.object_storage.client import ObjectStorageClient

ENV = os.environ.get("ENVIRONMENT")
DEBUGGER = os.environ.get("ENABLE_DEBUGGER")
BILL_TEXT_BUCKET_NAME = os.environ.get("BILL_TEXT_BUCKET_NAME")
if ENV == "local" and DEBUGGER is not None and DEBUGGER.lower() == "true":
    import debugpy

    debugpy.listen(("0.0.0.0", 6000))
    debugpy.wait_for_client()


transport = ASGITransport(app=app)
base_url = "http://localhost"


@pytest.fixture(scope="session")
def system_headers() -> dict:
    return {"X-API_Key": settings.API_ACCESS_TOKEN}


@pytest_asyncio.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(base_url=base_url, follow_redirects=True, transport=transport) as client:
        yield client


@pytest_asyncio.fixture(scope="session")
async def create_test_entity(client: AsyncClient, system_headers: Dict[str, str]):
    async def create_entity(endpoint: str, payload: Dict):
        if "id" not in payload:
            payload["id"] = 999999

        response = await client.post(endpoint, json=payload, headers=system_headers)
        assert_status_code(response, 201)
        return response.json()

    return create_entity


@pytest_asyncio.fixture(scope="session")
async def delete_test_entity(client: AsyncClient, system_headers: Dict):
    async def delete_entity(resource: str, entity_id: str):
        response = await client.delete(f"/{resource}/{entity_id}", headers=system_headers)
        if response.status_code != 404:
            assert_status_code(response, 204)

    return delete_entity


@pytest_asyncio.fixture(scope="function")
async def test_vote_choice(create_test_entity, delete_test_entity):
    vote_choice_data = {"name": "Yea"}
    vote_choice = await create_test_entity("/vote_choices/", vote_choice_data)
    yield vote_choice
    await delete_test_entity("vote_choices", vote_choice["id"])


@pytest_asyncio.fixture(scope="function")
async def test_vote_choices(create_test_entity, delete_test_entity):
    # We create the original and an alternative
    vote_choice_data = {"name": "Yea"}
    vote_choice = await create_test_entity("/vote_choices/", vote_choice_data)
    alt_choice_data = {"id": NO_VOTE_ID, "name": "Nay"}
    alt_choice = await create_test_entity("/vote_choices/", alt_choice_data)
    yield vote_choice, alt_choice
    await delete_test_entity("vote_choices", alt_choice["id"])
    await delete_test_entity("vote_choices", vote_choice["id"])


@pytest_asyncio.fixture(scope="function")
async def test_state(create_test_entity, delete_test_entity):
    state_data = {"name": "Washington"}
    state = await create_test_entity("/states/", state_data)
    yield state
    await delete_test_entity("states", state["id"])


@pytest_asyncio.fixture(scope="function")
async def test_party(create_test_entity, delete_test_entity):
    party_data = {"name": "Independent"}
    party = await create_test_entity("/partys/", party_data)
    yield party
    await delete_test_entity("partys", party["id"])


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
    await delete_test_entity("users/admin", user["id"])


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
async def test_legislative_body(create_test_entity, delete_test_entity, test_state, test_role):
    legislative_body_data = {"stateId": test_state["id"], "roleId": test_role["id"]}
    legislative_body = await create_test_entity("/legislative_bodys/", legislative_body_data)
    yield legislative_body
    await delete_test_entity("legislative_bodys", legislative_body["id"])


@pytest_asyncio.fixture(scope="function")
async def test_committee(create_test_entity, delete_test_entity, test_legislative_body):
    committee_data = {
        "name": f"Test Committee {generate_random_string()}",
        "legislativeBodyId": test_legislative_body["id"],
    }
    committee = await create_test_entity("/committees/", committee_data)
    yield committee
    await delete_test_entity("committees", committee["id"])


@pytest_asyncio.fixture(scope="function")
async def test_bill(create_test_entity, delete_test_entity, test_state, test_legislative_body):
    bill_data = {
        "legiscanId": random.randint(100000, 999999),
        "identifier": f"H.B.{random.randint(1, 999)}",
        "title": f"Test Bill {generate_random_string()}",
        "description": "This is a test bill",
        "stateId": test_state["id"],
        "legislativeBodyId": test_legislative_body["id"],
        "sessionId": 118,
        "briefing": "yadayadayada",
        "statusId": 1,
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
    create_test_entity, delete_test_entity, test_bill: Dict, test_legislative_body: Dict
):
    bill_action_data = {
        "id": random.randint(100000, 999999),
        "billId": test_bill["id"],
        "legislativeBodyId": test_legislative_body["id"],
        "date": "2024-01-01",
        "description": "Test",
    }
    bill_action = await create_test_entity("/bill_actions/", bill_action_data)
    yield bill_action
    await delete_test_entity("bill_actions", bill_action["id"])


@pytest_asyncio.fixture(scope="function")
async def test_bill_version(
    create_test_entity,
    delete_test_entity,
    test_bill: Dict,
):
    bill_text = "A BILL"

    hash_value = generate_random_string()
    storage_client = ObjectStorageClient()

    try:
        # Upload bill text to MinIO
        storage_client.upload_file(
            bucket=BILL_TEXT_BUCKET_NAME,
            key=f"{hash_value}.txt",
            file_obj=bill_text.encode("utf-8"),
            content_type="text/plain",
        )

        # Create bill version record
        bill_version_data = {
            "id": random.randint(100000, 999999),
            "billId": test_bill["id"],
            "url": "http://bill_text.com/1.pdf",
            "hash": hash_value,
        }

        bill_version = await create_test_entity("/bill_versions/", bill_version_data)
        yield bill_version

    finally:
        # Cleanup: First delete the database record
        await delete_test_entity("bill_versions", bill_version["id"])

        # Then delete the file from MinIO
        try:
            storage_client.delete_file(bucket=BILL_TEXT_BUCKET_NAME, key=f"{hash_value}.txt")
        except Exception as e:
            logger.warning(f"Failed to delete test bill text from MinIO: {str(e)}")


@pytest_asyncio.fixture(scope="function")
async def test_legislator(
    create_test_entity, delete_test_entity, test_party, test_state, test_role
):
    legislator_data = {
        "legiscanId": f"{random.randint(100,999)}",
        "name": f"John Doe {generate_random_string()}",
        "image_url": "example.com/image.png",
        "district": f"DC-{random.randint(100,999)}",
        "address": "100 Senate Office Building Washington, DC 20510",
        "instagram": f"@sen{generate_random_string()}",
        "phone": f"(202) {random.randint(100,999)}-{random.randint(1000,9999)}",
        "partyId": test_party["id"],
        "stateId": test_state["id"],
        "roleId": test_role["id"],
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
async def test_user_vote(
    client: AsyncClient,
    system_headers,
    test_user_session: Dict,
    test_bill_action: Dict,
    test_vote_choices: Tuple,
):
    _, headers = test_user_session
    yay_vote, nay_vote = test_vote_choices

    vote_data = {
        "billId": test_bill_action["billId"],
        "voteChoiceId": yay_vote["id"],
    }
    response = await client.put("/users/votes/", json=vote_data, headers=headers)
    assert_status_code(response, 200)
    user_vote = response.json()
    yield user_vote
    response = await client.delete(
        f"/users/votes?bill_id={user_vote['billId']}",
        headers=headers,
    )
    assert_status_code(response, 204)


@pytest_asyncio.fixture(scope="function")
async def test_legislator_vote(
    client: AsyncClient,
    system_headers,
    test_user_session: Dict,
    test_bill_action: Dict,
    test_vote_choices: Tuple,
):
    _, headers = test_user_session
    yay_vote, nay_vote = test_vote_choices

    vote_data = {
        "billId": test_bill_action["billId"],
        "billActionId": test_bill_action["id"],
        "voteChoiceId": yay_vote["id"],
    }
    response = await client.put("/legislator_votes/votes/", json=vote_data, headers=headers)
    assert_status_code(response, 200)
    user_vote = response.json()
    yield user_vote
    response = await client.delete(
        f"/users/votes?bill_id={user_vote['billId']}",
        headers=headers,
    )
    assert_status_code(response, 204)
