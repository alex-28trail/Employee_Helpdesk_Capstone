"""Core ticket tests required by the assessment: creation, invalid input, status update.
These call Member A's endpoints as defined in the shared API contract."""


def test_create_ticket_returns_201(client, requester_id):
    response = client.post("/api/tickets", json={
        "title": "File share down for Finance",
        "description": "Nobody in Finance can open the S: drive since 9am.",
        "requester_id": requester_id,
        "category": "Network",
    })
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "New"
    assert body["category"] == "Network"


def test_missing_required_fields_returns_422_with_field_names(client, requester_id):
    response = client.post("/api/tickets", json={"requester_id": requester_id})
    assert response.status_code == 422
    missing = {err["loc"][-1] for err in response.json()["detail"]}
    assert {"title", "description"} <= missing


def test_invalid_category_returns_422(client, requester_id):
    response = client.post("/api/tickets", json={
        "title": "x" * 5, "description": "y" * 20, "requester_id": requester_id, "category": "Coffee",
    })
    assert response.status_code == 422


def test_valid_status_transition(client, ticket_id):
    response = client.patch(f"/api/tickets/{ticket_id}/status", json={"status": "In Progress"})
    assert response.status_code == 200
    assert response.json()["status"] == "In Progress"


def test_invalid_status_transition_returns_409(client, ticket_id):
    response = client.patch(f"/api/tickets/{ticket_id}/status", json={"status": "Resolved"})  # New -> Resolved
    assert response.status_code == 409
