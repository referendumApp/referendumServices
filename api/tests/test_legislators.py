from api.tests.test_utils import assert_status_code


def test_add_legislator_success(test_legislator):
    assert "id" in test_legislator


def test_list_legislators(test_get_legislators):
    assert len(test_get_legislators) > 0


def test_add_legislator_already_exists(client, system_headers, test_legislator):
    legislator_data = {**test_legislator}
    legislator_data.pop("id")
    response = client.post("/legislators", json=legislator_data, headers=system_headers)
    assert_status_code(response, 409)
    assert "legislator already exists" in response.json()["detail"]


def test_add_legislator_unauthorized(client, test_legislator):
    legislator_data = {**test_legislator}
    legislator_data.pop("id")
    response = client.post(
        "/legislators",
        json=legislator_data,
        headers={"Authorization": "Bearer user_token"},
    )
    assert_status_code(response, 403)


def test_update_legislator_success(client, system_headers, test_legislator):
    updated_data = {**test_legislator, "name": "Updated Test legislator"}
    response = client.put("/legislators", json=updated_data, headers=system_headers)
    assert_status_code(response, 200)
    updated_legislator = response.json()
    assert updated_legislator["name"] == "Updated Test legislator"


def test_update_legislator_not_found(client, system_headers):
    non_existent_legislator = {
        "id": 9999,
        "legiscan_id": 99999999,
        "name": "Anti-John Doe",
        "image_url": "example.com/image.png",
        "district": "ED-1",
        "address": "999 Senate Office Building Washington, DC 20510",
        "instagram": "@senantijohndoe",
        "phone": "(202) 111-1112",
        "party_id": 1,
    }
    response = client.put(
        "/legislators", json=non_existent_legislator, headers=system_headers
    )
    assert_status_code(response, 404)
    assert "legislator not found" in response.json()["detail"]


def test_update_legislator_unauthorized(client, test_legislator):
    updated_data = {**test_legislator, "title": "Updated Test legislator"}
    response = client.put(
        "/legislators",
        json=updated_data,
        headers={"Authorization": "Bearer user_token"},
    )
    assert_status_code(response, 403)


def test_get_legislator_success(client, system_headers, test_legislator):
    response = client.get(
        f"/legislators/{test_legislator['id']}", headers=system_headers
    )
    assert_status_code(response, 200)
    retrieved_legislator = response.json()
    assert retrieved_legislator["id"] == test_legislator["id"]
    assert retrieved_legislator["name"] == test_legislator["name"]


def test_get_legislator_not_found(client, system_headers):
    response = client.get("/legislators/9999", headers=system_headers)
    assert_status_code(response, 404)
    assert "legislator not found" in response.json()["detail"]


def test_delete_legislator_success(client, system_headers, test_legislator):
    response = client.delete(
        f"/legislators/{test_legislator['id']}", headers=system_headers
    )
    assert_status_code(response, 204)


def test_delete_legislator_not_found(client, system_headers):
    response = client.delete("/legislators/9999", headers=system_headers)
    assert_status_code(response, 404)
    assert "legislator not found" in response.json()["detail"]


def test_delete_legislator_unauthorized(client, test_legislator):
    response = client.delete(
        f"/legislators/{test_legislator['id']}",
        headers={"Authorization": "Bearer user_token"},
    )
    assert_status_code(response, 403)
