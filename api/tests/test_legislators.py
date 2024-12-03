from api.tests.test_utils import DEFAULT_ID, assert_status_code


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
        "id": DEFAULT_ID * 2,
        "legiscanId": DEFAULT_ID * 2,
        "name": "Anti-John Doe",
        "image_url": "example.com/image.png",
        "district": "ED-1",
        "address": "999 Senate Office Building Washington, DC 20510",
        "instagram": "@senantijohndoe",
        "phone": "(202) 111-1112",
        "partyId": 1,
        "stateId": 1,
        "roleId": 1,
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


async def test_get_legislator_voting_history(client, system_headers, test_legislator_vote):
    bill_response = await client.get(
        f"/bills/{test_legislator_vote['billId']}",
        headers=system_headers,
    )
    action_response = await client.get(
        f"/bill_actions/{test_legislator_vote['billActionId']}",
        headers=system_headers,
    )
    vote_choice_response = await client.get("/vote_choices/", headers=system_headers)
    voting_response = await client.get(
        f"/legislators/{test_legislator_vote['legislatorId']}/voting_history",
        headers=system_headers,
    )
    assert_status_code(voting_response, 200)

    bill = bill_response.json()
    action = action_response.json()
    vote_choice = vote_choice_response.json()
    voting_history = voting_response.json()[0]

    assert voting_history["billId"] == bill["id"]
    assert voting_history["identifier"] == bill["identifier"]
    assert voting_history["title"] == bill["title"]

    bill_action_votes = voting_history["billActionVotes"][0]
    assert bill_action_votes["billActionId"] == action["id"]
    assert bill_action_votes["date"] == action["date"]
    assert bill_action_votes["actionDescription"] == action["description"]
    assert any(choice["name"] == bill_action_votes["voteChoiceName"] for choice in vote_choice)
