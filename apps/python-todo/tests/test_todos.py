from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_create_and_list_todos() -> None:
    response = client.post("/todos/", json={"title": "Write unit tests"})
    assert response.status_code == 201

    listing = client.get("/todos/")
    assert listing.status_code == 200
    payload = listing.json()
    assert any(item["title"] == "Write unit tests" for item in payload)


def test_update_and_delete_todo() -> None:
    response = client.post("/todos/", json={"title": "Refactor code"})
    todo_id = response.json()["id"]

    update = client.patch(f"/todos/{todo_id}", json={"completed": True})
    assert update.status_code == 200
    assert update.json()["completed"] is True

    delete_resp = client.delete(f"/todos/{todo_id}")
    assert delete_resp.status_code == 204

    missing = client.patch(f"/todos/{todo_id}", json={"completed": False})
    assert missing.status_code == 404
