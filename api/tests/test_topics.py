from api.tests.test_utils import assert_status_code


async def test_add_topic_success(test_topic):
    assert "id" in test_topic


async def test_add_topic_already_exists(client, system_headers, test_topic):
    topic_data = {**test_topic}
    topic_data.pop("id")
    response = await client.post("/topics", json=topic_data, headers=system_headers)
    assert_status_code(response, 409)
    assert "topic already exists" in response.json()["detail"]


async def test_add_topic_unauthorized(client, test_topic):
    topic_data = {**test_topic}
    topic_data.pop("id")
    response = await client.post(
        "/topics",
        json=topic_data,
        headers={"Authorization": "Bearer user_token"},
    )
    assert_status_code(response, 403)


async def test_update_topic_success(client, system_headers, test_topic):
    updated_data = {**test_topic, "name": "Updated topic Name"}
    response = await client.put("/topics", json=updated_data, headers=system_headers)
    assert_status_code(response, 200)
    updated_topic = response.json()
    assert updated_topic["name"] == "Updated topic Name"


async def test_update_topic_not_found(client, system_headers):
    non_existent_topic = {
        "id": 9999,
        "name": "DNE",
    }
    response = await client.put("/topics", json=non_existent_topic, headers=system_headers)
    assert_status_code(response, 404)
    assert "topic not found" in response.json()["detail"]


async def test_update_topic_unauthorized(client, test_topic):
    updated_data = {**test_topic, "name": "Updated topic Name"}
    response = await client.put(
        "/topics", json=updated_data, headers={"Authorization": "Bearer user_token"}
    )
    assert_status_code(response, 403)


async def test_get_topic_success(client, system_headers, test_topic):
    response = await client.get(f"/topics/{test_topic['id']}", headers=system_headers)
    assert_status_code(response, 200)
    retrieved_topic = response.json()
    assert retrieved_topic["id"] == test_topic["id"]
    assert retrieved_topic["name"] == test_topic["name"]


async def test_get_topic_not_found(client, system_headers):
    response = await client.get("/topics/9999", headers=system_headers)
    assert_status_code(response, 404)
    assert "topic not found" in response.json()["detail"]


async def test_delete_topic_success(client, system_headers, test_topic):
    response = await client.delete(f"/topics/{test_topic['id']}", headers=system_headers)
    assert_status_code(response, 204)


async def test_delete_topic_not_found(client, system_headers):
    response = await client.delete("/topics/9999", headers=system_headers)
    assert_status_code(response, 404)
    assert "topic not found" in response.json()["detail"]


async def test_delete_bill_unauthorized(client, test_topic):
    response = await client.delete(
        f"/topics/{test_topic['id']}", headers={"Authorization": "Bearer user_token"}
    )
    assert_status_code(response, 403)
