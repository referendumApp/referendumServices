from api.tests.test_utils import assert_status_code, NO_VOTE_ID


async def test_cast_vote_success(test_user_vote):
    assert "voteChoiceId" in test_user_vote


async def test_cast_vote_update(
    client, system_headers, test_user_vote, test_user_session, test_vote_choices
):
    _, user_headers = test_user_session
    yay_vote, nay_vote = test_vote_choices

    updated_vote_data = {"billId": test_user_vote["billId"], "voteChoiceId": NO_VOTE_ID}
    response = await client.put("/users/votes", json=updated_vote_data, headers=user_headers)
    assert_status_code(response, 200)
    updated_vote = response.json()
    assert updated_vote["voteChoiceId"] == nay_vote["id"]

    response = await client.get("/users/votes", headers=user_headers)
    assert_status_code(response, 200)
    votes = response.json()
    assert len(votes) == 1


async def test_cast_vote_unauthorized(client, test_bill, test_vote_choice):
    vote_data = {"billId": test_bill["id"], "voteChoiceId": test_vote_choice["id"]}
    response = await client.put("/users/votes", json=vote_data)
    assert_status_code(response, 401)


async def test_cast_vote_invalid_bill(client, test_user_session, test_vote_choice):
    _, headers = test_user_session
    vote_data = {"billId": 9999, "voteChoiceId": test_vote_choice["id"]}
    response = await client.put("/users/votes", json=vote_data, headers=headers)
    assert_status_code(response, 500)
    assert "Database error" in response.json()["detail"]


async def test_cast_vote_invalid_choice(client, test_user_session, test_bill):
    _, headers = test_user_session
    vote_data = {"billId": test_bill["id"], "vote_choice": "MAYBE"}
    response = await client.put("/users/votes", json=vote_data, headers=headers)
    assert_status_code(response, 422)


async def test_get_votes_for_user(client, test_user_session, test_user_vote):
    user, headers = test_user_session
    response = await client.get("/users/votes", headers=headers)
    assert_status_code(response, 200)
    votes = response.json()
    assert len(votes) > 0
    assert votes[0]["userId"] == user["id"]


async def test_get_votes_for_bill(client, system_headers, test_user_vote):
    response = await client.get(
        f"/users/admin/{test_user_vote['userId']}/votes/?bill_id={test_user_vote['billId']}",
        headers=system_headers,
    )
    assert_status_code(response, 200)
    votes = response.json()
    assert len(votes) > 0
    assert votes[0]["billId"] == test_user_vote["billId"]


async def test_get_votes_unauthorized(client):
    response = await client.get("/users/votes")
    assert_status_code(response, 401)


async def test_get_votes_for_other_user(client, test_user_session):
    _, headers = test_user_session
    response = await client.get("/users/admin/9999/votes", headers=headers)
    assert_status_code(response, 403)
