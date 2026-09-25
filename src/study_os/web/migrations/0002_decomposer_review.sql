-- SOS-0011: append-only pedagogical decomposer human reviews (per-step ratings + optional notes).
-- Free text is allowed here because this is Alex/product pedagogy feedback, not learner PII.

CREATE TABLE ux.decomposer_review (
    id bigserial PRIMARY KEY,
    review_batch_id text NOT NULL CHECK (review_batch_id ~ '^[A-Za-z0-9_-]{8,64}$'),
    client_session text NOT NULL CHECK (client_session ~ '^[A-Za-z0-9_-]{8,64}$'),
    subject_id uuid NULL REFERENCES learn.subject(subject_id),
    problem_id text NOT NULL CHECK (length(problem_id) BETWEEN 1 AND 80),
    variant_id text NOT NULL CHECK (length(variant_id) BETWEEN 1 AND 160),
    step_id text NULL CHECK (step_id IS NULL OR length(step_id) <= 80),
    step_index integer NULL CHECK (step_index IS NULL OR step_index BETWEEN 0 AND 500),
    artifact_format text NULL CHECK (artifact_format IS NULL OR artifact_format IN (
        'ascii', 'mermaid', 'algebra', 'katex', 'code', 'svg', 'mixed', 'overall'
    )),
    rating text NOT NULL CHECK (rating IN ('good', 'bad', 'prefer', 'ok', 'skip')),
    note text NULL CHECK (note IS NULL OR length(note) <= 4000),
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    client_ts timestamptz NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX ux_decomposer_review_problem_time
    ON ux.decomposer_review (problem_id, created_at);
CREATE INDEX ux_decomposer_review_batch
    ON ux.decomposer_review (review_batch_id);

CREATE TRIGGER append_only_decomposer_review
    BEFORE UPDATE OR DELETE OR TRUNCATE ON ux.decomposer_review
    FOR EACH STATEMENT EXECUTE FUNCTION learn.forbid_mutation();
