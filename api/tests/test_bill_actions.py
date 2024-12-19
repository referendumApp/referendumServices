from api.tests.conftest import TestManager


async def test_add_remove_bill_action(test_manager: TestManager):
    test_bill_action = await test_manager.create_bill_action()
    assert "id" in test_bill_action
