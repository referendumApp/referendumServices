from api.tests.test_utils import *  # Import everything to initialize all fixtures


def test_add_bill_success(test_bill):
    assert "id" in test_bill


def test_list_bills(test_bill):
    response = client.get("/bills", headers=system_headers)
    assert_status_code(response, 200)
    bills = response.json()
    assert len(bills) > 0


def test_add_bill_already_exists(test_bill):
    bill_data = {**test_bill}
    bill_data.pop("id")
    response = client.post("/bills", json=bill_data, headers=system_headers)
    assert_status_code(response, 409)
    assert "bill already exists" in response.json()["detail"]


def test_add_bill_unauthorized(test_bill):
    bill_data = {**test_bill}
    bill_data.pop("id")
    response = client.post(
        "/bills",
        json=bill_data,
        headers={"Authorization": "Bearer user_token"},
    )
    assert_status_code(response, 403)


def test_update_bill(test_bill):
    updated_data = {**test_bill, "title": "Updated Bill Title"}
    response = client.put("/bills", json=updated_data, headers=system_headers)
    assert_status_code(response, 200)
    updated_bill = response.json()
    assert updated_bill["title"] == "Updated Bill Title"


def test_update_bill_not_found():
    non_existent_bill = {
        "id": 9999,
        "legiscan_id": 0,
        "identifier": "DNE.1",
        "title": "Non-existent Bill",
        "description": "This bill does not exist",
        "state_id": 1,
        "legislative_body_id": 1,
        "session_id": 118,
        "briefing": "yadayadayada",
        "status_id": 1,
        "status_date": "2024-01-01",
    }
    response = client.put("/bills", json=non_existent_bill, headers=system_headers)
    assert_status_code(response, 404)
    assert "bill not found" in response.json()["detail"]


def test_update_bill_unauthorized(test_bill):
    updated_data = {**test_bill, "title": "Updated Test Bill"}
    response = client.put(
        "/bills", json=updated_data, headers={"Authorization": "Bearer user_token"}
    )
    assert_status_code(response, 403)


def test_get_bill_success(test_bill):
    response = client.get(f"/bills/{test_bill['id']}", headers=system_headers)
    assert_status_code(response, 200)
    retrieved_bill = response.json()
    assert retrieved_bill["id"] == test_bill["id"]
    assert retrieved_bill["title"] == test_bill["title"]


def test_get_bill_not_found():
    response = client.get("/bills/9999", headers=system_headers)
    assert_status_code(response, 404)
    assert "bill not found" in response.json()["detail"]


def test_delete_bill_success(test_bill):
    response = client.delete(f"/bills/{test_bill['id']}", headers=system_headers)
    assert_status_code(response, 204)


def test_delete_bill_not_found():
    response = client.delete("/bills/9999", headers=system_headers)
    assert_status_code(response, 404)
    assert "bill not found" in response.json()["detail"]


def test_delete_bill_unauthorized(test_bill):
    response = client.delete(
        f"/bills/{test_bill['id']}", headers={"Authorization": "Bearer user_token"}
    )
    assert_status_code(response, 403)


def test_get_bill_text_success(test_bill):
    response = client.get(f"/bills/{test_bill['id']}/text", headers=system_headers)
    assert_status_code(response, 200)
    bill_text = response.json()
    assert "bill_id" in bill_text
    assert "text" in bill_text
    assert bill_text["text"] == "Lorem ipsum dolor sit amet"


def test_add_remove_bill_topic(test_bill, test_topic):
    # Add topic to bill
    response = client.post(
        f"/bills/{test_bill['id']}/topics/{test_topic['id']}", headers=system_headers
    )
    assert_status_code(response, 204)

    # Check that it exists
    response = client.get(f"/bills/{test_bill['id']}", headers=system_headers)
    assert_status_code(response, 200)
    topics = response.json()["topics"]
    assert len(topics) == 1
    assert topics[0]["id"] == test_topic["id"]

    # Remove topic from bill
    response = client.delete(
        f"/bills/{test_bill['id']}/topics/{test_topic['id']}", headers=system_headers
    )
    assert_status_code(response, 204)

    # Check that it's gone
    response = client.get(f"/bills/{test_bill['id']}", headers=system_headers)
    assert_status_code(response, 200)
    topics = response.json()["topics"]
    assert len(topics) == 0
