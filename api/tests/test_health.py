from api.tests.test_utils import assert_status_code


async def test_health(client):
    response = await client.get("/health")
    assert_status_code(response, 200)
