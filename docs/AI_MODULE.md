# AI module (Member B) - OpenRouter

The AI part of the helpdesk: triage suggestions from a free OpenRouter model, stored
separately from the ticket, applied only when support staff accept or correct them.

## Files and where each one goes

| File | Story | Branch | Commit message |
|---|---|---|---|
| backend/app/config.py (AI block) + .env.example | F1.2 | feature/ai-config | feat(config): add AI provider settings |
| backend/requirements.txt (lines from requirements-ai.txt) | F1.1 | feature/ai-config | chore(backend): add httpx and pydantic-settings |
| backend/app/schemas/enums.py (if A hasn't made it) | F2.1 | feature/ai-config | feat(api): add shared enums |
| backend/app/schemas/ai.py | F5.3 / F6 | feature/ai-schemas | feat(ai): add AI output and feedback schemas |
| backend/app/services/prompts.py | F5.2 | feature/ai-prompt | feat(ai): add triage prompt with injection guard |
| backend/app/services/ai_service.py | F5.1 / F5.3 / F5.4 | feature/ai-openrouter-client | feat(ai): add OpenRouter client with validation and retry |
| backend/app/models/ai.py + database/ai_tables.sql (to A) | F2.1 | feature/ai-tables | feat(db): add ai_suggestions and ai_feedback tables |
| backend/app/routers/ai.py (analysis + list) | F6.1 / F6.2 | feature/ai-analysis-api | feat(api): add AI analysis endpoints |
| backend/app/routers/ai.py (feedback) | F6.3 | feature/ai-feedback-api | feat(api): add AI feedback endpoint |
| backend/app/logging_config.py | F1.4 | feature/logging | feat(backend): add logging with secret redaction |
| backend/tests/* | F9.1 | test/ai-and-core | test: cover tickets, AI failures and feedback |
| backend/scripts/ai_smoke.py + this file | F9.2 | docs/ai-setup | docs: add AI setup and smoke script |

requirements-ai.txt is a helper list only: copy its lines into requirements.txt, don't commit it separately.

## What this code expects from Member A
- `app/db.py` exports `Base`, `engine`, `SessionLocal`, `get_db`.
- `app/models/ticket.py` exports:
  - `Requester(id, display_name, email)`
  - `Ticket(id, requester_id, title, description, category, priority, status, ...)`, category/priority nullable
  - `TicketActivity(id, ticket_id, action, note, old_status, new_status, created_at)`
- Ticket endpoints as in the shared API contract (tests/test_tickets.py calls them).
- If names differ, change only the imports/field names in routers/ai.py and tests/conftest.py.

## Lines to add to main.py
```python
from app.config import settings
from app.logging_config import setup_logging
from app.routers import ai
from app.services.ai_service import get_ai_service

setup_logging(settings.log_level)          # near the top, before app = FastAPI(...)
app.include_router(ai.router)              # next to the other include_router lines

@app.get("/health")                        # A's health endpoint, with the AI part added
def health():
    return {"database": db_status(), "ai": get_ai_service().health()}
```

## Setup
1. Create a key at openrouter.ai and put it in backend/.env as AI_API_KEY (never in .env.example).
2. Optional: pick a specific free model id from the OpenRouter models page (filter: free, structured outputs)
   and set AI_MODEL to it, so demo results are repeatable. `openrouter/free` picks a random free model.
3. Check the model: `cd backend && python -m scripts.ai_smoke`
4. Tests (no internet needed, OpenRouter is mocked):
   ```bash
   createdb -U postgres helpdesk_test
   # Windows PowerShell: $env:TEST_DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/helpdesk_test"
   export TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/helpdesk_test
   pytest -v
   ```

## Error contract for the React AI panel
| HTTP | Meaning | UI |
|---|---|---|
| 201 | Suggestion stored | Show suggestion beside confirmed values |
| 404 | Ticket/suggestion missing | Show `detail` |
| 409 | Feedback already given | Show `detail`, reload suggestions |
| 422 | Invalid feedback | Show `detail` |
| 502 | Model output failed validation | "AI could not produce a valid suggestion" + Retry |
| 503 | No internet, bad/missing key, rate limit, provider down | "AI unavailable" banner; ticket actions still work |
| 504 | Model timed out | Retry button |

## Scenario 04 (AI unavailable) demo
Set `AI_API_KEY=wrong` in .env and restart the backend, or disconnect the internet.
Create, list and update tickets still work; "Analyse" shows the 503 message.

## Safety notes
- Free-model prompts may be logged by providers: use demo tickets only, no real employee data.
- The API key lives only in backend/.env; logs never include it (see logging_config.py).
- Ticket text is wrapped as untrusted data; output enums are enforced by schema and Pydantic.
- AI never changes ticket status. Category/priority change only via staff feedback.
