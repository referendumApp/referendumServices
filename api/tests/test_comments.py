from api.tests.conftest import TestManager
from api.tests.test_utils import assert_status_code


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

    # Like the comment
    response = await test_manager.client.post(f"/comments/{comment_id}/like", headers=user_headers)
    assert_status_code(response, 204)

    # Delete the comment with likes
    response = await test_manager.client.delete(f"/comments/{comment_id}", headers=user_headers)
    assert_status_code(response, 204)
