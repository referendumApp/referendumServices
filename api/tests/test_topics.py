from api.tests.test_utils import client, assert_status_code, system_headers
import random
import string


def get_test_topic_payload():
    name = "".join(random.choice(string.ascii_lowercase) for _ in range(5))
    return {"name": name}


# Helper function to create a test topic
def create_test_topic():
    response = client.post(
        "/topics", json=get_test_topic_payload(), headers=system_headers
    )
    return response.json()


def test_add_topic_success():
    response = client.post(
        "/topics", json=get_test_topic_payload(), headers=system_headers
    )
    assert_status_code(response, 200)
    created_topic = response.json()
    assert "id" in created_topic


def test_add_topic_already_exists():
    topic_data = create_test_topic()
    response = client.post("/topics", json=topic_data, headers=system_headers)
    assert_status_code(response, 409)
    assert "Topic already exists" in response.json()["detail"]


def test_add_topic_unauthorized():
    response = client.post(
        "/topics",
        json=get_test_topic_payload(),
        headers={"Authorization": "Bearer user_token"},
    )
    assert_status_code(response, 403)


def test_update_topic_success():
    topic = create_test_topic()
    updated_data = {**topic, "name": "Updated Topic Name"}
    response = client.put("/topics", json=updated_data, headers=system_headers)
    assert_status_code(response, 200)
    updated_topic = response.json()
    assert updated_topic["name"] == "Updated Topic Name"


def test_update_topic_not_found():
    non_existent_topic = {
        "id": 9999,
        "name": "DNE",
    }
    response = client.put("/topics", json=non_existent_topic, headers=system_headers)
    assert_status_code(response, 404)
    assert "Topic not found" in response.json()["detail"]


def test_update_topic_unauthorized():
    topic = create_test_topic()
    updated_data = {**topic, "name": "Updated Topic Name"}
    response = client.put(
        "/topics", json=updated_data, headers={"Authorization": "Bearer user_token"}
    )
    assert_status_code(response, 403)


def test_get_topic_success():
    topic = create_test_topic()
    response = client.get(f"/topics/{topic['id']}", headers=system_headers)
    assert_status_code(response, 200)
    retrieved_topic = response.json()
    assert retrieved_topic["id"] == topic["id"]
    assert retrieved_topic["name"] == topic["name"]


def test_get_topic_not_found():
    response = client.get("/topics/9999", headers=system_headers)
    assert_status_code(response, 404)
    assert "Topic not found" in response.json()["detail"]


def test_delete_topic_success():
    topic = create_test_topic()
    response = client.delete(f"/topics/{topic['id']}", headers=system_headers)
    assert_status_code(response, 200)


def test_delete_topic_not_found():
    response = client.delete("/topics/9999", headers=system_headers)
    assert_status_code(response, 404)
    assert "Topic not found" in response.json()["detail"]


def test_delete_bill_unauthorized():
    topic = create_test_topic()
    response = client.delete(
        f"/topics/{topic['id']}", headers={"Authorization": "Bearer user_token"}
    )
    assert_status_code(response, 403)
