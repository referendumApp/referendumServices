from api.tests.test_utils import assert_status_code


def test_add_remove_legislator_workflow(client, system_headers, test_committee, test_legislator):
    # Add the legislator
    response = client.post(
        f"/committees/{test_committee['id']}/legislators/{test_legislator['id']}",
        headers=system_headers,
    )
    assert_status_code(response, 204)

    # Check for membership
    response = client.get(
        f"/committees/{test_committee['id']}/legislators", headers=system_headers
    )
    assert_status_code(response, 200)
    legislators = response.json()
    assert len(legislators) == 1
    assert legislators[0]["id"] == test_legislator["id"]

    # Then, remove the legislator
    response = client.delete(
        f"/committees/{test_committee['id']}/legislators/{test_legislator['id']}",
        headers=system_headers,
    )
    assert_status_code(response, 204)

    # Check for removal
    response = client.get(
        f"/committees/{test_committee['id']}/legislators", headers=system_headers
    )
    assert_status_code(response, 200)
    legislators = response.json()
    assert len(legislators) == 0
