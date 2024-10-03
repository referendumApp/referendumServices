from api.tests.common import client, headers


def test_user_workflow():
    # Step 1: Add a new user
    user_payload = {"name": "John Smith", "email": "js@yahoo.com", "password": "1234"}
    response = client.post("/users", json=user_payload, headers=headers)
    assert response.status_code == 200

    # Verify user creation by checking for correct email in the POST response
    created_user = response.json()
    assert created_user["email"] == "js@yahoo.com"

    # Step 2: Get the user by the newly created user ID
    user_id = created_user["id"]
    get_response = client.get(f"/users/{user_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "John Smith"
    assert get_response.json()["email"] == "js@yahoo.com"

    # Step 3: Update the user (change the name)                 ### revisit ###
    user_payload["name"] = "Bob Jones"
    update = client.put("/users", json=user_payload, headers=headers)
    assert update.status_code == 200

    # Step 4: Get the user again after the update to verify the changes
    get_response_after_update = client.get(f"/users/{user_id}", headers=headers)
    assert get_response_after_update.status_code == 200
    assert get_response_after_update.json()["name"] == "Bob Jones"
    assert get_response_after_update.json()["email"] == "js@yahoo.com"

    # Step 5: Delete the user
    delete_response = client.delete(f"/users/{user_id}", headers=headers)
    assert delete_response.status_code == 200  # Assuming successful deletion returns 200

    # Step 6: Attempt to get the user again to verify they've been deleted
    get_response_after_delete = client.get(f"/users/{user_id}", headers=headers)
    assert get_response_after_delete.status_code == 404

    # Step 7: Try to get a non-existent user
    non_existent_user_id = 99999
    get_non_existent = client.get(f"/users/{non_existent_user_id}", headers=headers)
    assert get_non_existent.status_code == 404
