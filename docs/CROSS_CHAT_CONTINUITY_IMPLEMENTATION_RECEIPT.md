# Cross-Chat Continuity Implementation Receipt

Date: 2026-09-03

This receipt records the code-side repair for Issue #59. It does not claim
real-GPT acceptance while the Study OS GPT surface remains unverified.

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

## Not yet accepted

CT10–CT12 require the actual Study OS GPT, not synthetic service, MCP, or
Actions calls. The GPT must prove stable subject/runtime binding, durable user
turn capture, durable exact assistant-response capture, and fresh-chat
continuity. Historical transcript reconciliation remains deferred until that
proof exists.
