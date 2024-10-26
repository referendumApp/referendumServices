import pytest
from api.tests.test_utils import assert_status_code


@pytest.mark.asyncio
async def test_add_bill_success(test_bill):
    assert "id" in test_bill


@pytest.mark.asyncio
async def test_list_bills(test_get_bills):
    assert len(test_get_bills) > 0


@pytest.mark.asyncio
async def test_add_bill_already_exists(client, system_headers, test_bill):
    bill_data = {**test_bill}
    bill_data.pop("id")
    response = await client.post("/bills", json=bill_data, headers=system_headers)
    assert_status_code(response, 409)
    assert "bill already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_add_bill_unauthorized(client, test_bill):
    bill_data = {**test_bill}
    bill_data.pop("id")
    response = await client.post(
        "/bills",
        json=bill_data,
        headers={"Authorization": "Bearer user_token"},
    )
    assert_status_code(response, 403)


@pytest.mark.asyncio
async def test_update_bill(client, system_headers, test_bill):
    updated_data = {**test_bill, "title": "Updated Bill Title"}
    response = await client.put("/bills", json=updated_data, headers=system_headers)
    assert_status_code(response, 200)
    updated_bill = response.json()
    assert updated_bill["title"] == "Updated Bill Title"


@pytest.mark.asyncio
async def test_update_bill_not_found(client, system_headers):
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
    response = await client.put("/bills", json=non_existent_bill, headers=system_headers)
    assert_status_code(response, 404)
    assert "bill not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_bill_unauthorized(client, test_bill):
    updated_data = {**test_bill, "title": "Updated Test Bill"}
    response = await client.put(
        "/bills", json=updated_data, headers={"Authorization": "Bearer user_token"}
    )
    assert_status_code(response, 403)


@pytest.mark.asyncio
async def test_get_bill_success(client, system_headers, test_bill):
    response = await client.get(f"/bills/{test_bill['id']}", headers=system_headers)
    assert_status_code(response, 200)
    retrieved_bill = response.json()
    assert retrieved_bill["id"] == test_bill["id"]
    assert retrieved_bill["title"] == test_bill["title"]


@pytest.mark.asyncio
async def test_get_bill_not_found(client, system_headers):
    response = await client.get("/bills/9999", headers=system_headers)
    assert_status_code(response, 404)
    assert "bill not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_bill_success(client, system_headers, test_bill):
    response = await client.delete(f"/bills/{test_bill['id']}", headers=system_headers)
    assert_status_code(response, 204)


@pytest.mark.asyncio
async def test_delete_bill_not_found(client, system_headers):
    response = await client.delete("/bills/9999", headers=system_headers)
    assert_status_code(response, 404)
    assert "bill not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_bill_unauthorized(client, test_bill):
    response = await client.delete(
        f"/bills/{test_bill['id']}", headers={"Authorization": "Bearer user_token"}
    )
    assert_status_code(response, 403)


@pytest.mark.asyncio
async def test_get_bill_text_success(client, system_headers, test_bill):
    response = await client.get(f"/bills/{test_bill['id']}/version/1/text", headers=system_headers)
    assert_status_code(response, 200)
    bill_text = response.json()
    assert "bill_id" in bill_text
    assert "version" in bill_text
    assert "text" in bill_text
    assert bill_text["text"] == "Lorem ipsum dolor sit amet"


@pytest.mark.asyncio
async def test_add_remove_bill_topic(client, system_headers, test_bill, test_topic):
    # Add topic to bill
    response = await client.post(
        f"/bills/{test_bill['id']}/topics/{test_topic['id']}", headers=system_headers
    )
    assert_status_code(response, 204)

    # Check that it exists
    response = await client.get(f"/bills/{test_bill['id']}", headers=system_headers)
    assert_status_code(response, 200)
    topics = response.json()["topics"]
    assert len(topics) == 1
    assert topics[0]["id"] == test_topic["id"]

    # Remove topic from bill
    response = await client.delete(
        f"/bills/{test_bill['id']}/topics/{test_topic['id']}", headers=system_headers
    )
    assert_status_code(response, 204)

    # Check that it's gone
    response = await client.get(f"/bills/{test_bill['id']}", headers=system_headers)
    assert_status_code(response, 200)
    topics = response.json()["topics"]
    assert len(topics) == 0


@pytest.mark.asyncio
async def test_add_remove_bill_sponsor(client, system_headers, test_bill, test_legislator):
    # Add legislator to bill
    response = await client.post(
        f"/bills/{test_bill['id']}/sponsors/{test_legislator['id']}",
        headers=system_headers,
    )
    assert_status_code(response, 204)

    # Check that it exists
    response = await client.get(f"/bills/{test_bill['id']}", headers=system_headers)
    assert_status_code(response, 200)
    sponsors = response.json()["sponsors"]
    assert len(sponsors) == 1
    assert sponsors[0]["id"] == test_legislator["id"]

    # Remove topic from bill
    response = await client.delete(
        f"/bills/{test_bill['id']}/sponsors/{test_legislator['id']}",
        headers=system_headers,
    )
    assert_status_code(response, 204)

    # Check that it's gone
    response = await client.get(f"/bills/{test_bill['id']}", headers=system_headers)
    assert_status_code(response, 200)
    sponsors = response.json()["sponsors"]
    assert len(sponsors) == 0
