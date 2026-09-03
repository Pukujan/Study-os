# Cross-Chat Continuity Implementation Receipt

Date: 2026-09-03

This receipt records the code-side repair for Issue #59 and the subsequent
real-GPT verification on the live WSL-backed Study OS runtime.

## Implemented

- Added checkpoint-independent `resume_learning_context(subject_id)`.
- Kept historical `resume(subject_id)` checkpoint semantics unchanged.
- Returned accepted checkpoint state separately from bounded post-checkpoint or
  evidence-only context.
- Returned exact bounded source excerpts with hashes; transcript evidence is
  never promoted to capability or mastery state.
- Added subject isolation and explicit unknown-subject identity diagnostics.
- Versioned the current semantic MCP surface from v0.2.0 to v0.3.0 by adding
  the one bounded continuity query. v0.1.0 and v0.2.0 remain immutable.
- Narrowed `/actions` exception handling so `StudyOSError` categories remain
  semantic error categories.

## Verification

- CT1–CT9: PASS in `tests/test_p3_cross_chat_continuity.py`.
- `/actions` validation, not-found, and conflict categories: PASS.
- Full repository suite: PASS (265 tests).
- Repository validation: PASS.
- Engineering baseline: PASS.
- Schema migration: NO.
- CT10: PASS through a fresh Study OS GPT chat; it returned
  `checkpoint_plus_recent_evidence`, recovered `sliding-window`, and kept
  transcript material explicitly source-only.
- CT11: PASS through a fresh Study OS GPT chat; the exact learner turn is in
  `messages` and `raw_artifacts`.
- CT12: PASS through a fresh Study OS GPT chat; the exact displayed assistant
  response is in `messages` and `raw_artifacts`.
- Live message/artifact hashes: PASS; database content hashes match artifact
  hashes and on-disk bytes.
- Live WSL `study-os.service` and Cloudflare tunnel: ACTIVE.
- Live doctor: HEALTHY with zero foreign-key, checkpoint, and evidence
  integrity failures.

## Deferred

Historical transcript reconciliation remains deferred until the real capture
path has been used in ordinary learner conversations and any private/lossless
historical sources have been audited. Issue #56 remains open for that reason.
