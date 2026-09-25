-- Study OS player v2 schema (SOS-0005).
-- Extends 0001_webapp.sql; append-only triggers reuse learn.forbid_mutation().

ALTER TABLE auth.account ADD COLUMN IF NOT EXISTS is_guest boolean NOT NULL DEFAULT false;

CREATE TABLE IF NOT EXISTS learn.player_session (
    session_id uuid PRIMARY KEY,
    subject_id uuid NOT NULL REFERENCES learn.subject(subject_id),
    lesson_id text NOT NULL,
    lesson_revision text NOT NULL,
    state jsonb NOT NULL,
    started_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    ended_at timestamptz NULL
);

CREATE TABLE IF NOT EXISTS learn.player_event (
    id bigserial PRIMARY KEY,
    session_id uuid NOT NULL REFERENCES learn.player_session(session_id),
    seq integer NOT NULL,
    step_id text NULL,
    event text NOT NULL,
    modality text NULL,
    outcome text NULL,
    response_scrubbed text NULL,
    idempotency_key text UNIQUE NULL,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS player_event_session_seq ON learn.player_event (session_id, seq);

CREATE TABLE IF NOT EXISTS learn.llm_interaction (
    id uuid PRIMARY KEY,
    session_id uuid NULL REFERENCES learn.player_session(session_id),
    step_id text NULL,
    operation text NOT NULL,
    prompt_id text NULL,
    prompt_version text NULL,
    route text NULL,
    model text NULL,
    messages jsonb NOT NULL,
    response_text text NULL,
    served text NOT NULL,
    tokens_in integer NOT NULL DEFAULT 0,
    tokens_out integer NOT NULL DEFAULT 0,
    cost_usd numeric(12, 8) NOT NULL DEFAULT 0,
    latency_ms integer NOT NULL DEFAULT 0,
    validation_codes text[] NOT NULL DEFAULT '{}'::text[],
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ux.feedback (
    feedback_id uuid PRIMARY KEY,
    subject_id uuid NOT NULL REFERENCES learn.subject(subject_id),
    session_id uuid NULL REFERENCES learn.player_session(session_id),
    step_id text NULL,
    target_kind text NOT NULL,
    target_id text NOT NULL,
    rating text NOT NULL,
    reasons text[] NOT NULL DEFAULT '{}'::text[],
    free_text_scrubbed text NULL,
    prompt_version text NULL,
    model text NULL,
    llm_interaction_id uuid NULL REFERENCES learn.llm_interaction(id),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS feedback_subject_created ON ux.feedback (subject_id, created_at);

CREATE OR REPLACE VIEW analytics.v_feedback AS
SELECT
    f.feedback_id,
    f.subject_id,
    f.session_id,
    f.step_id,
    f.target_kind,
    f.target_id,
    f.rating,
    f.reasons,
    f.free_text_scrubbed,
    f.prompt_version,
    f.model,
    f.llm_interaction_id,
    f.created_at,
    i.route AS llm_route,
    i.prompt_version AS llm_prompt_version,
    i.model AS llm_model,
    ps.lesson_id,
    ps.lesson_revision
FROM ux.feedback f
LEFT JOIN learn.llm_interaction i ON i.id = f.llm_interaction_id
LEFT JOIN learn.player_session ps ON ps.session_id = f.session_id;

-- Append-only: player_event and llm_interaction.
DROP TRIGGER IF EXISTS player_event_append_only ON learn.player_event;
CREATE TRIGGER player_event_append_only
    BEFORE UPDATE OR DELETE OR TRUNCATE ON learn.player_event
    FOR EACH STATEMENT EXECUTE FUNCTION learn.forbid_mutation();

DROP TRIGGER IF EXISTS llm_interaction_append_only ON learn.llm_interaction;
CREATE TRIGGER llm_interaction_append_only
    BEFORE UPDATE OR DELETE OR TRUNCATE ON learn.llm_interaction
    FOR EACH STATEMENT EXECUTE FUNCTION learn.forbid_mutation();
