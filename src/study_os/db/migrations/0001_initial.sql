-- Study OS v0.1 P0 schema.  This migration is intentionally project-agnostic.
CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS subjects (
    subject_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
);

CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS domains (
    domain_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    created_at TEXT NOT NULL,
    UNIQUE (project_id, domain_id)
);

CREATE TABLE IF NOT EXISTS concepts (
    concept_id TEXT PRIMARY KEY,
    domain_id TEXT REFERENCES domains(domain_id),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL REFERENCES subjects(subject_id),
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    domain_id TEXT NOT NULL REFERENCES domains(domain_id),
    started_at TEXT NOT NULL,
    ended_at TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    source_client TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS raw_artifacts (
    artifact_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    sha256 TEXT NOT NULL,
    storage_path TEXT NOT NULL UNIQUE,
    media_type TEXT,
    captured_at TEXT NOT NULL,
    capture_method TEXT NOT NULL,
    source_metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS messages (
    message_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    role TEXT NOT NULL,
    artifact_id TEXT REFERENCES raw_artifacts(artifact_id),
    content_sha256 TEXT,
    created_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS learning_events (
    event_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    subject_id TEXT NOT NULL REFERENCES subjects(subject_id),
    evidence_class TEXT NOT NULL CHECK (evidence_class IN ('observed', 'self_reported', 'derived')),
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    payload_version TEXT NOT NULL DEFAULT '0.1.0',
    source_ids_json TEXT NOT NULL DEFAULT '[]',
    idempotency_key TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS episodes (
    episode_id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL REFERENCES subjects(subject_id),
    session_id TEXT REFERENCES sessions(session_id),
    status TEXT NOT NULL DEFAULT 'open',
    boundary_confidence REAL,
    review_status TEXT NOT NULL DEFAULT 'unreviewed',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attempts (
    attempt_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    subject_id TEXT NOT NULL REFERENCES subjects(subject_id),
    task_id TEXT NOT NULL,
    response_json TEXT NOT NULL,
    assistance_level TEXT NOT NULL DEFAULT 'none',
    context_json TEXT NOT NULL DEFAULT '{}',
    idempotency_key TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assessments (
    assessment_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    subject_id TEXT NOT NULL REFERENCES subjects(subject_id),
    capability TEXT NOT NULL,
    result TEXT NOT NULL,
    assistance_level TEXT NOT NULL,
    evidence_ids_json TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS representations (
    representation_id TEXT PRIMARY KEY,
    family TEXT NOT NULL,
    semantic_version TEXT NOT NULL,
    definition_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE (family, semantic_version)
);

CREATE TABLE IF NOT EXISTS interventions (
    intervention_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    subject_id TEXT NOT NULL REFERENCES subjects(subject_id),
    representation_id TEXT NOT NULL REFERENCES representations(representation_id),
    representation_family TEXT NOT NULL,
    operation TEXT NOT NULL,
    representation_version TEXT NOT NULL,
    target_bottleneck TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS representation_outcomes (
    outcome_id TEXT PRIMARY KEY,
    intervention_id TEXT NOT NULL REFERENCES interventions(intervention_id),
    subject_id TEXT NOT NULL REFERENCES subjects(subject_id),
    evidence_score INTEGER NOT NULL CHECK (evidence_score BETWEEN 0 AND 5),
    evidence_ids_json TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS checkpoints (
    checkpoint_id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL REFERENCES subjects(subject_id),
    source_session_ids_json TEXT NOT NULL,
    evidence_ids_json TEXT NOT NULL,
    capability_state_json TEXT NOT NULL,
    assistance_state_json TEXT NOT NULL,
    current_focus TEXT NOT NULL,
    do_not_reteach_json TEXT NOT NULL DEFAULT '[]',
    next_action TEXT NOT NULL,
    retention_due_at TEXT,
    derivation_version TEXT NOT NULL DEFAULT '0.1.0',
    idempotency_key TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS subject_current_checkpoint (
    subject_id TEXT PRIMARY KEY REFERENCES subjects(subject_id),
    checkpoint_id TEXT NOT NULL REFERENCES checkpoints(checkpoint_id),
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS retention_probes (
    retention_probe_id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL REFERENCES subjects(subject_id),
    concept_id TEXT NOT NULL REFERENCES concepts(concept_id),
    due_at TEXT NOT NULL,
    source_checkpoint_id TEXT NOT NULL REFERENCES checkpoints(checkpoint_id),
    status TEXT NOT NULL DEFAULT 'scheduled',
    result_json TEXT,
    idempotency_key TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fossil_exports (
    export_id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL REFERENCES subjects(subject_id),
    artifact_type TEXT NOT NULL,
    source_ids_json TEXT NOT NULL,
    storage_path TEXT NOT NULL UNIQUE,
    idempotency_key TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS idempotency_records (
    operation_name TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_fingerprint TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    result_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (operation_name, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_sessions_subject_started ON sessions(subject_id, started_at);
CREATE INDEX IF NOT EXISTS idx_events_session_created ON learning_events(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_events_subject_created ON learning_events(subject_id, created_at);
CREATE INDEX IF NOT EXISTS idx_artifacts_session ON raw_artifacts(session_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_subject_created ON checkpoints(subject_id, created_at);
CREATE INDEX IF NOT EXISTS idx_interventions_subject_created ON interventions(subject_id, created_at);
CREATE INDEX IF NOT EXISTS idx_outcomes_subject_created ON representation_outcomes(subject_id, created_at);
CREATE INDEX IF NOT EXISTS idx_retention_due ON retention_probes(subject_id, status, due_at);
