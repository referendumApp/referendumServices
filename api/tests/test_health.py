from api.tests.common import client


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
