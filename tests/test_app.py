from fastapi.testclient import TestClient
from api import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200

def test_user_workflow():
    # Step 1: Add a new user
    user_payload = {
        "name": "John Smith", 
        "email": "js@yahoo.com", 
        "password": "1234"
    }
    response = client.put("/users", json=user_payload)
    assert response.status_code == 200

    # Verify user creation by checking for correct email in the PUT response
    created_user = response.json()
    assert created_user["email"] == "js@yahoo.com"

    # Step 2: Get the user by the newly created user ID
    user_id = created_user["id"]  
    get_response = client.get(f"/users/{user_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "John Smith"
    assert get_response.json()["email"] == "js@yahoo.com"

    # Step 3: Update the user (change the name)                 ### revisit ###
    user_payload["name"] = "Bob Jones"
    update = client.post("/users", json=user_payload)
    assert update.status_code == 200

    # Step 4: Get the user again after the update to verify the changes
    get_response_after_update = client.get(f"/users/{user_id}")
    assert get_response_after_update.status_code == 200
    assert get_response_after_update.json()["name"] == "Bob Jones"
    assert get_response_after_update.json()["email"] == "js@yahoo.com"

    # Step 5: Delete the user
    delete_response = client.delete(f"/users/{user_id}")
    assert delete_response.status_code == 200  # Assuming successful deletion returns 200

    # Step 6: Attempt to get the user again to verify they've been deleted
    get_response_after_delete = client.get(f"/users/{user_id}")
    assert get_response_after_delete.status_code == 404

    # Step 7: Try to get a non-existent user
    non_existent_user_id = 99999
    get_non_existent = client.get(f"/users/{non_existent_user_id}")
    assert get_non_existent.status_code == 404

    # user = response.json()
    # assert user_payload == user


    # TODO error cases
    # docker ps - gives everything running
    # docker stop $(docker ps -aq) - shuts everything down
    # docker rm $(docker ps -aq) - remove everything
    # docker image prune, network prune, system prune - prune a bunch of stuff

def test_bill_workflow():
    # Step 1: Add a new bill
    original_bill_payload = {
    "legiscanID": 11,
    "identifier": "str",
    "title": "str",
    "description": "str",
    "state": "str",
    "body": "str",
    "session": "str",
    "briefing": "str",
    "status": "str",
    "latestAction": "str"
        }
    response = client.put("/bills", json=original_bill_payload)
    assert response.status_code == 200

    # Verify bill creation by checking for correct legiscanID in the PUT response
    created_bill = response.json()
    assert created_bill["legiscanID"] == 11

    # Step 2: Get the bill by the newly created bill ID
    bill_id = created_bill["id"]  
    get_response = client.get(f"/bills/{bill_id}")
    assert get_response.status_code == 200
    assert created_bill["legiscanID"] == 11
   
    # Step 3: Update the bill (change the title)
    created_bill["title"] = "new title"
    update_response = client.post("/bills", json=created_bill)
    assert update_response.status_code == 200

    # Step 4: Get the bill again after the update to verify the changes
    get_response_after_update = client.get(f"/bills/{bill_id}")
    assert get_response_after_update.status_code == 200
    assert get_response_after_update.json()["title"] == "new title"

    # Step 5: Delete the bill
    delete_response = client.delete(f"/bills/{bill_id}")
    assert delete_response.status_code == 200  # Assuming successful deletion returns 200

    # Step 6: Attempt to get the bill again to verify it's been deleted
    get_response_after_delete = client.get(f"/bills/{bill_id}")
    assert get_response_after_delete.status_code == 404

    # Step 7: Try to get a non-existent bill
    non_existent_bill_id = 99999
    get_non_existent = client.get(f"/bills/{non_existent_bill_id}")
    assert get_non_existent.status_code == 404
   


def test_legislator_workflow():
    
    # Step 1: Add a new bill
    original_legislator_payload = {
    "chamber": "str",
    "district": "str",
    "email": "str",
    "facebook": "str",
    "imageUrl": "str",
    "instagram": "str",
    "name": "str",
    "office": "str",
    "party": "str",
    "phone": "str",
    "state": "WA",
    "twitter": "str"
    }
    response = client.put("/legislators", json=original_legislator_payload)
    print(response.json())
    assert response.status_code == 200

    # Verify legislator creation by checking for correct state in the PUT response
    created_legislator = response.json()
    assert created_legislator["state"] == "WA"

    # Step 2: Get the legislator by the newly created legislator id
    legislator_id = created_legislator["id"]  
    get_response = client.get(f"/legislators/{legislator_id}")
    assert get_response.status_code == 200
    assert created_legislator["state"] == "WA"
   
    # Step 3: Update the legislator (change the chamber)
    created_legislator["chamber"] = "senate"
    update_response = client.post("/legislators", json=created_legislator)
    assert update_response.status_code == 200

    # Step 4: Get the legislator again after the update to verify the changes
    get_response_after_update = client.get(f"/legislators/{legislator_id}")
    assert get_response_after_update.status_code == 200
    assert get_response_after_update.json()["chamber"] == "senate"

    # Step 5: Delete the legislator
    delete_response = client.delete(f"/legislators/{legislator_id}")
    assert delete_response.status_code == 200  # Assuming successful deletion returns 200

    # Step 6: Attempt to get the bill again to verify it's been deleted
    get_response_after_delete = client.get(f"/legislators/{legislator_id}")
    print(legislator_id)
    assert get_response_after_delete.status_code == 404

    # Step 7: Try to get a non-existent bill
    non_existent_legislator_id = 99999
    get_non_existent = client.get(f"/legislators/{non_existent_legislator_id}")
    assert get_non_existent.status_code == 404









    