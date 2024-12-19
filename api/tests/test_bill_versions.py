from api.tests.conftest import TestManager
from api.tests.test_utils import assert_status_code


async def test_get_bill_text_success(test_manager: TestManager, system_headers):
    test_bill_version = await test_manager.create_bill_version()
    test_bill = await test_manager.get_bill(test_bill_version["billId"])

    assert test_bill["currentVersionId"] == test_bill_version["id"]

    response = await test_manager.client.get(
        f"/bill_versions/{test_bill_version['id']}/text", headers=system_headers
    )
    assert_status_code(response, 200)
    body = response.json()
    assert body["text"] == "A BILL"


async def test_get_bill_briefing_success(test_manager: TestManager, system_headers):
    test_bill_version = await test_manager.create_bill_version()
    response = await test_manager.client.get(
        f"/bill_versions/{test_bill_version['id']}/briefing", headers=system_headers
    )
    assert_status_code(response, 200)
    body = response.json()
    assert body["briefing"] == "yadayadayada"
