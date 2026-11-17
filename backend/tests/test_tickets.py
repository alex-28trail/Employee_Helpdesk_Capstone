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


def test_full_lifecycle_with_reopen_and_history(client, ticket_id):
    for status in ("In Progress", "Resolved", "In Progress"):
        assert client.patch(f"/api/tickets/{ticket_id}/status", json={"status": status}).status_code == 200
    history = client.get(f"/api/tickets/{ticket_id}/history").json()
    changes = [(h["old_status"], h["new_status"]) for h in history if h["activity_type"] == "status_change"]
    assert changes == [("New", "In Progress"), ("In Progress", "Resolved"), ("Resolved", "In Progress")]
    assert history[0]["activity_type"] == "created"


def test_status_cannot_be_changed_through_ticket_update(client, ticket_id):
    response = client.patch(f"/api/tickets/{ticket_id}", json={"status": "Resolved"})
    assert response.status_code == 422
    assert client.get(f"/api/tickets/{ticket_id}").json()["status"] == "New"


def test_priority_update_is_recorded_in_history(client, ticket_id):
    response = client.patch(f"/api/tickets/{ticket_id}", json={"priority": "High"})
    assert response.status_code == 200 and response.json()["priority"] == "High"
    history = client.get(f"/api/tickets/{ticket_id}/history").json()
    assert any("priority Medium -> High" in h["description"] for h in history)


def test_comment_is_visible_in_history(client, ticket_id):
    response = client.post(f"/api/tickets/{ticket_id}/comments", json={"comment": "Replacing batteries now."})
    assert response.status_code == 201
    history = client.get(f"/api/tickets/{ticket_id}/history").json()
    assert history[-1]["activity_type"] == "comment"
    assert history[-1]["description"] == "Replacing batteries now."


def test_missing_ticket_is_404_with_message(client):
    response = client.get("/api/tickets/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Ticket 9999 not found"


def test_list_filters_and_requester_details(client, ticket_id, requester_id):
    rows = client.get("/api/tickets", params={"status": "New", "requester_id": requester_id}).json()
    assert [r["id"] for r in rows] == [ticket_id]
    assert rows[0]["requester"]["name"] == "Asha Kumar"
    assert client.get("/api/tickets", params={"status": "Resolved"}).json() == []
    assert client.get("/api/tickets", params={"priority": "Urgent"}).status_code == 422


def test_dashboard_summary_counts(client, ticket_id):
    client.patch(f"/api/tickets/{ticket_id}/status", json={"status": "In Progress"})
    body = client.get("/api/dashboard/summary").json()
    assert body["total"] == 1
    assert body["by_status"] == {"New": 0, "In Progress": 1, "Resolved": 0}
    assert body["by_priority"]["Medium"] == 1


def test_unknown_requester_is_422(client):
    response = client.post("/api/tickets", json={
        "title": "Monitor flicker", "description": "Screen flickers every few seconds.", "requester_id": 999,
    })
    assert response.status_code == 422
