from starlette.testclient import TestClient

from api.main import app
from api.config import settings

client = TestClient(app)
system_headers = {"Authorization": f"Bearer {settings.API_ACCESS_TOKEN}"}


def assert_status_code(response, expected_status_code: int):
    assert (
        response.status_code == expected_status_code
    ), f"Expected status code {expected_status_code}, but got {response.status_code}. Response content: {response.content}"
