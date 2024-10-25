from api.tests.test_utils import client, assert_status_code, system_headers, test_topic


def test_add_topic_success(test_topic):
    assert "id" in test_topic


def test_add_topic_already_exists(test_topic):
    topic_data = {**test_topic, "id": 900000}
    response = client.post("/topics", json=topic_data, headers=system_headers)
    assert_status_code(response, 409)
    assert "topic already exists" in response.json()["detail"]


def test_add_topic_unauthorized(test_topic):
    topic_data = {**test_topic}
    topic_data.pop("id")
    response = client.post(
        "/topics",
        json=topic_data,
        headers={"Authorization": "Bearer user_token"},
    )
    assert_status_code(response, 403)


def test_update_topic_success(test_topic):
    updated_data = {**test_topic, "name": "Updated topic Name"}
    response = client.put("/topics", json=updated_data, headers=system_headers)
    assert_status_code(response, 200)
    updated_topic = response.json()
    assert updated_topic["name"] == "Updated topic Name"


def test_update_topic_not_found():
    non_existent_topic = {
        "id": 9999,
        "name": "DNE",
    }
    response = client.put("/topics", json=non_existent_topic, headers=system_headers)
    assert_status_code(response, 404)
    assert "topic not found" in response.json()["detail"]


def test_update_topic_unauthorized(test_topic):
    updated_data = {**test_topic, "name": "Updated topic Name"}
    response = client.put(
        "/topics", json=updated_data, headers={"Authorization": "Bearer user_token"}
    )
    assert_status_code(response, 403)


def test_get_topic_success(test_topic):
    response = client.get(f"/topics/{test_topic['id']}", headers=system_headers)
    assert_status_code(response, 200)
    retrieved_topic = response.json()
    assert retrieved_topic["id"] == test_topic["id"]
    assert retrieved_topic["name"] == test_topic["name"]


def test_get_topic_not_found():
    response = client.get("/topics/9999", headers=system_headers)
    assert_status_code(response, 404)
    assert "topic not found" in response.json()["detail"]


def test_delete_topic_success(test_topic):
    response = client.delete(f"/topics/{test_topic['id']}", headers=system_headers)
    assert_status_code(response, 204)


def test_delete_topic_not_found():
    response = client.delete("/topics/9999", headers=system_headers)
    assert_status_code(response, 404)
    assert "topic not found" in response.json()["detail"]


def test_delete_bill_unauthorized(test_topic):
    response = client.delete(
        f"/topics/{test_topic['id']}", headers={"Authorization": "Bearer user_token"}
    )
    assert_status_code(response, 403)
