from api.tests.test_utils import client, assert_status_code, system_headers
import random


def get_test_bill_payload():
    return {
        "legiscan_id": random.randint(100000, 999999),
        "identifier": "H.B.1",
        "title": "Test Bill",
        "description": "This is a test bill",
        "state": "CA",
        "body": "House",
        "session": "118",
        "briefing": "yadayadayada",
        "status": "killed",
        "latest_action": "none",
    }


# Helper function to create a test bill
def create_test_bill():
    response = client.put(
        "/bills", json=get_test_bill_payload(), headers=system_headers
    )
    return response.json()


def test_add_bill_success():
    response = client.put(
        "/bills", json=get_test_bill_payload(), headers=system_headers
    )
    assert_status_code(response, 200)
    created_bill = response.json()
    assert "id" in created_bill


def test_add_bill_already_exists():
    bill_data = create_test_bill()
    response = client.put("/bills", json=bill_data, headers=system_headers)
    assert_status_code(response, 409)
    assert "Bill already exists" in response.json()["detail"]


def test_add_bill_unauthorized():
    response = client.put(
        "/bills",
        json=get_test_bill_payload(),
        headers={"Authorization": "Bearer user_token"},
    )
    assert_status_code(response, 403)


def test_update_bill_success():
    bill = create_test_bill()
    updated_data = {**bill, "title": "Updated Test Bill"}
    response = client.post("/bills", json=updated_data, headers=system_headers)
    assert_status_code(response, 200)
    updated_bill = response.json()
    assert updated_bill["title"] == "Updated Test Bill"


def test_update_bill_not_found():
    non_existent_bill = {
        "id": 9999,
        "legiscan_id": 0,
        "identifier": "DNE.1",
        "title": "Non-existent Bill",
        "description": "This bill does not exist",
        "state": "CA",
        "body": "House",
        "session": "118",
        "briefing": "yadayadayada",
        "status": "killed",
        "latest_action": "none",
    }
    response = client.post("/bills", json=non_existent_bill, headers=system_headers)
    assert_status_code(response, 404)
    assert "Bill not found" in response.json()["detail"]


def test_update_bill_unauthorized():
    bill = create_test_bill()
    updated_data = {**bill, "title": "Updated Test Bill"}
    response = client.post(
        "/bills", json=updated_data, headers={"Authorization": "Bearer user_token"}
    )
    assert_status_code(response, 403)


def test_get_bill_success():
    bill = create_test_bill()
    response = client.get(f"/bills/{bill['id']}", headers=system_headers)
    assert_status_code(response, 200)
    retrieved_bill = response.json()
    assert retrieved_bill["id"] == bill["id"]
    assert retrieved_bill["title"] == bill["title"]


def test_get_bill_not_found():
    response = client.get("/bills/9999", headers=system_headers)
    assert_status_code(response, 404)
    assert "Bill not found" in response.json()["detail"]


def test_delete_bill_success():
    bill = create_test_bill()
    response = client.delete(f"/bills/{bill['id']}", headers=system_headers)
    assert_status_code(response, 200)


def test_delete_bill_not_found():
    response = client.delete("/bills/9999", headers=system_headers)
    assert_status_code(response, 404)
    assert "Bill not found" in response.json()["detail"]


def test_delete_bill_unauthorized():
    bill = create_test_bill()
    response = client.delete(
        f"/bills/{bill['id']}", headers={"Authorization": "Bearer user_token"}
    )
    assert_status_code(response, 403)


def test_get_bill_text_success():
    bill = create_test_bill()
    response = client.get(f"/bills/{bill['id']}/text", headers=system_headers)
    assert_status_code(response, 200)
    bill_text = response.json()
    assert "bill_id" in bill_text
    assert "text" in bill_text
    assert bill_text["text"] == "Lorem ipsum dolor sit amet"
