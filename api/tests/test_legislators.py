from api.tests.test_utils import client, assert_status_code, system_headers
import random


def get_test_legislator_payload():
    return {
        "name": "John Doe",
        "image_url": "example.com/image.png",
        "district": f"DC-{random.randint(100,999)}",
        "address": "100 Senate Office Building Washington, DC 20510",
        "instagram": "@senjohndoe",
        "phone": "(202) 111-1111",
    }


# Helper function to create a test legislator
def create_test_legislator():
    response = client.post(
        "/legislators", json=get_test_legislator_payload(), headers=system_headers
    )
    return response.json()


def test_add_legislator_success():
    response = client.post(
        "/legislators", json=get_test_legislator_payload(), headers=system_headers
    )
    assert_status_code(response, 201)
    created_legislator = response.json()
    assert "id" in created_legislator


def test_list_legislators():
    create_test_legislator()
    response = client.get("/legislators", headers=system_headers)
    assert_status_code(response, 200)
    legislators = response.json()
    assert len(legislators) > 0


def test_add_legislator_already_exists():
    legislator_data = create_test_legislator()
    response = client.post("/legislators", json=legislator_data, headers=system_headers)
    assert_status_code(response, 409)
    assert "legislator already exists" in response.json()["detail"]


def test_add_legislator_unauthorized():
    response = client.post(
        "/legislators",
        json=get_test_legislator_payload(),
        headers={"Authorization": "Bearer user_token"},
    )
    assert_status_code(response, 403)


def test_update_legislator_success():
    legislator = create_test_legislator()
    updated_data = {**legislator, "name": "Updated Test legislator"}
    response = client.put("/legislators", json=updated_data, headers=system_headers)
    assert_status_code(response, 200)
    updated_legislator = response.json()
    assert updated_legislator["name"] == "Updated Test legislator"


def test_update_legislator_not_found():
    non_existent_legislator = {
        "id": 9999,
        "name": "Anti-John Doe",
        "image_url": "example.com/image.png",
        "district": "ED-1",
        "address": "999 Senate Office Building Washington, DC 20510",
        "instagram": "@senantijohndoe",
        "phone": "(202) 111-1112",
    }
    response = client.put(
        "/legislators", json=non_existent_legislator, headers=system_headers
    )
    assert_status_code(response, 404)
    assert "legislator not found" in response.json()["detail"]


def test_update_legislator_unauthorized():
    legislator = create_test_legislator()
    updated_data = {**legislator, "title": "Updated Test legislator"}
    response = client.put(
        "/legislators",
        json=updated_data,
        headers={"Authorization": "Bearer user_token"},
    )
    assert_status_code(response, 403)


def test_get_legislator_success():
    legislator = create_test_legislator()
    response = client.get(f"/legislators/{legislator['id']}", headers=system_headers)
    assert_status_code(response, 200)
    retrieved_legislator = response.json()
    assert retrieved_legislator["id"] == legislator["id"]
    assert retrieved_legislator["name"] == legislator["name"]


def test_get_legislator_not_found():
    response = client.get("/legislators/9999", headers=system_headers)
    assert_status_code(response, 404)
    assert "legislator not found" in response.json()["detail"]


def test_delete_legislator_success():
    legislator = create_test_legislator()
    response = client.delete(f"/legislators/{legislator['id']}", headers=system_headers)
    assert_status_code(response, 204)


def test_delete_legislator_not_found():
    response = client.delete("/legislators/9999", headers=system_headers)
    assert_status_code(response, 404)
    assert "legislator not found" in response.json()["detail"]


def test_delete_legislator_unauthorized():
    legislator = create_test_legislator()
    response = client.delete(
        f"/legislators/{legislator['id']}",
        headers={"Authorization": "Bearer user_token"},
    )
    assert_status_code(response, 403)
