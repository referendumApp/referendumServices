from api.tests.test_utils import *  # Import everything to initialize all fixtures


def test_add_remove_bill_action(test_bill_action):
    assert "id" in test_bill_action
