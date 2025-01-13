import logging
import pytest

from api.tests.conftest import TestManager
from api.tests.test_utils import assert_status_code
from api.constants import YEA_VOTE_ID


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

    test_error = None
    try:
        response = await client.post("/bills/details", headers=system_headers, json={})
        assert_status_code(response, 200)
        bill_data = response.json()
        assert bill_data["hasMore"] == False
        assert len(bill_data["items"]) == 1
        bill = bill_data["items"][0]

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
    except Exception as e:
        test_error = str(e)
        logging.error(f"Test failed with {test_error}, marking and cleaning up")

    # Remove sponsor
    response = await client.delete(
        f"/bills/{test_bill_version['billId']}/sponsors/{test_legislator['id']}",
        headers=system_headers,
    )
    assert_status_code(response, 204)

    if test_error:
        raise Exception(test_error)


@pytest.mark.parametrize(
    "filter_request,expected_length,expected_titles",
    [
        ({"filter_options": {"state_id": [1, 2]}}, 2, ["Batman", "Joker"]),
        ({"filter_options": {"role_id": [3]}}, 1, ["Robin"]),
        ({"filter_options": {"status_id": [2, 3], "state_id": [2, 3]}}, 2, ["Joker", "Robin"]),
        ({"filter_options": {"status_id": [3], "role_id": [1]}}, 0, []),
        ({"search_query": "Batman"}, 1, ["Batman"]),
        ({"search_query": "BT"}, 2, ["Batman", "Robin"]),
        (
            {"filter_options": {"status_id": [2, 3], "state_id": [2, 3]}, "search_query": "Joker"},
            1,
            ["Joker"],
        ),
        ({"search_query": "Superman"}, 0, []),
    ],
)
async def test_list_bill_details_filter(
    filter_request,
    expected_length,
    expected_titles,
    test_manager: TestManager,
):
    # Create at least two legislator
    await test_manager.create_bill(
        identifier="BT1",
        title="Batman",
        state_id=1,
        role_id=1,
        status_id=1,
    )
    await test_manager.create_bill(
        identifier="JO1",
        title="Joker",
        state_id=2,
        role_id=2,
        status_id=2,
    )
    await test_manager.create_bill(
        identifier="BT2",
        title="Robin",
        state_id=3,
        role_id=3,
        status_id=3,
    )
    response = await test_manager.client.post(
        "/bills/details",
        headers=test_manager.headers,
        json=filter_request,
    )
    assert_status_code(response, 200)
    bills = response.json()
    assert bills["hasMore"] == False
    assert len(bills["items"]) == expected_length
    for bill in bills["items"]:
        assert bill["title"] in expected_titles


async def test_invalid_list_bills_filter(test_manager: TestManager):
    response = await test_manager.client.post(
        "/bills/details",
        headers=test_manager.headers,
        json={"filter_options": {"party_id": [1]}},
    )
    assert_status_code(response, 400)


async def test_list_bill_details_sort(test_manager: TestManager):
    test_titles = ["Batman", "Joker", "Robin", "Bane", "Mr. Freeze"]
    for title in test_titles:
        await test_manager.create_bill(title=title)

    response = await test_manager.client.post(
        "/bills/details",
        headers=test_manager.headers,
        json={"order_by": "title"},
    )
    assert_status_code(response, 200)
    bills = response.json()
    assert bills["hasMore"] == False
    assert len(bills["items"]) == 5

    sorted_test_titles = sorted(test_titles)
    for index, bill in enumerate(bills["items"]):
        assert bill["title"] == sorted_test_titles[index]


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


async def test_bill_user_votes(client, system_headers, test_manager: TestManager):
    _, headers = await test_manager.start_user_session()
    test_bill = await test_manager.create_bill()

    vote_data = {
        "billId": test_bill["id"],
        "voteChoiceId": YEA_VOTE_ID,
    }
    response = await client.put("/users/votes/", json=vote_data, headers=headers)
    test_error = None
    try:
        assert_status_code(response, 200)

        response = await client.get(f"/bills/{test_bill['id']}/user_votes", headers=system_headers)
        assert_status_code(response, 200)
        bill_votes = response.json()
        assert bill_votes["yea"] > 0
        assert bill_votes["nay"] == 0
    except Exception as e:
        test_error = str(e)
        logging.error(f"Test failed with {test_error}, marking and cleaning up")

    response = await client.delete(
        f"/users/votes?billId={test_bill['id']}",
        headers=headers,
    )
    assert_status_code(response, 204)

    if test_error:
        raise Exception(test_error)


async def test_voting_history(client, system_headers, test_manager: TestManager):
    test_legislator = await test_manager.create_legislator()
    test_bill_action = await test_manager.create_bill_action()

    response = await client.put(
        "/legislator_votes/",
        json={
            "billId": test_bill_action["billId"],
            "billActionId": test_bill_action["id"],
            "legislatorId": test_legislator["id"],
            "voteChoiceId": YEA_VOTE_ID,
        },
        headers=system_headers,
    )
    assert_status_code(response, 200)
    test_legislator_vote = response.json()
    test_error = None
    try:
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
    except Exception as e:
        test_error = str(e)
        logging.error(f"Test failed with {test_error}, marking and cleaning up")

    # Cleanup vote
    response = await client.delete(
        "/legislator_votes/",
        params={"bill_action_id": test_bill_action["id"], "legislator_id": test_legislator["id"]},
        headers=system_headers,
    )
    assert_status_code(response, 204)

    if test_error:
        raise Exception(test_error)
