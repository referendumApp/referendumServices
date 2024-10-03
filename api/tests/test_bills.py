from api.tests.common import client, system_headers


def test_bill_workflow():
    # Step 1: Add a new bill
    original_bill_payload = {
        "legiscan_id": 11,
        "identifier": "str",
        "title": "str",
        "description": "str",
        "state": "str",
        "body": "str",
        "session": "str",
        "briefing": "str",
        "status": "str",
        "latestAction": "str",
    }
    response = client.put("/bills", json=original_bill_payload, headers=system_headers)
    assert response.status_code == 200

    # Verify bill creation by checking for correct legiscanID in the PUT response
    created_bill = response.json()
    assert created_bill["legiscan_id"] == 11

    # Step 2: Get the bill by the newly created bill ID
    bill_id = created_bill["id"]
    get_response = client.get(f"/bills/{bill_id}", headers=system_headers)
    assert get_response.status_code == 200
    assert created_bill["legiscan_id"] == 11

    # Step 3: Update the bill (change the title)
    created_bill["title"] = "new title"
    update_response = client.post("/bills", json=created_bill, headers=system_headers)
    assert update_response.status_code == 200

    # Step 4: Get the bill again after the update to verify the changes
    get_response_after_update = client.get(f"/bills/{bill_id}", headers=system_headers)
    assert get_response_after_update.status_code == 200
    assert get_response_after_update.json()["title"] == "new title"

    # Step 5: Delete the bill
    delete_response = client.delete(f"/bills/{bill_id}", headers=system_headers)
    assert delete_response.status_code == 200  # Assuming successful deletion returns 200

    # Step 6: Attempt to get the bill again to verify it's been deleted
    get_response_after_delete = client.get(f"/bills/{bill_id}", headers=system_headers)
    assert get_response_after_delete.status_code == 404

    # Step 7: Try to get a non-existent bill
    non_existent_bill_id = 99999
    get_non_existent = client.get(f"/bills/{non_existent_bill_id}", headers=system_headers)
    assert get_non_existent.status_code == 404
