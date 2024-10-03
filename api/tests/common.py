from starlette.testclient import TestClient

from api import app
from api.config import settings

client = TestClient(app)
headers = {"Authorization": f"Bearer {settings.API_ACCESS_TOKEN}"}
