from api.tests.conftest import TestManager


async def test_add_remove_bill_action(test_manager: TestManager):
    bill_action = await test_manager.create_bill_action()
    assert "id" in bill_action
