from api.tests.test_utils import assert_status_code


async def test_get_bill_text_success(client, system_headers, test_bill_version):
    response = await client.get(f"/bills/{test_bill_version['billId']}", headers=system_headers)
    assert_status_code(response, 200)
    bill = response.json()
    assert bill["currentVersionId"] == test_bill_version["id"]

    response = await client.get(
        f"/bill_versions/{test_bill_version['id']}/text", headers=system_headers
    )
    assert_status_code(response, 200)
    body = response.json()
    assert body["text"] == "A BILL"
