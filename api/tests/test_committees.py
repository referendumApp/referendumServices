from api.tests.conftest import TestManager
from api.tests.test_utils import assert_status_code


async def test_add_remove_legislator_workflow(test_manager: TestManager):
    test_legislator = await test_manager.create_legislator()
    test_committee = await test_manager.create_committee()

    # Add the legislator
    response = await test_manager.client.post(
        f"/committees/{test_committee['id']}/legislators/{test_legislator['id']}",
        headers=test_manager.headers,
    )
    assert_status_code(response, 204)

    # Check for membership
    response = await test_manager.client.get(
        f"/committees/{test_committee['id']}/legislators", headers=test_manager.headers
    )
    assert_status_code(response, 200)
    legislators = response.json()
    assert len(legislators) == 1
    assert legislators[0]["id"] == test_legislator["id"]

    # Then, remove the legislator
    response = await test_manager.client.delete(
        f"/committees/{test_committee['id']}/legislators/{test_legislator['id']}",
        headers=test_manager.headers,
    )
    assert_status_code(response, 204)

    # Check for removal
    response = await test_manager.client.get(
        f"/committees/{test_committee['id']}/legislators", headers=test_manager.headers
    )
    assert_status_code(response, 200)
    legislators = response.json()
    assert len(legislators) == 0
