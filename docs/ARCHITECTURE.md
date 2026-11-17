# Architecture

```mermaid
flowchart LR
    subgraph Browser
        EMP[Employee pages<br/>Raise ticket · My tickets · Detail]
        SUP[Support pages<br/>Work queue · Processing · AI panel · Dashboard]
    end

    subgraph Backend["FastAPI (backend/app)"]
        R1[routers/tickets.py<br/>create · list · get · update · history]
        R2[routers/workflow.py<br/>status transitions · comments]
        R3[routers/ai.py<br/>analysis · suggestions · feedback]
        R4[routers/dashboard.py<br/>summary · requesters]
        V[Pydantic schemas<br/>enums + 422 validation]
        AIS[services/ai_service.py<br/>prompt · timeout · JSON validation · retry]
        LOG[logging_config.py<br/>redacted event logs]
    end

    DB[(PostgreSQL<br/>requesters · tickets · ticket_activity<br/>ai_suggestions · ai_feedback)]
    OLL[Ollama<br/>qwen2.5:3b<br/>localhost:11434]

    EMP -- "axios / JSON" --> R1
    SUP -- "axios / JSON" --> R1 & R2 & R3 & R4
    R1 & R2 & R3 & R4 --> V
    R1 & R2 & R3 & R4 -- SQLAlchemy --> DB
    R3 --> AIS -- "OpenAI-compatible /v1/chat/completions<br/>JSON schema output" --> OLL
```

## Human control over the AI

```mermaid
sequenceDiagram
    actor Staff
    participant UI as React AI panel
    participant API as FastAPI
    participant AI as Ollama
    participant DB as PostgreSQL

    Staff->>UI: Run AI analysis
    UI->>API: POST /api/tickets/{id}/ai-analysis
    API->>AI: system rules + ticket text wrapped as data
    alt valid JSON matching schema
        AI-->>API: category, priority, reason, steps
        API->>DB: INSERT ai_suggestions (ticket NOT changed)
        API-->>UI: 201 suggestion
    else model down / timeout / bad output
        API-->>UI: 503 / 504 / 502 {"detail": "..."}
        Note over API,DB: nothing written, ticket untouched
    end
    Staff->>UI: Accept or correct, useful / not useful
    UI->>API: POST /api/ai-suggestions/{id}/feedback
    API->>DB: INSERT ai_feedback, UPDATE ticket category/priority (never status)
```

## Key rules

| Rule | Where it is enforced |
|---|---|
| Enums identical everywhere | `schemas/enums.py`, CHECK constraints in `models/`, `frontend/src/constants.js` |
| Status only via allowed transitions (else 409) | `routers/workflow.py` |
| Status cannot be edited via PATCH /tickets/{id} (422) | `TicketUpdate` forbids extra fields |
| AI suggestion stored apart from confirmed values | `ai_suggestions` table; ticket changes only in the feedback endpoint |
| AI failure never touches the ticket | `ai_service.py` writes nothing; router commits only after valid output |
| No ticket text, secrets or connection strings in logs | `logging_config.py` redaction; SQL echo off |
