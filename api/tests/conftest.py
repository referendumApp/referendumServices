import os
import random
from typing import AsyncGenerator, Dict, Tuple, Optional, List

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from api.config import settings
from api.main import app
from api.security import create_access_token
from api.tests.test_utils import (
    assert_status_code,
    generate_random_string,
    DEFAULT_ID,
    YAY_VOTE_ID,
    NAY_VOTE_ID,
)
from common.object_storage.client import ObjectStorageClient

from dataclasses import dataclass, field
import uuid

ENV = os.environ.get("ENVIRONMENT")
DEBUGGER = os.environ.get("ENABLE_DEBUGGER")
BILL_TEXT_BUCKET_NAME = os.environ.get("BILL_TEXT_BUCKET_NAME")
if ENV == "local" and DEBUGGER is not None and DEBUGGER.lower() == "true":
    import debugpy

    debugpy.listen(("0.0.0.0", 6000))
    debugpy.wait_for_client()


transport = ASGITransport(app=app)
base_url = "http://localhost"
storage_client = ObjectStorageClient()


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
            payload["id"] = DEFAULT_ID

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
    vote_choice_data = {"id": YAY_VOTE_ID, "name": "Yea"}
    vote_choice = await create_test_entity("/vote_choices/", vote_choice_data)
    yield vote_choice
    await delete_test_entity("vote_choices", vote_choice["id"])


@pytest_asyncio.fixture(scope="function")
async def test_vote_choices(create_test_entity, delete_test_entity):
    # We create the original and an alternative
    vote_choice_data = {"id": YAY_VOTE_ID, "name": "Yea"}
    vote_choice = await create_test_entity("/vote_choices/", vote_choice_data)
    alt_choice_data = {"id": NAY_VOTE_ID, "name": "Nay"}
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
async def test_status(create_test_entity, delete_test_entity):
    status_data = {"name": "Introduced"}
    status = await create_test_entity("/statuses/", status_data)
    yield status
    await delete_test_entity("statuses", status["id"])


@pytest_asyncio.fixture(scope="function")
async def test_session(create_test_entity, delete_test_entity, test_state):
    session_data = {"name": "118th", "stateId": test_state["id"]}
    session = await create_test_entity("/sessions/", session_data)
    yield session
    await delete_test_entity("sessions", session["id"])


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
async def test_bill(
    create_test_entity, delete_test_entity, test_session, test_legislative_body, test_status
):
    bill_data = {
        "legiscanId": random.randint(0, DEFAULT_ID),
        "identifier": f"H.B.{random.randint(1, 999)}",
        "title": f"Test Bill {generate_random_string()}",
        "description": "This is a test bill",
        "stateId": test_session["stateId"],
        "legislativeBodyId": test_legislative_body["id"],
        "sessionId": test_session["id"],
        "statusId": test_status["id"],
        "status_date": "2024-01-01",
        "current_version_id": None,
    }
    bill = await create_test_entity("/bills/", bill_data)
    yield bill
    await delete_test_entity("bills", bill["id"])


@pytest_asyncio.fixture(scope="function")
async def test_bill_action(create_test_entity, delete_test_entity, test_bill):
    bill_action_data = {
        "id": random.randint(100000, DEFAULT_ID),
        "billId": test_bill["id"],
        "legislativeBodyId": test_bill["legislativeBodyId"],
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
            "id": random.randint(0, DEFAULT_ID),
            "billId": test_bill["id"],
            "url": "http://bill_text.com/1.pdf",
            "hash": hash_value,
            "briefing": "yadayadayada",
        }

        bill_version = await create_test_entity("/bill_versions/", bill_version_data)
        yield bill_version

    finally:
        # Cleanup: First delete the database record
        await delete_test_entity("bill_versions", bill_version["id"])

        # Then delete the file from MinIO
        storage_client.delete_file(bucket=BILL_TEXT_BUCKET_NAME, key=f"{hash_value}.txt")


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
    test_vote_choices: Tuple,
    test_bill: Dict,
):
    _, headers = test_user_session
    yay_vote, nay_vote = test_vote_choices

    vote_data = {
        "billId": test_bill["id"],
        "voteChoiceId": yay_vote["id"],
    }
    response = await client.put("/users/votes/", json=vote_data, headers=headers)
    assert_status_code(response, 200)
    user_vote = response.json()
    yield user_vote
    response = await client.delete(
        f"/users/votes?billId={user_vote['billId']}",
        headers=headers,
    )
    assert_status_code(response, 204)


@pytest_asyncio.fixture(scope="function")
async def test_legislator_vote(
    client: AsyncClient,
    system_headers,
    test_legislator: Dict,
    test_bill_action: Dict,
    test_vote_choice: Dict,
):
    legislator_vote_data = {
        "billId": test_bill_action["billId"],
        "billActionId": test_bill_action["id"],
        "legislatorId": test_legislator["id"],
        "voteChoiceId": test_vote_choice["id"],
    }
    response = await client.put(
        "/legislator_votes/", json=legislator_vote_data, headers=system_headers
    )
    assert_status_code(response, 200)
    legislator_vote = response.json()
    yield legislator_vote
    params = {"bill_action_id": test_bill_action["id"], "legislator_id": test_legislator["id"]}
    response = await client.delete("/legislator_votes/", params=params, headers=system_headers)
    assert_status_code(response, 204)


# ==========


def generate_random_string(prefix: str = "") -> str:
    """Generate a random string with optional prefix."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}" if prefix else uuid.uuid4().hex[:8]


@dataclass
class TestManager:
    client: AsyncClient
    headers: Dict[str, str]
    resources_to_cleanup: List[tuple] = field(default_factory=list)

    async def cleanup(self):
        """Clean up resources in reverse order of creation."""
        for resource_type, resource_id in reversed(self.resources_to_cleanup):
            response = await self.client.delete(
                f"/{resource_type}/{resource_id}", headers=self.headers
            )
            if response.status_code != 404:  # Ignore if already deleted
                assert response.status_code == 204

        filenames = storage_client.list_filenames(BILL_TEXT_BUCKET_NAME)
        for filename in filenames:
            storage_client.delete_file(BILL_TEXT_BUCKET_NAME, filename)

    async def create_resource(self, endpoint: str, data: Dict, skip_cleanup: bool = False) -> Dict:
        """Create a resource and optionally track it for cleanup."""
        if not data.get("id"):
            data["id"] = random.randint(0, 999999)
        response = await self.client.post(endpoint, json=data, headers=self.headers)
        assert response.status_code == 201, f"Failed to create resource: {response.text}"
        resource = response.json()

        if not skip_cleanup:
            self.resources_to_cleanup.append((endpoint.strip("/"), resource["id"]))
        return resource

    async def create_state(self, name: Optional[str] = None) -> Dict:
        """Create a state with optional custom name."""
        return await self.create_resource(
            "/states/", {"name": name or f"State_{generate_random_string()}"}
        )

    async def create_role(self, name: Optional[str] = None) -> Dict:
        """Create a role with optional custom name."""
        return await self.create_resource("/roles/", {"name": name or "Representative"})

    async def create_party(self, name: Optional[str] = None) -> Dict:
        """Create a party with optional custom name."""
        return await self.create_resource("/partys/", {"name": name or "Independent"})

    async def create_session(
        self, *, state_id: Optional[int] = None, name: Optional[str] = None
    ) -> Dict:
        """Create a session, creating state if needed."""
        if state_id is None:
            state = await self.create_state()
            state_id = state["id"]

        return await self.create_resource(
            "/sessions/",
            {"name": name or f"Session_{generate_random_string()}", "stateId": state_id},
        )

    async def create_status(self, name: Optional[str] = None) -> Dict:
        """Create a status with optional custom name."""
        return await self.create_resource("/statuses/", {"name": name or "Introduced"})

    async def create_topic(self, name: Optional[str] = None) -> Dict:
        """Create a status with optional custom name."""
        return await self.create_resource("/topics/", {"name": name or "Health"})

    async def create_legislative_body(
        self, *, state_id: Optional[int] = None, role_id: Optional[int] = None
    ) -> Dict:
        """Create a legislative body, creating dependencies if needed."""
        if state_id is None:
            state = await self.create_state()
            state_id = state["id"]

        if role_id is None:
            role = await self.create_role()
            role_id = role["id"]

        return await self.create_resource(
            "/legislative_bodys/", {"stateId": state_id, "roleId": role_id}
        )

    async def create_legislator(
        self,
        *,
        name: Optional[str] = None,
        state_id: Optional[int] = None,
        role_id: Optional[int] = None,
        party_id: Optional[int] = None,
    ) -> Dict:
        """Create a legislator with all dependencies."""
        if state_id is None:
            state = await self.create_state()
            state_id = state["id"]

        if role_id is None:
            role = await self.create_role()
            role_id = role["id"]

        if party_id is None:
            party = await self.create_party()
            party_id = party["id"]

        return await self.create_resource(
            "/legislators/",
            {
                "legiscanId": str(random.randint(100, 999)),
                "name": name or f"Legislator_{generate_random_string()}",
                "image_url": f"https://example.com/{generate_random_string()}.jpg",
                "district": f"D-{random.randint(1, 99)}",
                "address": "123 Capitol St",
                "partyId": party_id,
                "stateId": state_id,
                "roleId": role_id,
            },
        )

    async def create_bill(
        self,
        *,
        title: Optional[str] = None,
        state_id: Optional[int] = None,
        legislative_body_id: Optional[int] = None,
        session_id: Optional[int] = None,
        status_id: Optional[int] = None,
    ) -> Dict:
        """Create a bill with all dependencies."""
        if state_id is None:
            state = await self.create_state()
            state_id = state["id"]

        if legislative_body_id is None:
            leg_body = await self.create_legislative_body(state_id=state_id)
            legislative_body_id = leg_body["id"]

        if session_id is None:
            session = await self.create_session(state_id=state_id)
            session_id = session["id"]

        if status_id is None:
            status = await self.create_status()
            status_id = status["id"]

        bill_id = random.randint(0, 999999)

        return await self.create_resource(
            "/bills/",
            {
                "id": bill_id,
                "legiscanId": bill_id,
                "identifier": f"HB_{random.randint(100, 999)}",
                "title": title or f"Bill_{generate_random_string()}",
                "description": "Test bill description",
                "stateId": state_id,
                "legislativeBodyId": legislative_body_id,
                "sessionId": session_id,
                "statusId": status_id,
                "status_date": "2024-01-01",
                "current_version_id": None,
            },
        )

    async def create_bill_version(
        self,
        *,
        bill_id: Optional[int] = None,
        url: Optional[str] = None,
        hash_value: Optional[str] = None,
    ) -> Dict:
        """Create a bill version, creating bill if needed."""
        if bill_id is None:
            bill = await self.create_bill()
            bill_id = bill["id"]

        if not hash_value:
            hash_value = generate_random_string()

        # Upload bill text to MinIO
        bill_text = "A BILL"
        storage_client.upload_file(
            bucket=BILL_TEXT_BUCKET_NAME,
            key=f"{hash_value}.txt",
            file_obj=bill_text.encode("utf-8"),
            content_type="text/plain",
        )

        return await self.create_resource(
            "/bill_versions/",
            {
                "id": random.randint(1000, 9999),
                "billId": bill_id,
                "url": url or f"https://example.com/bills/{generate_random_string()}.pdf",
                "hash": hash_value,
                "briefing": "yadayadayada",
            },
        )

    async def create_bill_action(self, *, bill_id: Optional[int] = None) -> Dict:
        """Create a bill action, creating bill if needed."""
        if bill_id is None:
            bill = await self.create_bill()
            bill_id = bill["id"]
        else:
            bill = await self.get_bill(bill_id)

        return await self.create_resource(
            "/bill_actions/",
            {
                "id": random.randint(1000, 9999),
                "billId": bill_id,
                "legislativeBodyId": bill["legislativeBodyId"],
                "date": "2024-01-01",
                "description": "Test",
            },
        )

    async def get_bill(self, bill_id: int) -> Dict:
        """Get current bill details by ID."""
        response = await self.client.get(f"/bills/{bill_id}", headers=self.headers)
        assert response.status_code == 200, f"Failed to get bill: {response.text}"
        return response.json()


@pytest_asyncio.fixture
async def test_manager(client: AsyncClient, system_headers: Dict[str, str]) -> TestManager:
    """Fixture that provides access to test resources with automatic cleanup."""
    resources = TestManager(client, system_headers)
    try:
        yield resources
    finally:
        await resources.cleanup()
