-- Study OS web app schema v1 (SOS-0004, #87). Personal-data scope is normative:
-- see docs/webapp/DATA_MODEL.md and tests/test_web_schema.py (allowlist).
CREATE EXTENSION IF NOT EXISTS citext;

CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS learn;
CREATE SCHEMA IF NOT EXISTS ux;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS cache;

-- D018: open signup with Google sign-in (primary) and a local email/passphrase fallback.
-- Minimal profile only (Google subject, email, display name, learner handle), and only in auth.*.
CREATE TABLE auth.account (
    account_id uuid PRIMARY KEY,
    handle citext NOT NULL UNIQUE CHECK (handle ~ '^[a-z0-9_-]{3,24}$'),
    email citext NULL UNIQUE,
    display_name text NULL CHECK (display_name IS NULL OR length(display_name) <= 80),
    role text NOT NULL CHECK (role IN ('learner', 'admin')),
    created_at timestamptz NOT NULL DEFAULT now(),
    disabled_at timestamptz NULL
);

CREATE TABLE auth.identity (
    provider text NOT NULL CHECK (provider IN ('google', 'local')),
    provider_subject text NOT NULL,
    account_id uuid NOT NULL REFERENCES auth.account(account_id),
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (provider, provider_subject)
);

CREATE TABLE auth.local_credential (
    account_id uuid PRIMARY KEY REFERENCES auth.account(account_id),
    passphrase_hash text NOT NULL CHECK (passphrase_hash LIKE '$argon2id$%'),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE auth.session (
    session_id_hash bytea PRIMARY KEY,
    account_id uuid NOT NULL REFERENCES auth.account(account_id),
    csrf_token_hash bytea NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    last_seen_at timestamptz NOT NULL DEFAULT now(),
    absolute_expires_at timestamptz NOT NULL,
    idle_expires_at timestamptz NOT NULL,
    revoked_at timestamptz NULL
);

CREATE TABLE auth.oauth_state (
    state_hash bytea PRIMARY KEY,
    code_verifier text NOT NULL,
    nonce text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    consumed_at timestamptz NULL
);

-- Throttling only. ip_hash is an HMAC with a server secret (never the raw IP); rows are purged after 1 day.
CREATE TABLE auth.login_attempt (
    account_key_hash bytea NOT NULL,
    ip_hash bytea NOT NULL,
    succeeded boolean NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX login_attempt_account ON auth.login_attempt (account_key_hash, created_at);
CREATE INDEX login_attempt_ip ON auth.login_attempt (ip_hash, created_at);

CREATE TABLE learn.subject (
    subject_id uuid PRIMARY KEY,
    pseudonym text NOT NULL UNIQUE CHECK (pseudonym ~ '^subject-[0-9]{3,}$'),
    created_at timestamptz NOT NULL DEFAULT now()
);

-- The only bridge between identity and learning data. learn.* never references auth.*.
CREATE TABLE auth.account_subject (
    account_id uuid NOT NULL UNIQUE REFERENCES auth.account(account_id),
    subject_id uuid NOT NULL UNIQUE REFERENCES learn.subject(subject_id)
);

CREATE TABLE learn.content_revision (
    revision_id text PRIMARY KEY,
    kind text NOT NULL CHECK (kind IN ('pir_asset', 'subject_pack')),
    ref text NOT NULL,
    sha256 text NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE learn.session (
    session_id uuid PRIMARY KEY,
    subject_id uuid NOT NULL REFERENCES learn.subject(subject_id),
    track text NOT NULL CHECK (track IN ('dsa', 'hesi')),
    started_at timestamptz NOT NULL DEFAULT now(),
    ended_at timestamptz NULL,
    end_state text NULL,
    module_version_set jsonb NOT NULL
);

CREATE TABLE learn.turn (
    turn_id uuid PRIMARY KEY,
    session_id uuid NOT NULL REFERENCES learn.session(session_id),
    seq integer NOT NULL,
    state_before text NOT NULL,
    event text NOT NULL,
    state_after text NOT NULL,
    step_id text NULL,
    item_id text NULL,
    assistance_level smallint NOT NULL DEFAULT 0 CHECK (assistance_level BETWEEN 0 AND 6),
    representation_id text NULL,
    operation text NOT NULL,
    served_from text NOT NULL CHECK (served_from IN ('canonical', 'promoted', 'generated', 'fallback')),
    controller_revision text NOT NULL,
    run_state jsonb NOT NULL,
    payload jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (session_id, seq)
);

CREATE TABLE learn.attempt (
    attempt_id uuid PRIMARY KEY,
    turn_id uuid NOT NULL REFERENCES learn.turn(turn_id),
    idempotency_key text NOT NULL UNIQUE,
    response_kind text NOT NULL,
    response_text_scrubbed text NOT NULL,
    grader text NOT NULL CHECK (grader IN ('deterministic', 'decision_model', 'interpreter', 'none')),
    outcome text NOT NULL CHECK (outcome IN ('correct', 'partial', 'incorrect', 'unresolved')),
    latency_ms integer NULL,
    evidence_class text NOT NULL DEFAULT 'observed',
    result_turn_seq integer NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE learn.capability_transition (
    id bigserial PRIMARY KEY,
    subject_id uuid NOT NULL REFERENCES learn.subject(subject_id),
    kc_id text NOT NULL,
    from_state text NULL,
    to_state text NOT NULL,
    evidence_attempt_ids uuid[] NOT NULL,
    assistance_level smallint NOT NULL,
    "window" text NOT NULL CHECK ("window" IN ('immediate', 'faded', 'transfer', 'delayed')),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE learn.interpretation (
    id uuid PRIMARY KEY,
    turn_id uuid NULL REFERENCES learn.turn(turn_id),
    operation text NOT NULL,
    route text NOT NULL,
    model text NOT NULL,
    price_snapshot_id text NOT NULL,
    prompt_template_version text NOT NULL,
    input_tokens integer NOT NULL DEFAULT 0,
    output_tokens integer NOT NULL DEFAULT 0,
    cost_usd numeric(12, 8) NOT NULL DEFAULT 0,
    latency_ms integer NOT NULL DEFAULT 0,
    validation_result text NOT NULL,
    violation_codes text[] NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE learn.generation (
    generation_id uuid PRIMARY KEY,
    interpretation_id uuid NOT NULL REFERENCES learn.interpretation(id),
    step_id text NOT NULL,
    content_json jsonb NOT NULL,
    validated boolean NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE learn.decision (
    decision_id uuid PRIMARY KEY,
    turn_id uuid NULL REFERENCES learn.turn(turn_id),
    decision_type text NOT NULL CHECK (decision_type IN ('grade', 'misconception', 'affect', 'intent', 'sentiment', 'next_step')),
    state_hash text NOT NULL,
    question_schema jsonb NOT NULL,
    route text NOT NULL CHECK (route IN ('rule', 'decision_model', 'frontier_llm', 'human', 'cache')),
    model_id text NULL,
    model_version text NULL,
    question_type text NULL CHECK (question_type IN ('choice', 'noul', 'score')),
    label text NULL,
    probabilities jsonb NULL,
    confidence real NULL,
    threshold_used real NULL,
    acted_on boolean NOT NULL,
    escalated boolean NOT NULL,
    audit_sample boolean NOT NULL DEFAULT false,
    error text NULL,
    latency_ms integer NOT NULL DEFAULT 0,
    tokens_in integer NOT NULL DEFAULT 0,
    tokens_out integer NOT NULL DEFAULT 0,
    cost_usd numeric(12, 8) NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE learn.decision_label (
    decision_id uuid NOT NULL REFERENCES learn.decision(decision_id),
    label text NOT NULL,
    source text NOT NULL CHECK (source IN ('reviewer', 'deterministic_verifier', 'llm_adjudication', 'learner_outcome', 'learner_dispute')),
    quality text NOT NULL CHECK (quality IN ('gold', 'silver')),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE learn.experiment_assignment (
    subject_id uuid NOT NULL REFERENCES learn.subject(subject_id),
    experiment_id text NOT NULL,
    arm text NOT NULL,
    assignment_unit text NOT NULL,
    propensity real NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- Projection (mutable): FSRS card state per subject and item.
CREATE TABLE learn.review_schedule (
    subject_id uuid NOT NULL REFERENCES learn.subject(subject_id),
    item_id text NOT NULL,
    kc_id text NOT NULL,
    fsrs_state jsonb NOT NULL,
    due_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (subject_id, item_id)
);

CREATE TABLE ux.reaction (
    id bigserial PRIMARY KEY,
    turn_id uuid NOT NULL REFERENCES learn.turn(turn_id),
    kind text NOT NULL CHECK (kind IN ('helped', 'confused', 'frustrated', 'too_easy')),
    created_at timestamptz NOT NULL DEFAULT now()
);

-- First-party UX tracker events (D018: no PostHog). Identifiers and short enums only; no free text.
CREATE TABLE ux.event (
    id bigserial PRIMARY KEY,
    subject_id uuid NULL REFERENCES learn.subject(subject_id),
    session_id uuid NULL REFERENCES learn.session(session_id),
    turn_id uuid NULL REFERENCES learn.turn(turn_id),
    client_session text NOT NULL CHECK (client_session ~ '^[A-Za-z0-9_-]{8,64}$'),
    event_type text NOT NULL CHECK (event_type IN (
        'page_view', 'click', 'step_shown', 'step_answered', 'hint_requested', 'time_on_step',
        'idle', 'tab_hidden', 'tab_visible', 'error', 'rating'
    )),
    path text NULL CHECK (path IS NULL OR path ~ '^/[A-Za-z0-9/_-]{0,120}$'),
    control text NULL CHECK (control IS NULL OR control ~ '^[a-z0-9_.-]{1,48}$'),
    step_id text NULL CHECK (step_id IS NULL OR length(step_id) <= 120),
    value_ms integer NULL CHECK (value_ms IS NULL OR value_ms BETWEEN 0 AND 86400000),
    value_int integer NULL,
    client_ts timestamptz NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ux_event_type_time ON ux.event (event_type, created_at);

-- Model response cache keyed by sha256(model, prompt template, input). No learner identifiers.
CREATE TABLE cache.model_response (
    key_hash text PRIMARY KEY CHECK (key_hash ~ '^[0-9a-f]{64}$'),
    kind text NOT NULL CHECK (kind IN ('decision', 'llm')),
    model text NOT NULL,
    response jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    hits integer NOT NULL DEFAULT 0
);

-- Per-subject topic progress for subject packs (projection, mutable, rebuilt from events).
CREATE TABLE learn.topic_progress (
    subject_id uuid NOT NULL REFERENCES learn.subject(subject_id),
    track text NOT NULL,
    topic_id text NOT NULL,
    state text NOT NULL CHECK (state IN ('not_started', 'in_progress', 'assembled', 'checkpoint_passed')),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (subject_id, track, topic_id)
);

-- Append-only enforcement (P-SYS-3).
CREATE OR REPLACE FUNCTION learn.forbid_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'append-only table %.%: % is not allowed', TG_TABLE_SCHEMA, TG_TABLE_NAME, TG_OP
        USING ERRCODE = 'insufficient_privilege';
END;
$$;

DO $$
DECLARE t text;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'learn.turn', 'learn.attempt', 'learn.capability_transition', 'learn.interpretation',
        'learn.generation', 'learn.decision', 'learn.decision_label', 'learn.experiment_assignment',
        'ux.reaction', 'ux.event'
    ] LOOP
        EXECUTE format(
            'CREATE TRIGGER append_only BEFORE UPDATE OR DELETE OR TRUNCATE ON %s '
            'FOR EACH STATEMENT EXECUTE FUNCTION learn.forbid_mutation()', t);
    END LOOP;
END;
$$;

-- learn.session: only ended_at/end_state may be set, once.
CREATE OR REPLACE FUNCTION learn.session_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'learn.session rows are never deleted' USING ERRCODE = 'insufficient_privilege';
    END IF;
    IF OLD.ended_at IS NOT NULL
       OR NEW.session_id <> OLD.session_id OR NEW.subject_id <> OLD.subject_id
       OR NEW.track <> OLD.track OR NEW.started_at <> OLD.started_at
       OR NEW.module_version_set <> OLD.module_version_set THEN
        RAISE EXCEPTION 'learn.session allows only a single end update' USING ERRCODE = 'insufficient_privilege';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER session_guard BEFORE UPDATE OR DELETE ON learn.session
    FOR EACH ROW EXECUTE FUNCTION learn.session_guard();

-- xAPI-shaped learning event stream (#93). No free text; answers only as hashes.
CREATE OR REPLACE VIEW analytics.v_learning_event AS
SELECT
    encode(sha256(convert_to(s.subject_id::text, 'UTF8')), 'hex') AS learner_key,
    CASE t.event
        WHEN 'start' THEN 'session_start'
        WHEN 'session_done' THEN 'session_end'
        ELSE 'step_shown'
    END AS verb,
    s.track AS object_track,
    t.step_id AS object_step,
    t.item_id AS object_item,
    s.module_version_set ->> 'content_revision' AS object_revision,
    NULL::text AS result_grade,
    t.assistance_level AS result_help_level,
    NULL::integer AS result_latency_ms,
    jsonb_build_object('operation', t.operation, 'served_from', t.served_from, 'state_after', t.state_after) AS context,
    t.created_at AS "timestamp"
FROM learn.turn t JOIN learn.session s USING (session_id)
UNION ALL
SELECT
    encode(sha256(convert_to(s.subject_id::text, 'UTF8')), 'hex'),
    'answer_submitted',
    s.track, t.step_id, t.item_id,
    s.module_version_set ->> 'content_revision',
    a.outcome,
    t.assistance_level,
    a.latency_ms,
    jsonb_build_object('grader', a.grader, 'answer_hash', encode(sha256(convert_to(a.response_text_scrubbed, 'UTF8')), 'hex')),
    a.created_at
FROM learn.attempt a JOIN learn.turn t USING (turn_id) JOIN learn.session s USING (session_id)
UNION ALL
SELECT
    encode(sha256(convert_to(s.subject_id::text, 'UTF8')), 'hex'),
    'self_report',
    s.track, t.step_id, t.item_id,
    s.module_version_set ->> 'content_revision',
    r.kind, t.assistance_level, NULL,
    '{}'::jsonb,
    r.created_at
FROM ux.reaction r JOIN learn.turn t USING (turn_id) JOIN learn.session s USING (session_id);

CREATE OR REPLACE VIEW analytics.v_decision AS
SELECT decision_id, decision_type, route, model_id, model_version, question_type, label,
       confidence, threshold_used, acted_on, escalated, audit_sample, error, latency_ms,
       tokens_in, tokens_out, cost_usd, created_at
FROM learn.decision;

-- Metabase-ready views (#93). Learner identity is the pseudonymous subject hash.
CREATE OR REPLACE VIEW analytics.v_daily_active_learners AS
SELECT day, count(DISTINCT subject_id) AS active_learners
FROM (
    SELECT date_trunc('day', created_at)::date AS day, subject_id FROM ux.event WHERE subject_id IS NOT NULL
    UNION ALL
    SELECT date_trunc('day', t.created_at)::date, s.subject_id
    FROM learn.turn t JOIN learn.session s USING (session_id)
) d
GROUP BY day;

CREATE OR REPLACE VIEW analytics.v_step_funnel AS
SELECT s.track,
       t.step_id,
       count(DISTINCT t.turn_id) FILTER (WHERE t.operation IN ('present_probe', 'present_item')) AS shown,
       count(DISTINCT a.attempt_id) AS answered,
       count(DISTINCT a.attempt_id) FILTER (WHERE a.outcome = 'correct') AS correct,
       count(DISTINCT s.subject_id) AS learners
FROM learn.turn t
JOIN learn.session s USING (session_id)
LEFT JOIN learn.attempt a ON a.turn_id = t.turn_id
WHERE t.step_id IS NOT NULL
GROUP BY s.track, t.step_id;

-- Where sessions stop: the last turn of every session that never reached SESSION_DONE.
CREATE OR REPLACE VIEW analytics.v_drop_off AS
SELECT s.track, last.step_id, last.state_after, count(*) AS sessions
FROM learn.session s
JOIN LATERAL (
    SELECT t.step_id, t.state_after FROM learn.turn t
    WHERE t.session_id = s.session_id ORDER BY t.seq DESC LIMIT 1
) last ON true
WHERE last.state_after <> 'SESSION_DONE'
GROUP BY s.track, last.step_id, last.state_after;

CREATE OR REPLACE VIEW analytics.v_hint_rate AS
SELECT s.track,
       date_trunc('day', t.created_at)::date AS day,
       count(*) FILTER (WHERE t.operation = 'expansion') AS hints,
       count(*) FILTER (WHERE t.operation IN ('present_probe', 'present_item')) AS probes,
       round(
           count(*) FILTER (WHERE t.operation = 'expansion')::numeric
           / nullif(count(*) FILTER (WHERE t.operation IN ('present_probe', 'present_item')), 0), 3
       ) AS hint_rate
FROM learn.turn t JOIN learn.session s USING (session_id)
GROUP BY s.track, day;

CREATE OR REPLACE VIEW analytics.v_accuracy_by_concept AS
SELECT s.track,
       coalesce(t.payload ->> 'concept', split_part(t.step_id, '.', 1)) AS concept,
       count(*) AS attempts,
       count(*) FILTER (WHERE a.outcome = 'correct') AS correct,
       round(count(*) FILTER (WHERE a.outcome = 'correct')::numeric / nullif(count(*), 0), 3) AS accuracy
FROM learn.attempt a
JOIN learn.turn t USING (turn_id)
JOIN learn.session s USING (session_id)
GROUP BY s.track, concept;

CREATE OR REPLACE VIEW analytics.v_time_on_step AS
SELECT step_id, count(*) AS samples,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY value_ms) AS median_ms,
       percentile_cont(0.9) WITHIN GROUP (ORDER BY value_ms) AS p90_ms
FROM ux.event WHERE event_type = 'time_on_step' AND value_ms IS NOT NULL
GROUP BY step_id;
