import pytest
from api.tests.test_utils import assert_status_code


@pytest.mark.asyncio
async def test_replies(client, test_user_session, test_bill):
    user, user_headers = test_user_session

    # Create a parent comment
    parent_comment_data = {
        "user_id": user["id"],
        "bill_id": test_bill["id"],
        "parent_id": None,
        "comment": "This is a parent comment.",
    }
    response = await client.post("/comments/", json=parent_comment_data, headers=user_headers)
    assert_status_code(response, 201)
    parent_comment = response.json()
    assert parent_comment["comment"] == parent_comment_data["comment"]
    assert parent_comment["parentId"] is None

    # Create a child comment
    child_comment_data = {
        "user_id": user["id"],
        "bill_id": test_bill["id"],
        "parent_id": parent_comment["id"],
        "comment": "This is a child comment.",
    }
    response = await client.post("/comments/", json=child_comment_data, headers=user_headers)
    assert_status_code(response, 201)
    child_comment = response.json()
    assert child_comment["comment"] == child_comment_data["comment"]
    assert child_comment["parentId"] == parent_comment["id"]

    # Verify both comments were added
    response = await client.get(f"/comments/{parent_comment['id']}", headers=user_headers)
    assert_status_code(response, 200)
    retrieved_parent = response.json()
    assert retrieved_parent["id"] == parent_comment["id"]
    assert retrieved_parent["comment"] == parent_comment_data["comment"]

    response = await client.get(f"/comments/{child_comment['id']}", headers=user_headers)
    assert_status_code(response, 200)
    retrieved_child = response.json()
    assert retrieved_child["id"] == child_comment["id"]
    assert retrieved_child["parentId"] == parent_comment["id"]
    assert retrieved_child["comment"] == child_comment_data["comment"]

    # Attempt to remove the parent comment
    response = await client.delete(f"/comments/{parent_comment['id']}", headers=user_headers)
    assert_status_code(response, 403)

    # Remove the child comment
    response = await client.delete(f"/comments/{child_comment['id']}", headers=user_headers)
    assert_status_code(response, 204)

    # Remove the parent comment
    response = await client.delete(f"/comments/{parent_comment['id']}", headers=user_headers)
    assert_status_code(response, 204)

    # Verify both comments were removed
    response = await client.get(f"/comments/{child_comment['id']}", headers=user_headers)
    assert_status_code(response, 404)

    response = await client.get(f"/comments/{parent_comment['id']}", headers=user_headers)
    assert_status_code(response, 404)


@pytest.mark.asyncio
async def test_delete_with_likes(client, test_user_session, test_bill):
    user, user_headers = test_user_session

    # Create a comment
    comment_data = {
        "user_id": user["id"],
        "bill_id": test_bill["id"],
        "parent_id": None,
        "comment": "This is a parent comment.",
    }
    response = await client.post("/comments/", json=comment_data, headers=user_headers)
    assert_status_code(response, 201)
    comment_id = response.json()["id"]

    # Like the comment
    response = await client.post(f"/comments/{comment_id}/like", headers=user_headers)
    assert_status_code(response, 204)

    # Delete the comment with likes
    response = await client.delete(f"/comments/{comment_id}", headers=user_headers)
    assert_status_code(response, 204)
