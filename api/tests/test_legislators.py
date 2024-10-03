from api.tests.common import client, headers


def test_legislator_workflow():

    # Step 1: Add a new bill
    original_legislator_payload = {
        "chamber": "str",
        "district": "str",
        "email": "str",
        "facebook": "str",
        "image_url": "str",
        "instagram": "str",
        "name": "str",
        "office": "str",
        "party": "str",
        "phone": "str",
        "state": "WA",
        "twitter": "str",
    }
    response = client.put("/legislators", json=original_legislator_payload, headers=headers)
    assert response.status_code == 200

    # Verify legislator creation by checking for correct state in the PUT response
    created_legislator = response.json()
    assert created_legislator["state"] == "WA"

    # Step 2: Get the legislator by the newly created legislator id
    legislator_id = created_legislator["id"]
    get_response = client.get(f"/legislators/{legislator_id}", headers=headers)
    assert get_response.status_code == 200
    assert created_legislator["state"] == "WA"

    # Step 3: Update the legislator (change the chamber)
    created_legislator["chamber"] = "senate"
    update_response = client.post("/legislators", json=created_legislator, headers=headers)
    assert update_response.status_code == 200

    # Step 4: Get the legislator again after the update to verify the changes
    get_response_after_update = client.get(f"/legislators/{legislator_id}", headers=headers)
    assert get_response_after_update.status_code == 200
    assert get_response_after_update.json()["chamber"] == "senate"

    # Step 5: Delete the legislator
    delete_response = client.delete(f"/legislators/{legislator_id}", headers=headers)
    assert delete_response.status_code == 200  # Assuming successful deletion returns 200

    # Step 6: Attempt to get the bill again to verify it's been deleted
    get_response_after_delete = client.get(f"/legislators/{legislator_id}", headers=headers)
    assert get_response_after_delete.status_code == 404

    # Step 7: Try to get a non-existent bill
    non_existent_legislator_id = 99999
    get_non_existent = client.get(f"/legislators/{non_existent_legislator_id}", headers=headers)
    assert get_non_existent.status_code == 404
