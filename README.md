# AI-Powered Employee Helpdesk

Employees raise and track IT tickets. Support staff triage, comment and resolve them. A **local Ollama model (`qwen2.5:3b`)** suggests category, priority and troubleshooting steps. Staff accept or correct the suggestion, and the AI never changes ticket status.

**Stack:** React (Vite) → FastAPI + Pydantic + SQLAlchemy → PostgreSQL, with Ollama for AI. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 14+
- [Ollama](https://ollama.com), then `ollama pull qwen2.5:3b`

## 1. Database

Create two databases (the second is for tests only):

```sql
CREATE DATABASE helpdesk;
CREATE DATABASE helpdesk_test;
```

## 2. Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy ..\.env.example .env          # then edit DATABASE_URL with your Postgres password

python -m app.init_db              # create tables (add --reset to drop and recreate)
python -m app.seed                 # 6 requesters, 10 tickets, history and AI samples
uvicorn app.main:app --reload      # http://localhost:8000/docs
```

`GET /health` reports database and AI model status separately.

## 3. Frontend

```powershell
cd frontend
npm install
npm run dev                        # http://localhost:5173
```

The API URL defaults to `http://localhost:8000`. To change it, set `VITE_API_URL` in `frontend/.env` (see `frontend/.env.example`).

## 4. Ollama

```powershell
ollama pull qwen2.5:3b
ollama serve                       # usually already running as a background service
```

The AI settings live in `backend/.env`:

| Setting | Default |
|---|---|
| `AI_BASE_URL` | `http://localhost:11434/v1` |
| `AI_MODEL` | `qwen2.5:3b` |
| `AI_TIMEOUT_SECONDS` | `60` |

The first analysis loads the model into memory, so it is slower than later ones.

## 5. Tests

```powershell
cd backend
$env:TEST_DATABASE_URL="postgresql+psycopg://postgres:<password>@localhost:5432/helpdesk_test"
pytest -v
```

The tests replace Ollama with a fake, so the model does not need to be running. They drop and recreate every table, which is why they refuse to run unless the database name contains `test`.

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/tickets` | Create ticket (201, 422) |
| GET | `/api/tickets?status=&category=&priority=&requester_id=` | List with requester |
| GET | `/api/tickets/{id}` | Detail (404) |
| PATCH | `/api/tickets/{id}` | Update title, description, category, priority |
| GET | `/api/tickets/{id}/history` | Activity, oldest first, with old and new status |
| PATCH | `/api/tickets/{id}/status` | New → In Progress → Resolved; Resolved → In Progress to reopen; any other change is 409 |
| POST | `/api/tickets/{id}/comments` | Support comment |
| POST | `/api/tickets/{id}/ai-analysis` | Run AI; 502 bad output, 503 model unavailable, 504 timeout |
| GET | `/api/tickets/{id}/ai-suggestions` | Latest suggestions with feedback |
| POST | `/api/ai-suggestions/{id}/feedback` | Accept or correct, useful flag, final values |
| GET | `/api/dashboard/summary` | Counts by status, priority and category |
| GET | `/api/requesters` | Requesters for the employee picker |
| GET | `/health` | Database and model status |

Every error body is `{"detail": "<message>"}`, apart from 422 validation errors, which list each failing field.

## Demo scenarios

| # | Steps |
|---|---|
| 01 Routine ticket | Raise *"Wireless keyboard not typing"*, open it in **Work queue**, then **Run AI analysis**. Expect Hardware / Low with steps. |
| 02 Major outage | Ticket #4 *"Finance shared drive unreachable"*: run AI analysis. Expect High priority. |
| 03 Human correction | On any suggestion, click **Correct it…**, change priority, mark useful and save. Refresh: the values and feedback are still there. |
| 04 AI unavailable | Quit Ollama (tray icon, or `taskkill /IM ollama.exe /F`). The AI dot in the header turns red. Creating, listing and updating still work, and **Run AI analysis** shows a clear error. |
| 05 Invalid request | Submit **Raise ticket** with empty fields. FastAPI's 422 messages appear beside each field. |
| 06 Persistence | Stop uvicorn, start it again and refresh React. Tickets, history, comments and feedback are all still there. |

## Project layout

```
backend/app/    main.py, config.py, db.py, init_db.py, seed.py, logging_config.py
  routers/      tickets, workflow, ai, dashboard
  schemas/      Pydantic models + shared enums
  services/     ai_service (Ollama client), prompts
  models/       SQLAlchemy ORM models
backend/tests/  pytest suite (TestClient + fake AI)
frontend/src/   api/, pages/employee/, pages/support/, components/
database/       queries.sql (join + aggregate queries)
docs/           architecture, AI module notes, screenshots
```
