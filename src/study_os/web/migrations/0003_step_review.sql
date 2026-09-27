-- Study OS learner step review (SOS-0016 / issue #126).
-- Additive only: existing ux.feedback rows keep null key/version and their
-- historical like/dislike ratings. 0002_player.sql already created the table.

ALTER TABLE ux.feedback ADD COLUMN IF NOT EXISTS presentation_version integer NULL;
ALTER TABLE ux.feedback ADD COLUMN IF NOT EXISTS idempotency_key text NULL;

-- One committed review intent per subject+key; exact replay reads the original
-- row, a fresh key deliberately appends. Historical rows (null key) are exempt.
CREATE UNIQUE INDEX IF NOT EXISTS feedback_subject_idempotency
    ON ux.feedback (subject_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

-- Append-only: no UPDATE/DELETE/TRUNCATE in normal review flows.
DROP TRIGGER IF EXISTS feedback_append_only ON ux.feedback;
CREATE TRIGGER feedback_append_only
    BEFORE UPDATE OR DELETE OR TRUNCATE ON ux.feedback
    FOR EACH STATEMENT EXECUTE FUNCTION learn.forbid_mutation();

-- Surface the reviewed presentation version beside the existing columns.
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
    ps.lesson_revision,
    f.presentation_version
FROM ux.feedback f
LEFT JOIN learn.llm_interaction i ON i.id = f.llm_interaction_id
LEFT JOIN learn.player_session ps ON ps.session_id = f.session_id;
