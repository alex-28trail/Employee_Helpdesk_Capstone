"""API tests for AI analysis, suggestions and feedback (F6, scenarios 01, 03, 04)."""
from app.services.ai_service import AIInvalidOutputError, AITimeoutError, AIUnavailableError


def _confirmed(client, ticket_id):
    body = client.get(f"/api/tickets/{ticket_id}").json()
    return body["category"], body["priority"], body["status"]


def test_analysis_stores_suggestion_without_changing_ticket(client, ticket_id):
    before = _confirmed(client, ticket_id)

    response = client.post(f"/api/tickets/{ticket_id}/ai-analysis")

    assert response.status_code == 201
    body = response.json()
    assert body["suggested_category"] == "Hardware"
    assert body["suggested_priority"] == "Low"
    assert len(body["troubleshooting_steps"]) == 3
    assert body["model_name"] == "fake-model"
    assert body["feedback"] is None
    assert _confirmed(client, ticket_id) == before  # advisory only


def test_suggestions_are_listed_newest_first(client, ticket_id):
    first = client.post(f"/api/tickets/{ticket_id}/ai-analysis").json()["id"]
    second = client.post(f"/api/tickets/{ticket_id}/ai-analysis").json()["id"]

    listed = client.get(f"/api/tickets/{ticket_id}/ai-suggestions").json()
    assert [s["id"] for s in listed] == [second, first]


def test_analysis_for_missing_ticket_is_404(client):
    response = client.post("/api/tickets/99999/ai-analysis")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_model_unavailable_returns_503_and_ticket_is_untouched(client, fake_ai, ticket_id):
    before = _confirmed(client, ticket_id)
    fake_ai.error = AIUnavailableError("The AI service is not reachable. Check the internet connection.")

    response = client.post(f"/api/tickets/{ticket_id}/ai-analysis")

    assert response.status_code == 503
    assert "not reachable" in response.json()["detail"]
    assert _confirmed(client, ticket_id) == before
    assert client.get(f"/api/tickets/{ticket_id}/ai-suggestions").json() == []


def test_timeout_and_bad_output_status_codes(client, fake_ai, ticket_id):
    fake_ai.error = AITimeoutError("timed out")
    assert client.post(f"/api/tickets/{ticket_id}/ai-analysis").status_code == 504
    fake_ai.error = AIInvalidOutputError("bad output")
    assert client.post(f"/api/tickets/{ticket_id}/ai-analysis").status_code == 502


def test_ticket_crud_still_works_while_model_is_down(client, fake_ai, requester_id, ticket_id):
    """Scenario 04: create, list and update succeed when the AI fails."""
    fake_ai.error = AIUnavailableError("down")
    assert client.post(f"/api/tickets/{ticket_id}/ai-analysis").status_code == 503

    created = client.post("/api/tickets", json={
        "title": "VPN disconnects",
        "description": "VPN drops every ten minutes when working from home.",
        "requester_id": requester_id,
    })
    assert created.status_code == 201
    assert client.get("/api/tickets").status_code == 200
    updated = client.patch(f"/api/tickets/{created.json()['id']}", json={"priority": "Medium"})
    assert updated.status_code == 200
    assert client.patch(f"/api/tickets/{ticket_id}/status", json={"status": "In Progress"}).status_code == 200


def test_correction_applies_final_values_and_persists(client, ticket_id):
    """Scenario 03: staff correct the AI; values and feedback are visible after refresh."""
    suggestion_id = client.post(f"/api/tickets/{ticket_id}/ai-analysis").json()["id"]

    response = client.post(f"/api/ai-suggestions/{suggestion_id}/feedback", json={
        "decision": "corrected", "useful": False,
        "final_category": "Hardware", "final_priority": "Medium",
        "comment": "Employee cannot work without an external keyboard.",
    })

    assert response.status_code == 201
    category, priority, status = _confirmed(client, ticket_id)
    assert (category, priority, status) == ("Hardware", "Medium", "New")  # status never touched by AI flow

    stored = client.get(f"/api/tickets/{ticket_id}/ai-suggestions").json()[0]
    assert stored["suggested_priority"] == "Low"  # original suggestion kept for comparison
    assert stored["feedback"]["decision"] == "corrected"
    assert stored["feedback"]["useful"] is False


def test_accept_copies_suggested_values(client, ticket_id):
    suggestion_id = client.post(f"/api/tickets/{ticket_id}/ai-analysis").json()["id"]
    response = client.post(f"/api/ai-suggestions/{suggestion_id}/feedback",
                           json={"decision": "accepted", "useful": True})
    assert response.status_code == 201
    assert _confirmed(client, ticket_id)[:2] == ("Hardware", "Low")


def test_corrected_without_values_is_422(client, ticket_id):
    suggestion_id = client.post(f"/api/tickets/{ticket_id}/ai-analysis").json()["id"]
    response = client.post(f"/api/ai-suggestions/{suggestion_id}/feedback",
                           json={"decision": "corrected", "useful": True})
    assert response.status_code == 422


def test_feedback_can_only_be_given_once(client, ticket_id):
    suggestion_id = client.post(f"/api/tickets/{ticket_id}/ai-analysis").json()["id"]
    url = f"/api/ai-suggestions/{suggestion_id}/feedback"
    assert client.post(url, json={"decision": "accepted", "useful": True}).status_code == 201
    assert client.post(url, json={"decision": "accepted", "useful": True}).status_code == 409


def test_feedback_on_missing_suggestion_is_404(client):
    response = client.post("/api/ai-suggestions/99999/feedback", json={"decision": "accepted", "useful": True})
    assert response.status_code == 404


def test_dashboard_reports_ai_feedback_stats(client, ticket_id):
    empty = client.get("/api/dashboard/summary").json()["ai"]
    assert empty["suggestions"] == 0 and empty["acceptance_rate"] is None

    first = client.post(f"/api/tickets/{ticket_id}/ai-analysis").json()
    client.post(f"/api/ai-suggestions/{first['id']}/feedback", json={"decision": "accepted", "useful": True})
    second = client.post(f"/api/tickets/{ticket_id}/ai-analysis").json()
    client.post(f"/api/ai-suggestions/{second['id']}/feedback", json={
        "decision": "corrected", "useful": False, "final_category": "Network", "final_priority": "High",
    })

    ai = client.get("/api/dashboard/summary").json()["ai"]
    assert ai["suggestions"] == 2 and ai["tickets_analysed"] == 1
    assert (ai["reviewed"], ai["accepted"], ai["corrected"], ai["useful"]) == (2, 1, 1, 1)
    assert ai["acceptance_rate"] == 50.0 and ai["useful_rate"] == 50.0
