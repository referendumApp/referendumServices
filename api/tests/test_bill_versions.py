from api.tests.test_utils import assert_status_code


async def test_get_bill_text_success(client, system_headers, test_bill_version):
    response = await client.get(
        f"/bills/{test_bill_version['billId']}/bill_versions", headers=system_headers
    )
    assert_status_code(response, 200)
    bill_versions = response.json()
    assert len(bill_versions) == 1
    assert bill_versions[0]["id"] == test_bill_version["id"]

    response = await client.get(
        f"/bill_versions/{test_bill_version['id']}/text", headers=system_headers
    )
    assert_status_code(response, 200)
    body = response.json()
    assert body["text"] == "12345"
