from api.tests.conftest import TestManager
from api.tests.test_utils import assert_status_code


async def test_add_topic_success(test_manager: TestManager):
    test_topic = await test_manager.create_topic()
    assert "id" in test_topic


async def test_add_topic_already_exists(test_manager: TestManager):
    test_topic = await test_manager.create_topic()
    topic_data = {**test_topic, "id": 9000}
    response = await test_manager.client.post(
        "/topics/", json=topic_data, headers=test_manager.headers
    )
    assert_status_code(response, 409)
    assert "topic already exists" in response.json()["detail"]


async def test_add_topic_unauthorized(test_manager: TestManager):
    test_topic = await test_manager.create_topic()
    topic_data = {**test_topic}
    topic_data.pop("id")
    response = await test_manager.client.post(
        "/topics/",
        json=topic_data,
        headers={"Authorization": "Bearer user_token"},
    )
    assert_status_code(response, 403)


async def test_update_topic_success(test_manager: TestManager):
    test_topic = await test_manager.create_topic()
    updated_data = {**test_topic, "name": "Updated topic Name"}
    response = await test_manager.client.put(
        "/topics/", json=updated_data, headers=test_manager.headers
    )
    assert_status_code(response, 200)
    updated_topic = response.json()
    assert updated_topic["name"] == "Updated topic Name"


async def test_update_topic_not_found(test_manager: TestManager):
    non_existent_topic = {
        "id": 9999,
        "name": "DNE",
    }
    response = await test_manager.client.put(
        "/topics/", json=non_existent_topic, headers=test_manager.headers
    )
    assert_status_code(response, 404)
    assert "topic not found" in response.json()["detail"]


async def test_update_topic_unauthorized(test_manager: TestManager):
    test_topic = await test_manager.create_topic()
    updated_data = {**test_topic, "name": "Updated topic Name"}
    response = await test_manager.client.put(
        "/topics/", json=updated_data, headers={"Authorization": "Bearer user_token"}
    )
    assert_status_code(response, 403)


async def test_get_topic_success(test_manager: TestManager):
    test_topic = await test_manager.create_topic()
    response = await test_manager.client.get(
        f"/topics/{test_topic['id']}", headers=test_manager.headers
    )
    assert_status_code(response, 200)
    retrieved_topic = response.json()
    assert retrieved_topic["id"] == test_topic["id"]
    assert retrieved_topic["name"] == test_topic["name"]


async def test_get_topic_not_found(test_manager: TestManager):
    response = await test_manager.client.get("/topics/9999", headers=test_manager.headers)
    assert_status_code(response, 404)
    assert "topic not found" in response.json()["detail"]


async def test_delete_topic_success(test_manager: TestManager):
    test_topic = await test_manager.create_topic()
    response = await test_manager.client.delete(
        f"/topics/{test_topic['id']}", headers=test_manager.headers
    )
    assert_status_code(response, 204)


async def test_delete_topic_not_found(test_manager: TestManager):
    response = await test_manager.client.delete("/topics/9999", headers=test_manager.headers)
    assert_status_code(response, 404)
    assert "topic not found" in response.json()["detail"]


async def test_delete_topic_unauthorized(test_manager: TestManager):
    test_topic = await test_manager.create_topic()
    response = await test_manager.client.delete(
        f"/topics/{test_topic['id']}", headers={"Authorization": "Bearer user_token"}
    )
    assert_status_code(response, 403)
