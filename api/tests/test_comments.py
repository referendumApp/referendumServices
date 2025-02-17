from api.tests.conftest import TestManager
from api.tests.test_utils import assert_status_code
from datetime import datetime


async def test_comment_workflow(test_manager: TestManager):
    user, user_headers = await test_manager.start_user_session()
    test_bill = await test_manager.create_bill()

    # Create a parent comment
    parent_comment_data = {
        "userId": user["id"],
        "billId": test_bill["id"],
        "parentId": None,
        "comment": "This is a parent comment.",
    }
    response = await test_manager.client.post(
        "/comments/", json=parent_comment_data, headers=user_headers
    )
    assert_status_code(response, 201)
    parent_comment = response.json()
    assert parent_comment["comment"] == parent_comment_data["comment"]
    assert parent_comment["parentId"] is None

    # Create a child comment
    child_comment_data = {
        "userId": user["id"],
        "billId": test_bill["id"],
        "parentId": parent_comment["id"],
        "comment": "This is a child comment.",
    }
    response = await test_manager.client.post(
        "/comments/", json=child_comment_data, headers=user_headers
    )
    assert_status_code(response, 201)
    child_comment = response.json()
    assert child_comment["comment"] == child_comment_data["comment"]
    assert child_comment["parentId"] == parent_comment["id"]

    # Update parent comment and verify updated_at is set
    update_data = {**parent_comment, "comment": "Updated parent comment"}
    response = await test_manager.client.put(f"/comments", json=update_data, headers=user_headers)
    assert_status_code(response, 200)
    updated_comment = response.json()
    assert updated_comment["comment"] == update_data["comment"]
    assert updated_comment["createdAt"] == parent_comment["createdAt"]
    assert updated_comment["updatedAt"] is not None
    assert isinstance(datetime.fromisoformat(updated_comment["updatedAt"]), datetime)

    # Verify both comments were added to the bill
    response = await test_manager.client.get(
        f"/bills/{test_bill['id']}/comments", headers=user_headers
    )
    assert_status_code(response, 200)
    comment_list = response.json()

    assert len(comment_list) == 2
    parent_result = next((c for c in comment_list if c["id"] == parent_comment["id"]), None)
    assert parent_result is not None, "Parent comment not found in response"
    child_result = next((c for c in comment_list if c["id"] == child_comment["id"]), None)
    assert child_result is not None, "Child comment not found in response"
    assert child_result["parentId"] == parent_comment["id"]

    # Verify these comments appear in the feed
    response = await test_manager.client.get(f"/users/feed", headers=user_headers)
    assert_status_code(response, 200)
    assert len(response.json()) == 4  # Include header & pinned bill

    # Attempt to remove the parent comment
    response = await test_manager.client.delete(
        f"/comments/{parent_comment['id']}", headers=user_headers
    )
    assert_status_code(response, 403)

    # Remove the child comment
    response = await test_manager.client.delete(
        f"/comments/{child_comment['id']}", headers=user_headers
    )
    assert_status_code(response, 204)

    # Remove the parent comment
    response = await test_manager.client.delete(
        f"/comments/{parent_comment['id']}", headers=user_headers
    )
    assert_status_code(response, 204)

    # Verify both comments were removed
    response = await test_manager.client.get(
        f"/comments/{child_comment['id']}", headers=user_headers
    )
    assert_status_code(response, 404)

    response = await test_manager.client.get(
        f"/comments/{parent_comment['id']}", headers=user_headers
    )
    assert_status_code(response, 404)


async def test_delete_with_likes(test_manager: TestManager):
    user, user_headers = await test_manager.start_user_session()
    test_bill = await test_manager.create_bill()

    # Create a comment
    comment_data = {
        "userId": user["id"],
        "billId": test_bill["id"],
        "parentId": None,
        "comment": "This is a parent comment.",
    }
    response = await test_manager.client.post("/comments/", json=comment_data, headers=user_headers)
    assert_status_code(response, 201)
    comment_id = response.json()["id"]

    # Endorse the comment
    response = await test_manager.client.post(
        f"/comments/{comment_id}/endorsement", headers=user_headers
    )
    assert_status_code(response, 204)

    # Check that the endorsement shows up in the feed
    response = await test_manager.client.get(f"/users/feed", headers=user_headers)
    comments = [item["content"] for item in response.json() if (item["type"] == "comment")]
    assert comments[0]["endorsements"] > 0
    assert comments[0]["currentUserHasEndorsed"] == True

    # Delete the comment with likes
    response = await test_manager.client.delete(f"/comments/{comment_id}", headers=user_headers)
    assert_status_code(response, 204)
