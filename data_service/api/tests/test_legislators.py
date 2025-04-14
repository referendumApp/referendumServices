import pytest
from random import randint

from api.constants import ABSENT_VOTE_ID, NAY_VOTE_ID, YEA_VOTE_ID
from api.tests.conftest import TestManager
from api.tests.test_utils import DEFAULT_ID, assert_status_code


async def test_add_legislator_success(test_manager: TestManager):
    test_legislator = await test_manager.create_legislator()
    assert "id" in test_legislator


async def test_list_legislators(test_manager: TestManager):
    # Create at least one legislator
    await test_manager.create_legislator()
    response = await test_manager.client.post(
        "/legislators/details",
        headers=test_manager.headers,
        json={"federalOnly": False},
    )
    assert_status_code(response, 200)
    legislators = response.json()
    assert legislators["hasMore"] == False
    assert len(legislators["items"]) > 0


@pytest.mark.parametrize(
    "filter_request,expected_length,expected_names",
    [
        ({"filter_options": {"state_id": [1, 2]}}, 2, ["Batman", "Joker"]),
        ({"filter_options": {"role_id": [3]}}, 1, ["Robin"]),
        ({"filter_options": {"party_id": [2, 3], "state_id": [2, 3]}}, 2, ["Joker", "Robin"]),
        ({"filter_options": {"party_id": [3], "role_id": [1]}}, 0, []),
        ({"search_query": "Batman"}, 1, ["Batman"]),
        (
            {"filter_options": {"party_id": [2, 3], "state_id": [2, 3]}, "search_query": "Joker"},
            1,
            ["Joker"],
        ),
        ({"search_query": "Superman"}, 0, []),
    ],
)
async def test_list_legislators_filter(
    filter_request,
    expected_length,
    expected_names,
    test_manager: TestManager,
):
    # Create at least two legislator
    await test_manager.create_legislator(name="Batman", state_id=1, role_id=1, party_id=1)
    await test_manager.create_legislator(name="Joker", state_id=2, role_id=2, party_id=2)
    await test_manager.create_legislator(name="Robin", state_id=3, role_id=3, party_id=3)
    response = await test_manager.client.post(
        "/legislators/details",
        headers=test_manager.headers,
        json={**filter_request, "federalOnly": False},
    )
    assert_status_code(response, 200)
    legislators = response.json()
    assert legislators["hasMore"] == False
    assert len(legislators["items"]) == expected_length
    for legislator in legislators["items"]:
        assert legislator["name"] in expected_names
        assert legislator["followthemoneyEid"]


async def test_invalid_list_legislators_filter(test_manager: TestManager):
    response = await test_manager.client.post(
        "/legislators/details",
        headers=test_manager.headers,
        json={"filter_options": {"status_id": [1]}, "federalOnly": False},
    )
    assert_status_code(response, 422)


async def test_list_legislators_sort(test_manager: TestManager):
    test_names = ["Batman", "Joker", "Robin", "Bane", "Mr. Freeze"]
    for name in test_names:
        await test_manager.create_legislator(name=name)

    response = await test_manager.client.post(
        "/legislators/details",
        headers=test_manager.headers,
        json={"order_by": {"name": "ascending"}, "federalOnly": False},
    )
    assert_status_code(response, 200)
    legislators = response.json()
    assert legislators["hasMore"] == False
    assert len(legislators["items"]) == 5

    sorted_test_names = sorted(test_names)
    for index, legislator in enumerate(legislators["items"]):
        assert legislator["name"] == sorted_test_names[index]


async def test_add_legislator_already_exists(test_manager: TestManager):
    test_legislator = await test_manager.create_legislator()
    legislator_data = {**test_legislator, "id": 9000}
    response = await test_manager.client.post(
        "/legislators/", json=legislator_data, headers=test_manager.headers
    )
    assert_status_code(response, 409)
    assert "legislator already exists" in response.json()["detail"]


async def test_add_legislator_unauthorized(test_manager: TestManager):
    test_legislator = await test_manager.create_legislator()
    legislator_data = {**test_legislator}
    legislator_data.pop("id")
    response = await test_manager.client.post(
        "/legislators/",
        json=legislator_data,
        headers={"Authorization": "Bearer user_token"},
    )
    assert_status_code(response, 403)


async def test_update_legislator_success(test_manager: TestManager):
    test_legislator = await test_manager.create_legislator()
    updated_data = {**test_legislator, "name": "Updated Test legislator"}
    response = await test_manager.client.put(
        "/legislators/", json=updated_data, headers=test_manager.headers
    )
    assert_status_code(response, 200)
    updated_legislator = response.json()
    assert updated_legislator["name"] == "Updated Test legislator"


async def test_update_legislator_not_found(test_manager: TestManager):
    party = await test_manager.create_party()
    state = await test_manager.create_state()
    role = await test_manager.create_role()

    non_existent_legislator = {
        "id": DEFAULT_ID * 2,
        "legiscanId": str(DEFAULT_ID * 2),
        "name": "Anti-John Doe",
        "imageUrl": "example.com/image.png",
        "district": "ED-1",
        "address": "999 Senate Office Building Washington, DC 20510",
        "instagram": "@senantijohndoe",
        "phone": "(202) 111-1112",
        "partyId": party["id"],
        "stateId": state["id"],
        "roleId": role["id"],
        "followthemoneyEid": str(randint(100, 99999)),
    }
    response = await test_manager.client.put(
        "/legislators/", json=non_existent_legislator, headers=test_manager.headers
    )
    assert_status_code(response, 404)
    assert "legislator not found" in response.json()["detail"]


async def test_update_legislator_unauthorized(test_manager: TestManager):
    test_legislator = await test_manager.create_legislator()
    updated_data = {**test_legislator, "title": "Updated Test legislator"}
    response = await test_manager.client.put(
        "/legislators/",
        json=updated_data,
        headers={"Authorization": "Bearer user_token"},
    )
    assert_status_code(response, 403)


async def test_get_legislator_success(test_manager: TestManager):
    test_legislator = await test_manager.create_legislator()
    response = await test_manager.client.get(
        f"/legislators/{test_legislator['id']}", headers=test_manager.headers
    )
    assert_status_code(response, 200)
    retrieved_legislator = response.json()
    assert retrieved_legislator["id"] == test_legislator["id"]
    assert retrieved_legislator["name"] == test_legislator["name"]


async def test_get_legislator_not_found(test_manager: TestManager):
    response = await test_manager.client.get("/legislators/9999", headers=test_manager.headers)
    assert_status_code(response, 404)
    assert "legislator not found" in response.json()["detail"]


async def test_delete_legislator_success(test_manager: TestManager):
    test_legislator = await test_manager.create_legislator()
    response = await test_manager.client.delete(
        f"/legislators/{test_legislator['id']}", headers=test_manager.headers
    )
    assert_status_code(response, 204)


async def test_delete_legislator_not_found(test_manager: TestManager):
    response = await test_manager.client.delete("/legislators/9999", headers=test_manager.headers)
    assert_status_code(response, 404)
    assert "legislator not found" in response.json()["detail"]


async def test_delete_legislator_unauthorized(test_manager: TestManager):
    test_legislator = await test_manager.create_legislator()
    response = await test_manager.client.delete(
        f"/legislators/{test_legislator['id']}",
        headers={"Authorization": "Bearer user_token"},
    )
    assert_status_code(response, 403)


async def test_get_legislator_voting_history(test_manager: TestManager):
    # Create a test legislator and bill action
    test_legislator = await test_manager.create_legislator()
    test_bill_action = await test_manager.create_bill_action()

    # Create legislator vote
    response = await test_manager.client.put(
        "/legislator_votes/",
        json={
            "billId": test_bill_action["billId"],
            "billActionId": test_bill_action["id"],
            "legislatorId": test_legislator["id"],
            "voteChoiceId": YEA_VOTE_ID,
        },
        headers=test_manager.headers,
    )
    assert_status_code(response, 200)
    test_legislator_vote = response.json()

    test_error = None
    try:
        bill_response = await test_manager.client.get(
            f"/bills/{test_legislator_vote['billId']}",
            headers=test_manager.headers,
        )
        action_response = await test_manager.client.get(
            f"/bill_actions/{test_legislator_vote['billActionId']}",
            headers=test_manager.headers,
        )
        vote_choice_response = await test_manager.client.get(
            "/vote_choices/", headers=test_manager.headers
        )
        voting_response = await test_manager.client.get(
            f"/legislators/{test_legislator_vote['legislatorId']}/voting_history",
            headers=test_manager.headers,
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
        assert any(choice["id"] == bill_action_votes["voteChoiceId"] for choice in vote_choice)
    except Exception as e:
        test_error = str(e)

    response = await test_manager.client.delete(
        "/legislator_votes/",
        params={
            "bill_action_id": test_bill_action["id"],
            "legislator_id": test_legislator["id"],
        },
        headers=test_manager.headers,
    )
    assert_status_code(response, 204)

    if test_error:
        raise Exception(test_error)


async def test_get_legislator_scores_empty(test_manager: TestManager):
    """Test scores for a legislator with no votes."""
    test_legislator = await test_manager.create_legislator()

    try:
        response = await test_manager.client.get(
            f"/legislators/{test_legislator['id']}/scorecard", headers=test_manager.headers
        )
        assert_status_code(response, 200)
        scores = response.json()
        assert scores["delinquency"] == 0
        assert scores["bipartisanship"] == 0
    finally:
        # Cleanup
        await test_manager.client.delete(
            f"/legislators/{test_legislator['id']}",
            headers=test_manager.headers,
        )


async def test_get_legislator_scores_with_votes(test_manager: TestManager):
    """Test scores for a legislator with a mix of votes."""
    # Setup
    test_legislator = await test_manager.create_legislator(party_name="Democratic")
    opposing_legislator = await test_manager.create_legislator(party_name="Republican")

    bill1 = await test_manager.create_bill()
    bill1_action = await test_manager.create_bill_action(bill_id=bill1["id"])
    bill2 = await test_manager.create_bill()
    bill2_action = await test_manager.create_bill_action(bill_id=bill2["id"])

    votes_data = [
        # Bill 1 votes
        {
            "billId": bill1["id"],
            "billActionId": bill1_action["id"],
            "legislatorId": test_legislator["id"],
            "voteChoiceId": YEA_VOTE_ID,
        },
        {
            "billId": bill1["id"],
            "billActionId": bill1_action["id"],
            "legislatorId": opposing_legislator["id"],
            "voteChoiceId": NAY_VOTE_ID,
        },
        # Bill 2 votes
        {
            "billId": bill2["id"],
            "billActionId": bill2_action["id"],
            "legislatorId": test_legislator["id"],
            "voteChoiceId": YEA_VOTE_ID,
        },
        {
            "billId": bill2["id"],
            "billActionId": bill2_action["id"],
            "legislatorId": opposing_legislator["id"],
            "voteChoiceId": YEA_VOTE_ID,
        },
    ]

    test_error = None
    try:
        for vote_data in votes_data:
            response = await test_manager.client.put(
                "/legislator_votes/",
                json=vote_data,
                headers=test_manager.headers,
            )
            assert_status_code(response, 200)

        response = await test_manager.client.get(
            f"/legislators/{test_legislator['id']}/scorecard", headers=test_manager.headers
        )
        assert_status_code(response, 200)
        scores = response.json()

        assert scores["delinquency"] == 0
        assert scores["bipartisanship"] == 0.5

    except Exception as e:
        test_error = str(e)

    for vote_data in votes_data:
        await test_manager.client.delete(
            "/legislator_votes/",
            params={
                "bill_action_id": vote_data["billActionId"],
                "legislator_id": vote_data["legislatorId"],
            },
            headers=test_manager.headers,
        )

    if test_error:
        raise Exception(test_error)


async def test_get_legislator_scores_all_absent(test_manager: TestManager):
    """Test scores for a legislator who is absent for all votes."""
    # Setup
    test_legislator = await test_manager.create_legislator()
    bill = await test_manager.create_bill()
    bill_action = await test_manager.create_bill_action(bill_id=bill["id"])

    test_error = None
    try:
        response = await test_manager.client.put(
            "/legislator_votes/",
            json={
                "billId": bill["id"],
                "billActionId": bill_action["id"],
                "legislatorId": test_legislator["id"],
                "voteChoiceId": ABSENT_VOTE_ID,
            },
            headers=test_manager.headers,
        )
        assert_status_code(response, 200)

        response = await test_manager.client.get(
            f"/legislators/{test_legislator['id']}/scorecard", headers=test_manager.headers
        )
        assert_status_code(response, 200)
        scores = response.json()

        assert scores["delinquency"] == 1
        assert scores["bipartisanship"] == 0

    except Exception as e:
        test_error = str(e)

    await test_manager.client.delete(
        "/legislator_votes/",
        params={
            "bill_action_id": bill_action["id"],
            "legislator_id": test_legislator["id"],
        },
        headers=test_manager.headers,
    )

    if test_error:
        raise Exception(test_error)
