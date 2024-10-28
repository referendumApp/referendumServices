from api.tests.test_utils import assert_status_code


async def test_add_legislator_success(test_legislator):
    assert "id" in test_legislator


async def test_list_legislators(test_get_legislators):
    assert len(test_get_legislators) > 0


async def test_add_legislator_already_exists(client, system_headers, test_legislator):
    legislator_data = {**test_legislator, "id": 9000}
    response = await client.post("/legislators/", json=legislator_data, headers=system_headers)
    assert_status_code(response, 409)
    assert "legislator already exists" in response.json()["detail"]


async def test_add_legislator_unauthorized(client, test_legislator):
    legislator_data = {**test_legislator}
    legislator_data.pop("id")
    response = await client.post(
        "/legislators/",
        json=legislator_data,
        headers={"Authorization": "Bearer user_token"},
    )
    assert_status_code(response, 403)


async def test_update_legislator_success(client, system_headers, test_legislator):
    updated_data = {**test_legislator, "name": "Updated Test legislator"}
    response = await client.put("/legislators/", json=updated_data, headers=system_headers)
    assert_status_code(response, 200)
    updated_legislator = response.json()
    assert updated_legislator["name"] == "Updated Test legislator"


async def test_update_legislator_not_found(client, system_headers):
    non_existent_legislator = {
        "id": 9999,
        "legiscanId": 99999999,
        "name": "Anti-John Doe",
        "image_url": "example.com/image.png",
        "district": "ED-1",
        "address": "999 Senate Office Building Washington, DC 20510",
        "instagram": "@senantijohndoe",
        "phone": "(202) 111-1112",
        "partyId": 1,
        "stateId": 1,
    }
    response = await client.put(
        "/legislators/", json=non_existent_legislator, headers=system_headers
    )
    assert_status_code(response, 404)
    assert "legislator not found" in response.json()["detail"]


async def test_update_legislator_unauthorized(client, test_legislator):
    updated_data = {**test_legislator, "title": "Updated Test legislator"}
    response = await client.put(
        "/legislators/",
        json=updated_data,
        headers={"Authorization": "Bearer user_token"},
    )
    assert_status_code(response, 403)


async def test_get_legislator_success(client, system_headers, test_legislator):
    response = await client.get(f"/legislators/{test_legislator['id']}", headers=system_headers)
    assert_status_code(response, 200)
    retrieved_legislator = response.json()
    assert retrieved_legislator["id"] == test_legislator["id"]
    assert retrieved_legislator["name"] == test_legislator["name"]


async def test_get_legislator_not_found(client, system_headers):
    response = await client.get("/legislators/9999", headers=system_headers)
    assert_status_code(response, 404)
    assert "legislator not found" in response.json()["detail"]


async def test_delete_legislator_success(client, system_headers, test_legislator):
    response = await client.delete(f"/legislators/{test_legislator['id']}", headers=system_headers)
    assert_status_code(response, 204)


async def test_delete_legislator_not_found(client, system_headers):
    response = await client.delete("/legislators/9999", headers=system_headers)
    assert_status_code(response, 404)
    assert "legislator not found" in response.json()["detail"]


async def test_delete_legislator_unauthorized(client, test_legislator):
    response = await client.delete(
        f"/legislators/{test_legislator['id']}",
        headers={"Authorization": "Bearer user_token"},
    )
    assert_status_code(response, 403)
