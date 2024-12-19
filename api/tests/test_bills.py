from api.tests.conftest import TestManager
from api.tests.test_utils import DEFAULT_ID, assert_status_code


async def test_add_bill_success(test_manager: TestManager):
    test_bill = await test_manager.create_bill()
    assert "id" in test_bill


async def test_list_bill_details(client, system_headers, test_manager: TestManager):
    test_legislator = await test_manager.create_legislator()
    test_bill_version = await test_manager.create_bill_version()

    # Add sponsor
    response = await client.post(
        f"/bills/{test_bill_version['billId']}/sponsors/{test_legislator['id']}",
        headers=system_headers,
    )
    assert_status_code(response, 204)

    response = await client.get("/bills/details", headers=system_headers)
    assert_status_code(response, 200)
    bill_data = response.json()
    assert len(bill_data) == 1
    bill = bill_data[0]

    expected_fields = [
        "billId",
        "description",
        "statusId",
        "status",
        "statusDate",
        "sessionId",
        "stateName",
        "legislativeBodyRole",
        "sponsors",
    ]
    assert all(field in bill for field in expected_fields)

    # Remove sponsor
    response = await client.delete(
        f"/bills/{test_bill_version['billId']}/sponsors/{test_legislator['id']}",
        headers=system_headers,
    )
    assert_status_code(response, 204)


async def test_add_bill_already_exists(client, system_headers, test_manager: TestManager):
    test_bill = await test_manager.create_bill()
    bill_data = {**test_bill, "id": 9000}
    response = await client.post("/bills/", json=bill_data, headers=system_headers)
    assert_status_code(response, 409)
    assert "bill already exists" in response.json()["detail"]


async def test_add_bill_unauthorized(client, test_manager: TestManager):
    test_bill = await test_manager.create_bill()
    bill_data = {**test_bill}
    bill_data.pop("id")
    response = await client.post(
        "/bills/",
        json=bill_data,
        headers={"Authorization": "Bearer user_token"},
    )
    assert_status_code(response, 403)


async def test_update_bill(client, system_headers, test_manager: TestManager):
    test_bill = await test_manager.create_bill()
    updated_data = {**test_bill, "title": "Updated Bill Title"}
    response = await client.put("/bills/", json=updated_data, headers=system_headers)
    assert_status_code(response, 200)
    updated_bill = response.json()
    assert updated_bill["title"] == "Updated Bill Title"


async def test_update_bill_not_found(client, system_headers, test_manager: TestManager):
    test_status = await test_manager.create_status()
    non_existent_bill = {
        "id": 9999,
        "legiscanId": 0,
        "identifier": "DNE.1",
        "title": "Non-existent Bill",
        "description": "This bill does not exist",
        "stateId": 1,
        "legislativeBodyId": 1,
        "sessionId": 118,
        "statusId": test_status["id"],
        "status_date": "2024-01-01",
        "currentVersionId": 0,
    }
    response = await client.put("/bills/", json=non_existent_bill, headers=system_headers)
    assert_status_code(response, 404)
    assert "bill not found" in response.json()["detail"]


async def test_update_bill_unauthorized(client, test_manager: TestManager):
    test_bill = await test_manager.create_bill()
    updated_data = {**test_bill, "title": "Updated Test Bill"}
    response = await client.put(
        "/bills/", json=updated_data, headers={"Authorization": "Bearer user_token"}
    )
    assert_status_code(response, 403)


async def test_get_bill_success(client, system_headers, test_manager: TestManager):
    test_bill = await test_manager.create_bill()
    response = await client.get(f"/bills/{test_bill['id']}", headers=system_headers)
    assert_status_code(response, 200)
    retrieved_bill = response.json()
    assert retrieved_bill["id"] == test_bill["id"]
    assert retrieved_bill["title"] == test_bill["title"]


async def test_get_bill_not_found(client, system_headers):
    response = await client.get("/bills/9999", headers=system_headers)
    assert_status_code(response, 404)
    assert "bill not found" in response.json()["detail"]


async def test_delete_bill_success(client, system_headers, test_manager: TestManager):
    test_bill = await test_manager.create_bill()
    response = await client.delete(f"/bills/{test_bill['id']}", headers=system_headers)
    assert_status_code(response, 204)


async def test_delete_bill_not_found(client, system_headers):
    response = await client.delete("/bills/9999", headers=system_headers)
    assert_status_code(response, 404)
    assert "bill not found" in response.json()["detail"]


async def test_delete_bill_unauthorized(client, test_manager: TestManager):
    test_bill = await test_manager.create_bill()
    response = await client.delete(
        f"/bills/{test_bill['id']}", headers={"Authorization": "Bearer user_token"}
    )
    assert_status_code(response, 403)


async def test_add_remove_bill_topic(client, system_headers, test_manager: TestManager):
    test_bill = await test_manager.create_bill()
    test_topic = await test_manager.create_topic()
    # Add topic to bill
    response = await client.post(
        f"/bills/{test_bill['id']}/topics/{test_topic['id']}", headers=system_headers
    )
    assert_status_code(response, 204)

    # Check that it exists
    response = await client.get(f"/bills/{test_bill['id']}", headers=system_headers)
    assert_status_code(response, 200)
    topics = response.json()["topics"]
    assert len(topics) == 1
    assert topics[0]["id"] == test_topic["id"]

    # Remove topic from bill
    response = await client.delete(
        f"/bills/{test_bill['id']}/topics/{test_topic['id']}", headers=system_headers
    )
    assert_status_code(response, 204)

    # Check that it's gone
    response = await client.get(f"/bills/{test_bill['id']}", headers=system_headers)
    assert_status_code(response, 200)
    topics = response.json()["topics"]
    assert len(topics) == 0


async def test_add_remove_bill_sponsor(client, system_headers, test_manager: TestManager):
    test_bill = await test_manager.create_bill()
    test_legislator = await test_manager.create_legislator()
    # Add legislator to bill
    response = await client.post(
        f"/bills/{test_bill['id']}/sponsors/{test_legislator['id']}",
        headers=system_headers,
    )
    assert_status_code(response, 204)

    # Check that it exists
    response = await client.get(f"/bills/{test_bill['id']}", headers=system_headers)
    assert_status_code(response, 200)
    sponsors = response.json()["sponsors"]
    assert len(sponsors) == 1
    assert sponsors[0]["legislatorId"] == test_legislator["id"]

    # Remove sponsor from bill
    response = await client.delete(
        f"/bills/{test_bill['id']}/sponsors/{test_legislator['id']}",
        headers=system_headers,
    )
    assert_status_code(response, 204)

    # Check that it's gone
    response = await client.get(f"/bills/{test_bill['id']}", headers=system_headers)
    assert_status_code(response, 200)
    sponsors = response.json()["sponsors"]
    assert len(sponsors) == 0


async def test_bulk_update_success(client, system_headers, test_manager: TestManager):
    # Test successful bulk update
    test_bill = await test_manager.create_bill()
    update_data = [{**test_bill, "title": f"Updated {test_bill['title']}"}]
    response = await client.put("/bills/bulk", json=update_data, headers=system_headers)
    assert_status_code(response, 200)
    updated_items = response.json()
    for i, item in enumerate(updated_items):
        assert item["title"] == update_data[i]["title"]


async def test_bill_user_votes(client, system_headers, test_user_vote):
    response = await client.get(
        f"/bills/{test_user_vote['billId']}/user_votes", headers=system_headers
    )
    assert_status_code(response, 200)
    bill_votes = response.json()
    assert bill_votes["yay"] > 0
    assert bill_votes["nay"] == 0


async def test_voting_history(client, system_headers, test_legislator_vote):
    response = await client.get(
        f"/bills/{test_legislator_vote['billId']}/voting_history", headers=system_headers
    )
    assert_status_code(response, 200)
    result = response.json()

    # Check top level structure
    assert set(result.keys()) == {"billId", "votes", "summaries"}
    assert result["billId"] == test_legislator_vote["billId"]

    # Check votes array structure
    assert isinstance(result["votes"], list)
    assert len(result["votes"]) == 1
    vote = result["votes"][0]
    required_vote_keys = {
        "billActionId",
        "date",
        "actionDescription",
        "legislatorVotes",
    }
    assert set(vote.keys()) == required_vote_keys
    assert vote["billActionId"] == test_legislator_vote["billActionId"]

    assert isinstance(vote["legislatorVotes"], list)
    assert len(vote["legislatorVotes"]) == 1
    legislator_vote = vote["legislatorVotes"][0]
    required_legislator_vote_keys = {
        "legislatorId",
        "legislatorName",
        "partyName",
        "roleName",
        "stateName",
        "voteChoiceId",
    }
    assert set(legislator_vote.keys()) == required_legislator_vote_keys
    assert legislator_vote["legislatorId"] == test_legislator_vote["legislatorId"]

    assert isinstance(result["summaries"], list)
    assert len(result["summaries"]) == 1
    summary = result["summaries"][0]
    assert set(summary.keys()) == {
        "billActionId",
        "totalVotes",
        "voteCountsByChoice",
        "voteCountsByParty",
    }

    assert isinstance(summary["voteCountsByChoice"], list)
    assert len(summary["voteCountsByChoice"]) == 1
    vote_choice = summary["voteCountsByChoice"][0]
    assert set(vote_choice.keys()) == {"voteChoiceId", "count"}
    assert vote_choice["voteChoiceId"] == test_legislator_vote["voteChoiceId"]
    assert vote_choice["count"] == 1

    assert isinstance(summary["voteCountsByParty"], list)
    assert len(summary["voteCountsByParty"]) == 1
    party_count = summary["voteCountsByParty"][0]
    assert set(party_count.keys()) == {"voteChoiceId", "partyId", "count"}
    assert party_count["count"] == 1
