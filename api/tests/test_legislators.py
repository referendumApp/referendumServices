import pytest
import random

from api.tests.test_utils import client, assert_status_code, system_headers


@pytest.fixture(scope="function")
def test_party():
    party_data = {"name": "Independent"}
    response = client.post("/parties", json=party_data, headers=system_headers)
    assert_status_code(response, 201)
    party = response.json()

    yield party

    response = client.delete(f"/parties/{party['id']}", headers=system_headers)
    assert_status_code(response, 204)


def get_test_legislator_payload():
    return {
        "name": "John Doe",
        "image_url": "example.com/image.png",
        "party_id": 1,
        "district": f"DC-{random.randint(100,999)}",
        "address": "100 Senate Office Building Washington, DC 20510",
        "instagram": "@senjohndoe",
        "phone": "(202) 111-1111",
    }


@pytest.fixture(scope="function")
def test_legislator(test_party):
    legislator_data = get_test_legislator_payload()
    legislator_data["party_id"] = test_party["id"]

    response = client.post("/legislators", json=legislator_data, headers=system_headers)
    assert_status_code(response, 201)
    legislator = response.json()

    yield legislator

    response = client.delete(f"/legislators/{legislator['id']}", headers=system_headers)
    assert_status_code(response, 204)


def test_list_legislators(test_legislator):
    response = client.get("/legislators", headers=system_headers)
    assert_status_code(response, 200)
    legislators = response.json()
    assert len(legislators) > 0


def test_add_legislator_already_exists(test_legislator):
    test_legislator.pop("id")
    response = client.post("/legislators", json=test_legislator, headers=system_headers)
    assert_status_code(response, 409)
    assert "legislator already exists" in response.json()["detail"]


def test_add_legislator_unauthorized():
    response = client.post(
        "/legislators",
        json=get_test_legislator_payload(),
        headers={"Authorization": "Bearer user_token"},
    )
    assert_status_code(response, 403)


def test_update_legislator_success(test_legislator):
    updated_data = {**test_legislator, "name": "Updated Test legislator"}
    response = client.put("/legislators", json=updated_data, headers=system_headers)
    assert_status_code(response, 200)
    updated_legislator = response.json()
    assert updated_legislator["name"] == "Updated Test legislator"


def test_update_legislator_not_found():
    non_existent_legislator = {
        "id": 9999,
        "name": "Anti-John Doe",
        "party_id": 1,
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


def test_update_legislator_unauthorized(test_legislator):
    updated_data = {**test_legislator, "title": "Updated Test legislator"}
    response = client.put(
        "/legislators",
        json=updated_data,
        headers={"Authorization": "Bearer user_token"},
    )
    assert_status_code(response, 403)


def test_get_legislator_success(test_legislator):
    response = client.get(
        f"/legislators/{test_legislator['id']}", headers=system_headers
    )
    assert_status_code(response, 200)
    retrieved_legislator = response.json()
    assert retrieved_legislator["id"] == test_legislator["id"]
    assert retrieved_legislator["name"] == test_legislator["name"]


def test_get_legislator_not_found():
    response = client.get("/legislators/9999", headers=system_headers)
    assert_status_code(response, 404)
    assert "legislator not found" in response.json()["detail"]


def test_delete_legislator_not_found():
    response = client.delete("/legislators/9999", headers=system_headers)
    assert_status_code(response, 404)
    assert "legislator not found" in response.json()["detail"]


def test_delete_legislator_unauthorized(test_legislator):
    response = client.delete(
        f"/legislators/{test_legislator['id']}",
        headers={"Authorization": "Bearer user_token"},
    )
    assert_status_code(response, 403)
