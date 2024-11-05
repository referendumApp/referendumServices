from api.tests.test_utils import assert_status_code


async def test_bulk_update_success(client, system_headers, test_items):
    # Test successful bulk update
    update_data = [{"id": item["id"], "name": f"Updated {item['name']}"} for item in test_items]
    response = await client.put("/items/bulk", json=update_data, headers=system_headers)
    assert_status_code(response, 200)
    updated_items = response.json()
    for i, item in enumerate(updated_items):
        assert item["name"] == update_data[i]["name"]


async def test_bulk_update_partial_success(client, system_headers, test_items):
    # Test with a mix of valid and invalid IDs
    update_data = [
        {"id": test_items[0]["id"], "name": "Updated Item 1"},
        {"id": 9999, "name": "Non-existent Item"},
    ]
    response = await client.put("/items/bulk", json=update_data, headers=system_headers)
    assert_status_code(response, 200)
    results = response.json()
    assert results[0]["name"] == "Updated Item 1"
    assert "not found" in results[1]["detail"]


async def test_bulk_update_no_permission(client, test_items):
    # Test unauthorized access
    update_data = [{"id": item["id"], "name": f"Updated {item['name']}"} for item in test_items]
    response = await client.put(
        "/items/bulk",
        json=update_data,
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert_status_code(response, 403)
    assert "Forbidden" in response.json()["detail"]


async def test_bulk_update_non_existent_items(client, system_headers):
    # Test with all non-existent IDs
    update_data = [
        {"id": 9999, "name": "Non-existent Item 1"},
        {"id": 8888, "name": "Non-existent Item 2"},
    ]
    response = await client.put("/items/bulk", json=update_data, headers=system_headers)
    assert_status_code(response, 404)
    assert "not found" in response.json()["detail"]


async def test_bulk_update_partial_failure(client, system_headers, test_items):
    # Test with some items missing fields
    update_data = [
        {"id": test_items[0]["id"], "name": "Updated Item 1"},
        {"id": test_items[1]["id"]},  # Missing required fields
    ]
    response = await client.put("/items/bulk", json=update_data, headers=system_headers)
    assert_status_code(response, 400)
    assert "Missing required fields" in response.json()["detail"]
