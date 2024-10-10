from api.tests.test_utils import *
from common.database.referendum.models import VoteChoice


def test_cast_vote_success(test_user_session, test_bill):
    user, headers = test_user_session
    vote_data = {"bill_id": test_bill["id"], "vote_choice": VoteChoice.YES.value}
    response = client.put("/votes/", json=vote_data, headers=headers)
    assert_status_code(response, 200)
    created_vote = response.json()
    assert created_vote["user_id"] == user["id"]
    assert created_vote["bill_id"] == test_bill["id"]
    assert created_vote["vote_choice"] == VoteChoice.YES.value


def test_cast_vote_update(test_user_session, test_vote):
    user, headers = test_user_session
    updated_vote_data = {
        "bill_id": test_vote["bill_id"],
        "vote_choice": VoteChoice.NO.value,
    }
    response = client.put("/votes/", json=updated_vote_data, headers=headers)
    assert_status_code(response, 200)
    updated_vote = response.json()
    assert updated_vote["vote_choice"] == VoteChoice.NO.value

    response = client.get(f"/votes/?user_id={user['id']}", headers=system_headers)
    assert_status_code(response, 200)
    votes = response.json()
    assert len(votes) == 1


def test_cast_vote_unauthorized(test_bill):
    vote_data = {"bill_id": test_bill["id"], "vote_choice": VoteChoice.YES.value}
    response = client.put("/votes/", json=vote_data)
    assert_status_code(response, 401)


def test_cast_vote_invalid_bill(test_user_session):
    user, headers = test_user_session
    vote_data = {"bill_id": 9999, "vote_choice": VoteChoice.YES.value}
    response = client.put("/votes/", json=vote_data, headers=headers)
    assert_status_code(response, 500)
    assert "Database error" in response.json()["detail"]


def test_cast_vote_invalid_choice(test_user_session, test_bill):
    user, headers = test_user_session
    vote_data = {"bill_id": test_bill["id"], "vote_choice": "MAYBE"}
    response = client.put("/votes/", json=vote_data, headers=headers)
    assert_status_code(response, 422)


def test_get_votes_for_user(test_user_session, test_vote):
    user, headers = test_user_session
    response = client.get(f"/votes/?user_id={user['id']}", headers=headers)
    assert_status_code(response, 200)
    votes = response.json()
    assert len(votes) > 0
    assert votes[0]["user_id"] == user["id"]


def test_get_votes_for_bill(test_user_session, test_vote):
    user, headers = test_user_session
    response = client.get(
        f"/votes/?bill_id={test_vote['bill_id']}", headers=system_headers
    )
    assert_status_code(response, 200)
    votes = response.json()
    assert len(votes) > 0
    assert votes[0]["bill_id"] == test_vote["bill_id"]


def test_get_votes_unauthorized():
    response = client.get("/votes/?user_id=1")
    assert_status_code(response, 401)


def test_get_votes_for_other_user(test_user_session):
    user, headers = test_user_session
    response = client.get("/votes/?user_id=9999", headers=headers)
    assert_status_code(response, 403)


def test_get_votes_missing_params():
    response = client.get("/votes/", headers=system_headers)
    assert_status_code(response, 400)
    assert "Either user_id or bill_id must be provided" in response.json()["detail"]
