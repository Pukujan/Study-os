-- Study OS P4 known-problem PIR persistence.
CREATE TABLE IF NOT EXISTS problem_runs (
    problem_run_id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL REFERENCES subjects(subject_id),
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    canonical_problem_id TEXT NOT NULL,
    canonical_pir_revision TEXT NOT NULL,
    controller_revision TEXT NOT NULL,
    renderer_revision TEXT NOT NULL,
    assessment_revision TEXT NOT NULL,
    current_step_id TEXT,
    status TEXT NOT NULL CHECK (
        status IN ('active', 'assembled_mastery_unproven', 'completed_validated', 'blocked')
    ),
    transition_seq INTEGER NOT NULL DEFAULT 0 CHECK (transition_seq >= 0),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS problem_run_operations (
    operation_id TEXT PRIMARY KEY,
    operation_kind TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_fingerprint TEXT NOT NULL,
    problem_run_id TEXT NOT NULL REFERENCES problem_runs(problem_run_id),
    result_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (operation_kind, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_problem_runs_subject_updated
    ON problem_runs(subject_id, updated_at);
CREATE INDEX IF NOT EXISTS idx_problem_runs_session_updated
    ON problem_runs(session_id, updated_at);
CREATE INDEX IF NOT EXISTS idx_problem_run_operations_run_created
    ON problem_run_operations(problem_run_id, created_at);
