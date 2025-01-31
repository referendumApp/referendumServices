import logging

from api.tests.conftest import TestManager
from api.tests.test_utils import assert_status_code


async def test_list_executive_order_details(client, system_headers, test_manager: TestManager):
    test_president = await test_manager.create_president()
    test_executive_order = await test_manager.create_executive_order(
        president_id=test_president["id"]
    )
    print(test_executive_order)

    test_error = None
    try:
        response = await client.post("/executive_orders/details", headers=system_headers, json={})
        assert_status_code(response, 200)
        eo_data = response.json()
        assert eo_data["hasMore"] == False
        assert len(eo_data["items"]) == 1
        eo = eo_data["items"][0]

        expected_fields = [
            "executiveOrderId",
            "briefing",
            "signedDate",
            "hash",
            "presidentId",
            "title",
            "url",
        ]
        print(eo)
        print(expected_fields)
        print([field in eo for field in expected_fields])
        assert all(field in eo for field in expected_fields)
    except Exception as e:
        test_error = str(e)
        logging.error(f"Test failed with {test_error}, marking and cleaning up")

    if test_error:
        raise Exception(test_error)
