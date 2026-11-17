"""Shared pytest fixtures (F9.1).

Uses a SEPARATE test database (TEST_DATABASE_URL) and replaces the real AI service
with a fake, so tests never call OpenRouter (no internet or API key needed) and never touch your dev data.

    createdb helpdesk_test
    export TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/helpdesk_test
    pytest -v
"""
import os

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/helpdesk_test"
)
assert "test" in TEST_DATABASE_URL, "Refusing to run: tests drop all tables, use a *_test database"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL  # must be set before the app is imported

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.models.ai  # noqa: E402,F401  (registers AI tables on Base.metadata)
import app.models.ticket  # noqa: E402,F401
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.ticket import Requester  # noqa: E402
from app.schemas.ai import AIAnalysisResult  # noqa: E402
from app.services.ai_service import AnalysisOutcome, get_ai_service  # noqa: E402


class FakeAIService:
    """Stands in for OpenRouter. Set `.error` to an AIServiceError to simulate failures."""

    def __init__(self):
        self.error = None
        self.calls = 0
        self.result = AIAnalysisResult(
            category="Hardware",
            priority="Low",
            priority_reason="Single user affected and a workaround exists.",
            troubleshooting_steps=["Replace the batteries", "Re-pair the USB receiver", "Try another USB port"],
        )

    def analyze_ticket(self, title, description):
        self.calls += 1
        if self.error:
            raise self.error
        return AnalysisOutcome(result=self.result, model_name="fake-model", prompt_version="test", latency_ms=5)

    def health(self):
        return {"status": "ok", "model": "fake-model"}


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def fake_ai():
    fake = FakeAIService()
    app.dependency_overrides[get_ai_service] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_ai_service, None)


@pytest.fixture
def client(fake_ai):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def requester_id():
    # Adjust field names if Member A's Requester model differs.
    with SessionLocal() as session:
        requester = Requester(display_name="Asha Kumar", email="asha.kumar@example.com")
        session.add(requester)
        session.commit()
        return requester.id


@pytest.fixture
def ticket_id(client, requester_id):
    response = client.post("/api/tickets", json={
        "title": "Wireless keyboard not typing",
        "description": "My wireless keyboard stopped responding this morning. The laptop keyboard still works.",
        "requester_id": requester_id,
    })
    assert response.status_code == 201, response.text
    return response.json()["id"]
