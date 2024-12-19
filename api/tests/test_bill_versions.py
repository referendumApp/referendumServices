from api.tests.conftest import TestManager
from api.tests.test_utils import assert_status_code


async def test_get_bill_text_success(test_manager: TestManager, system_headers):
    bill_version = await test_manager.create_bill_version()
    bill = await test_manager.get_bill(bill_version["billId"])

    assert bill["currentVersionId"] == bill_version["id"]

    response = await test_manager.client.get(
        f"/bill_versions/{bill_version['id']}/text", headers=system_headers
    )
    assert_status_code(response, 200)
    body = response.json()
    assert body["text"] == "A BILL"


async def test_get_bill_briefing_success(test_manager: TestManager, system_headers):
    bill_version = await test_manager.create_bill_version()
    response = await test_manager.client.get(
        f"/bill_versions/{bill_version['id']}/briefing", headers=system_headers
    )
    assert_status_code(response, 200)
    body = response.json()
    assert body["briefing"] == "yadayadayada"
