from api.tests.test_utils import assert_status_code
from common.database.referendum.models import VoteChoice


async def test_cast_vote_success(client, test_user_session, test_bill):
    user, headers = test_user_session
    vote_data = {"bill_id": test_bill["id"], "vote_choice": VoteChoice.YES.value}
    response = await client.put(f"/users/{user['id']}/votes", json=vote_data, headers=headers)
    assert_status_code(response, 200)
    created_vote = response.json()
    assert created_vote["userId"] == user["id"]
    assert created_vote["billId"] == test_bill["id"]
    assert created_vote["voteChoice"] == VoteChoice.YES.value


async def test_cast_vote_update(client, system_headers, test_user_session, test_vote):
    user, headers = test_user_session
    updated_vote_data = {
        "bill_id": test_vote["bill_id"],
        "vote_choice": VoteChoice.NO.value,
    }
    response = await client.put(
        f"/users/{user['id']}/votes", json=updated_vote_data, headers=headers
    )
    assert_status_code(response, 200)
    updated_vote = response.json()
    assert updated_vote["voteChoice"] == VoteChoice.NO.value

    response = await client.get(f"/users/{user['id']}/votes", headers=system_headers)
    assert_status_code(response, 200)
    votes = response.json()
    assert len(votes) == 1


async def test_cast_vote_unauthorized(client, test_bill):
    vote_data = {"bill_id": test_bill["id"], "vote_choice": VoteChoice.YES.value}
    response = await client.put("/users/0/votes", json=vote_data)
    assert_status_code(response, 401)


async def test_cast_vote_invalid_bill(client, test_user_session):
    user, headers = test_user_session
    vote_data = {"bill_id": 9999, "vote_choice": VoteChoice.YES.value}
    response = await client.put(f"/users/{user['id']}/votes", json=vote_data, headers=headers)
    assert_status_code(response, 500)
    assert "Database error" in response.json()["detail"]


async def test_cast_vote_invalid_choice(client, test_user_session, test_bill):
    user, headers = test_user_session
    vote_data = {"bill_id": test_bill["id"], "vote_choice": "MAYBE"}
    response = await client.put(f"/users/{user['id']}/votes", json=vote_data, headers=headers)
    assert_status_code(response, 422)


async def test_get_votes_for_user(client, test_user_session, test_vote):
    user, headers = test_user_session
    response = await client.get(f"/users/{user['id']}/votes", headers=headers)
    assert_status_code(response, 200)
    votes = response.json()
    assert len(votes) > 0
    assert votes[0]["userId"] == user["id"]


async def test_get_votes_for_bill(client, system_headers, test_vote):
    response = await client.get(
        f"/users/{test_vote['user_id']}/votes/?bill_id={test_vote['bill_id']}",
        headers=system_headers,
    )
    assert_status_code(response, 200)
    votes = response.json()
    assert len(votes) > 0
    assert votes[0]["billId"] == test_vote["bill_id"]


async def test_get_votes_unauthorized(client):
    response = await client.get("/users/1/votes")
    assert_status_code(response, 401)


async def test_get_votes_for_other_user(client, test_user_session):
    _, headers = test_user_session
    response = await client.get("/users/9999/votes", headers=headers)
    assert_status_code(response, 403)
