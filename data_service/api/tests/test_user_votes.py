from api.tests.conftest import TestManager
from api.tests.test_utils import assert_status_code
from api.constants import NAY_VOTE_ID, YEA_VOTE_ID
import logging


async def test_cast_vote_success(test_manager: TestManager):
    user, user_headers = await test_manager.start_user_session()
    test_bill = await test_manager.create_bill()

    vote_data = {
        "billId": test_bill["id"],
        "voteChoiceId": YEA_VOTE_ID,
    }
    response = await test_manager.client.put("/users/votes", json=vote_data, headers=user_headers)
    test_error = None
    try:
        assert_status_code(response, 200)
        test_user_vote = response.json()
        assert "voteChoiceId" in test_user_vote
    except Exception as e:
        test_error = str(e)
        logging.error(f"Test failed with {test_error}, marking and cleaning up")

    # Cleanup
    response = await test_manager.client.delete(
        f"/users/votes?billId={test_bill['id']}",
        headers=user_headers,
    )
    assert_status_code(response, 204)

    if test_error:
        raise Exception(test_error)


async def test_cast_vote_update(test_manager: TestManager):
    user, user_headers = await test_manager.start_user_session()
    test_bill = await test_manager.create_bill()

    # Create initial vote
    vote_data = {
        "billId": test_bill["id"],
        "voteChoiceId": YEA_VOTE_ID,
    }
    response = await test_manager.client.put("/users/votes", json=vote_data, headers=user_headers)
    assert_status_code(response, 200)
    test_user_vote = response.json()

    test_error = None
    try:
        # Update the vote
        updated_vote_data = {"billId": test_user_vote["billId"], "voteChoiceId": NAY_VOTE_ID}
        response = await test_manager.client.put(
            "/users/votes", json=updated_vote_data, headers=user_headers
        )

        assert_status_code(response, 200)
        updated_vote = response.json()
        assert updated_vote["voteChoiceId"] == NAY_VOTE_ID

        # Verify vote count
        response = await test_manager.client.get("/users/votes", headers=user_headers)

        assert_status_code(response, 200)
        votes = response.json()
        assert len(votes) == 1
    except Exception as e:
        test_error = str(e)
        logging.error(f"Test failed with {test_error}, marking and cleaning up")

    # Cleanup
    response = await test_manager.client.delete(
        f"/users/votes?billId={test_bill['id']}",
        headers=user_headers,
    )
    assert_status_code(response, 204)

    if test_error:
        raise Exception(test_error)


async def test_cast_vote_unauthorized(test_manager: TestManager):
    test_bill = await test_manager.create_bill()

    vote_data = {"billId": test_bill["id"], "voteChoiceId": YEA_VOTE_ID}
    response = await test_manager.client.put("/users/votes", json=vote_data)
    assert_status_code(response, 403)


async def test_cast_vote_invalid_bill(test_manager: TestManager):
    _, user_headers = await test_manager.start_user_session()

    vote_data = {"billId": 9999, "voteChoiceId": YEA_VOTE_ID}
    response = await test_manager.client.put("/users/votes", json=vote_data, headers=user_headers)
    assert_status_code(response, 400)
    assert "Database error" in response.json()["detail"]


async def test_cast_vote_invalid_choice(test_manager: TestManager):
    _, user_headers = await test_manager.start_user_session()
    test_bill = await test_manager.create_bill()

    vote_data = {"billId": test_bill["id"], "vote_choice": "MAYBE"}
    response = await test_manager.client.put("/users/votes", json=vote_data, headers=user_headers)
    assert_status_code(response, 422)


async def test_get_votes_for_user(test_manager: TestManager):
    user, user_headers = await test_manager.start_user_session()
    test_bill = await test_manager.create_bill()

    # Create a vote
    vote_data = {
        "billId": test_bill["id"],
        "voteChoiceId": YEA_VOTE_ID,
    }
    response = await test_manager.client.put("/users/votes", json=vote_data, headers=user_headers)
    assert_status_code(response, 200)

    test_error = None
    try:
        # Get user's votes
        response = await test_manager.client.get("/users/votes", headers=user_headers)
        assert_status_code(response, 200)
        votes = response.json()
        assert len(votes) > 0
        assert votes[0]["userId"] == user["id"]
    except Exception as e:
        test_error = str(e)
        logging.error(f"Test failed with {test_error}, marking and cleaning up")

    # Cleanup
    response = await test_manager.client.delete(
        f"/users/votes?billId={test_bill['id']}",
        headers=user_headers,
    )
    assert_status_code(response, 204)

    if test_error:
        raise Exception(test_error)


async def test_get_votes_for_bill(test_manager: TestManager):
    user, user_headers = await test_manager.start_user_session()
    test_bill = await test_manager.create_bill()

    # Create a vote
    vote_data = {
        "billId": test_bill["id"],
        "voteChoiceId": YEA_VOTE_ID,
    }
    response = await test_manager.client.put("/users/votes", json=vote_data, headers=user_headers)
    assert_status_code(response, 200)
    test_user_vote = response.json()

    test_error = None
    try:
        # Get votes for bill
        response = await test_manager.client.get(
            f"/users/admin/{user['id']}/votes/?bill_id={test_bill['id']}",
            headers=test_manager.headers,
        )
        assert_status_code(response, 200)
        votes = response.json()
        assert len(votes) > 0
        assert votes[0]["billId"] == test_user_vote["billId"]
    except Exception as e:
        test_error = str(e)
        logging.error(f"Test failed with {test_error}, marking and cleaning up")

    # Cleanup
    response = await test_manager.client.delete(
        f"/users/votes?billId={test_bill['id']}",
        headers=user_headers,
    )
    assert_status_code(response, 204)

    if test_error:
        raise Exception(test_error)


async def test_get_votes_unauthorized(test_manager: TestManager):
    response = await test_manager.client.get("/users/votes")
    assert_status_code(response, 403)


async def test_get_votes_for_other_user(test_manager: TestManager):
    _, user_headers = await test_manager.start_user_session()
    response = await test_manager.client.get("/users/admin/9999/votes", headers=user_headers)
    assert_status_code(response, 403)
