import os
import random
from dataclasses import dataclass, field
from typing import AsyncGenerator, Dict, List, Optional, Tuple

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from api.constants import ABSENT_VOTE_ID, NAY_VOTE_ID, YEA_VOTE_ID
from api.main import app
from api.security import create_access_token
from api.settings import settings
from api.tests.test_utils import generate_random_string
from common.aws.s3.client import S3Client

ENV = os.environ.get("ENVIRONMENT")
DEBUGGER = os.environ.get("ENABLE_DEBUGGER")
BILL_TEXT_BUCKET_NAME = os.environ.get("BILL_TEXT_BUCKET_NAME")
if ENV == "local" and DEBUGGER is not None and DEBUGGER.lower() == "true":
    import debugpy

    debugpy.listen(("0.0.0.0", 6000))
    debugpy.wait_for_client()


transport = ASGITransport(app=app)
base_url = "http://localhost"
storage_client = S3Client()


@pytest.fixture(scope="session")
def system_headers() -> dict:
    return {"X-API_Key": settings.API_ACCESS_TOKEN}


@pytest_asyncio.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(base_url=base_url, follow_redirects=True, transport=transport) as client:
        yield client


@dataclass
class TestManager:
    __test__ = False

    client: AsyncClient
    headers: Dict[str, str]
    resources_to_cleanup: List[tuple] = field(default_factory=list)

    async def cleanup(self):
        """Clean up resources in reverse order of creation."""
        for resource_type, resource_id in reversed(self.resources_to_cleanup):
            if resource_type == "users":
                response = await self.client.delete(
                    f"users/admin/{resource_id}", headers=self.headers
                )
            else:
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

    async def create_state(
        self,
        id: Optional[int] = None,
        name: Optional[str] = None,
        abbr: Optional[str] = None,
    ) -> Dict:
        """Create a state with optional custom name."""
        return await self.create_resource(
            "/states/",
            {
                "id": id,
                "name": name or f"State_{generate_random_string()}",
                "abbr": abbr or f"Abbr_{generate_random_string()}",
            },
        )

    async def create_committee(
        self, name: Optional[str] = None, legislative_body_id: Optional[int] = None
    ) -> Dict:
        """Create a state with optional custom name."""
        if legislative_body_id is None:
            legislative_body = await self.create_legislative_body()
        else:
            legislative_body = await self.get_legislative_body(legislative_body_id)

        return await self.create_resource(
            "/committees/",
            {
                "name": name or f"Committee_{generate_random_string()}",
                "legislativeBodyId": legislative_body["id"],
            },
        )

    async def create_role(self, id: Optional[int] = None, name: Optional[str] = None) -> Dict:
        """Create a role with optional custom name."""
        return await self.create_resource("/roles/", {"id": id, "name": name or "Representative"})

    async def create_party(self, id: Optional[int] = None, name: Optional[str] = None) -> Dict:
        """Create a party with optional custom name."""
        return await self.create_resource("/partys/", {"id": id, "name": name or "Independent"})

    async def create_president(
        self,
        president_id: Optional[int] = None,
        name: Optional[str] = None,
        party_id: Optional[int] = None,
        party_name: Optional[int] = None,
    ) -> Dict:
        """Create a bill with all dependencies."""
        party = await self.create_party(id=party_id, name=party_name)
        party_id = party["id"]

        if not president_id:
            president_id = random.randint(0, 999999)

        return await self.create_resource(
            "/presidents/",
            {
                "id": president_id,
                "name": name or f"President_{generate_random_string()}",
                "partyId": party_id,
            },
        )

    async def create_executive_order(
        self,
        president_id: Optional[int] = None,
        hash_value: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Dict:
        """Create an executive_order with all dependencies."""
        if not president_id:
            president = await self.create_president()
            president_id = president["id"]

        if not hash_value:
            hash_value = generate_random_string()

        return await self.create_resource(
            "/executive_orders/",
            {
                "id": random.randint(0, 999999),
                "briefing": "yadayadayada",
                "signedDate": "2024-01-01",
                "hash": hash_value,
                "presidentId": president_id,
                "title": title or f"EO_{generate_random_string()}",
                "url": generate_random_string(),
            },
        )

    async def create_session(
        self, *, legislature_id: Optional[int] = None, name: Optional[str] = None
    ) -> Dict:
        """Create a session, creating state if needed."""
        if legislature_id is None:
            legislature = await self.create_state()
            legislature_id = legislature["id"]

        return await self.create_resource(
            "/sessions/",
            {
                "name": name or f"Session_{generate_random_string()}",
                "legislatureId": legislature_id,
            },
        )

    async def create_status(self, id: Optional[int] = None, name: Optional[str] = None) -> Dict:
        """Create a status with optional custom name."""
        return await self.create_resource("/statuses/", {"id": id, "name": name or "Introduced"})

    async def create_topic(self, name: Optional[str] = None) -> Dict:
        """Create a status with optional custom name."""
        return await self.create_resource("/topics/", {"name": name or "Health"})

    async def create_legislative_body(
        self, *, legislature_id: Optional[int] = None, role_id: Optional[int] = None
    ) -> Dict:
        """Create a legislative body, creating dependencies if needed."""
        if legislature_id is None:
            legislature = await self.create_state()
            legislature_id = legislature["id"]

        if role_id is None:
            role = await self.create_role()
            role_id = role["id"]

        return await self.create_resource(
            "/legislative_bodys/", {"legislatureId": legislature_id, "roleId": role_id}
        )

    async def create_legislator(
        self,
        *,
        name: Optional[str] = None,
        state_id: Optional[int] = None,
        state_name: Optional[str] = None,
        legislature_id: Optional[int] = None,
        legislature_name: Optional[str] = None,
        role_id: Optional[int] = None,
        role_name: Optional[str] = None,
        party_id: Optional[int] = None,
        party_name: Optional[str] = None,
    ) -> Dict:
        """Create a legislator with all dependencies."""
        state = await self.create_state(id=state_id, name=state_name)
        state_id = state["id"]

        legislature = await self.create_state(id=legislature_id, name=legislature_name)
        legislature_id = legislature["id"]

        role = await self.create_role(id=role_id, name=role_name)
        role_id = role["id"]

        party = await self.create_party(id=party_id, name=party_name)
        party_id = party["id"]

        return await self.create_resource(
            "/legislators/",
            {
                "legiscanId": str(random.randint(100, 99999)),
                "name": name or f"Legislator_{generate_random_string()}",
                "imageUrl": f"https://example.com/{generate_random_string()}.jpg",
                "district": f"D-{random.randint(1, 99)}",
                "address": "123 Capitol St",
                "partyId": party_id,
                "stateId": state_id,
                "legislatureId": legislature_id,
                "roleId": role_id,
                "followthemoneyEid": str(random.randint(100, 99999)),
            },
        )

    async def create_bill(
        self,
        *,
        identifier: Optional[str] = None,
        title: Optional[str] = None,
        role_id: Optional[int] = None,
        role_name: Optional[str] = None,
        legislature_id: Optional[int] = None,
        status_id: Optional[int] = None,
    ) -> Dict:
        """Create a bill with all dependencies."""
        legislature = await self.create_state(id=legislature_id)
        legislature_id = legislature["id"]

        role = await self.create_role(id=role_id, name=role_name)
        role_id = role["id"]

        session = await self.create_session(legislature_id=legislature_id)
        session_id = session["id"]

        if status_id is None:
            status = await self.create_status()
            status_id = status["id"]

        leg_body = await self.create_legislative_body(
            legislature_id=legislature_id, role_id=role_id
        )
        legislative_body_id = leg_body["id"]

        bill_id = random.randint(0, 999999)

        return await self.create_resource(
            "/bills/",
            {
                "id": bill_id,
                "legiscanId": bill_id,
                "identifier": identifier or f"HB_{random.randint(100, 999)}",
                "title": title or f"Bill_{generate_random_string()}",
                "description": "Test bill description",
                "legislatureId": legislature_id,
                "legislativeBodyId": legislative_body_id,
                "sessionId": session_id,
                "statusId": status_id,
                "statusDate": "2024-01-01",
                "currentVersionId": None,
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

        # Upload bill text
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

    async def get_legislative_body(self, legislative_body_id: int) -> Dict:
        """Get legislative_body by ID."""
        response = await self.client.get(
            f"/legislative_bodys/{legislative_body_id}", headers=self.headers
        )
        assert response.status_code == 200, f"Failed to get legislative_body: {response.text}"
        return response.json()

    async def create_user(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Dict:
        """Create a state with optional custom name."""
        return await self.create_resource(
            "/users/",
            {
                "email": email or f"{generate_random_string()}@example.com",
                "password": password or "testpassword",
                "name": name or "Test User",
            },
        )

    async def start_user_session(self) -> Tuple:
        user = await self.create_user()
        token = create_access_token(data={"sub": user["email"]})
        headers = {"Authorization": f"Bearer {token}"}
        return user, headers


@pytest_asyncio.fixture(scope="function")
async def test_manager(
    client: AsyncClient,
    system_headers: Dict[str, str],
) -> AsyncGenerator[TestManager, None]:
    """Fixture that provides access to test resources with automatic cleanup."""
    resources = TestManager(client, system_headers)
    try:
        yield resources
    finally:
        await resources.cleanup()


@pytest.fixture(scope="session", autouse=True)
async def setup_vote_choices(client, system_headers):
    """Create vote choices once at the start of the test session."""
    choice_data_options = [
        {"id": YEA_VOTE_ID, "name": "Yea"},
        {"id": NAY_VOTE_ID, "name": "Nay"},
        {"id": ABSENT_VOTE_ID, "name": "Absent"},
    ]
    for choice_data in choice_data_options:
        response = await client.post("/vote_choices", json=choice_data, headers=system_headers)
        assert response.status_code == 201
    yield
    for choice_data in choice_data_options:
        response = await client.delete(f"/vote_choices/{choice_data['id']}", headers=system_headers)
        assert response.status_code == 204
