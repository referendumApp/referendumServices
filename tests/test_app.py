from fastapi.testclient import TestClient
from api import app

client = TestClient(app)


def test_get_bills():
    response = client.get("/bills")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4


def test_get_bill_text():
    response = client.get("/bills/123/text")
    assert response.status_code == 200
    data = response.json()
    assert "bill_id" in data
    assert "text" in data
    assert data["bill_id"] == "123"
    assert "ipsum" in data["text"]


def test_get_legislators():
    response = client.get("/legislators")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 102


def test_get_legislator_vote_events():
    response = client.get("/legislator-vote-events")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_get_legislator_votes():
    response = client.get("/legislator-votes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 100


def test_get_user_votes():
    user_id = "user123"
    response = client.get(f"/user-votes?user_id={user_id}")
    data = response.json()
    assert len(data) == 0


def test_get_comments():
    response = client.get("/comments")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
