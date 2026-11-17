-- AI tables for schema.sql (Member A merges this after the tickets table).
-- Enums must match app/schemas/enums.py exactly.

CREATE TABLE ai_suggestions (
    id                    SERIAL PRIMARY KEY,
    ticket_id             INTEGER      NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    suggested_category    VARCHAR(20)  NOT NULL
        CONSTRAINT ck_ai_suggestions_category CHECK (suggested_category IN ('Hardware','Software','Network','Access','Other')),
    suggested_priority    VARCHAR(10)  NOT NULL
        CONSTRAINT ck_ai_suggestions_priority CHECK (suggested_priority IN ('Low','Medium','High')),
    priority_reason       TEXT         NOT NULL,
    troubleshooting_steps JSONB        NOT NULL,
    model_name            VARCHAR(100) NOT NULL,
    prompt_version        VARCHAR(20)  NOT NULL,
    latency_ms            INTEGER,
    analyzed_at           TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX ix_ai_suggestions_ticket ON ai_suggestions (ticket_id, analyzed_at DESC);

CREATE TABLE ai_feedback (
    id              SERIAL PRIMARY KEY,
    suggestion_id   INTEGER     NOT NULL UNIQUE REFERENCES ai_suggestions(id) ON DELETE CASCADE,
    ticket_id       INTEGER     NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    decision        VARCHAR(10) NOT NULL
        CONSTRAINT ck_ai_feedback_decision CHECK (decision IN ('accepted','corrected')),
    useful          BOOLEAN     NOT NULL,
    final_category  VARCHAR(20) NOT NULL
        CONSTRAINT ck_ai_feedback_category CHECK (final_category IN ('Hardware','Software','Network','Access','Other')),
    final_priority  VARCHAR(10) NOT NULL
        CONSTRAINT ck_ai_feedback_priority CHECK (final_priority IN ('Low','Medium','High')),
    comment         TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_ai_feedback_ticket ON ai_feedback (ticket_id);

-- Example seed rows (run after tickets are seeded; ticket ids 1 and 2 assumed)
INSERT INTO ai_suggestions (ticket_id, suggested_category, suggested_priority, priority_reason,
                            troubleshooting_steps, model_name, prompt_version, latency_ms)
VALUES
 (1, 'Hardware', 'Low', 'Single user affected and the laptop keyboard works as a workaround.',
  '["Replace the keyboard batteries", "Re-pair the USB receiver", "Try a different USB port"]', 'seed-data', 'v1', 4200),
 (2, 'Network', 'High', 'Whole department cannot access the file share and has no workaround.',
  '["Check file server status", "Confirm DNS resolves the share", "Review recent network or permission changes"]', 'seed-data', 'v1', 5100);

INSERT INTO ai_feedback (suggestion_id, ticket_id, decision, useful, final_category, final_priority, comment)
VALUES (1, 1, 'corrected', TRUE, 'Hardware', 'Medium', 'User needs the external keyboard for accessibility.');
