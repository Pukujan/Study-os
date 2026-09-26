# SOS-0016 learner step review: test design (A8)

Status: contract tests, green after the A8-exec implementation; issue #126. The API/database cases in `tests/test_player_step_review_contract.py`, the frontend cases in `web/src/player/FeedbackBar.contract.test.tsx`, and the stub A2A scorecard pass. Playwright/vision and live InferHub remain later gates; hidden acceptance is `not_run`.

## Deterministic and metamorphic acceptance

`tests/test_player_step_review_contract.py` drives the real API in a disposable Postgres database and reads `ux.feedback`. `web/src/player/FeedbackBar.contract.test.tsx` asserts the client only posts after Submit, requires both fields, and sends the bound step and idempotency key. The executor should extend it for draft preservation on same-step re-render and reset on step/variant change once the component accepts presentation context. Do not weaken API checks because frontend checks pass.

| Property | Transformation | Required observation |
| --- | --- | --- |
| M1 replay | Same step + exact payload + key twice | Same `feedback_id`; one row. |
| M2 deliberate second review | Same step + new key | Two distinct immutable rows; first row unchanged. |
| M3 render invariance | Regenerate presentation, then review same step/variant | Review binds original step ID and regenerated version; phase/progress unchanged by review. |
| M4 invalid input | Replace rating with 0, 6, bool, float, string or omit why | 4xx; no row added. |
| M5 stale binding | Change step ID, target variant, session owner, or version | 4xx; no row added. |
| M6 key conflict | Reuse key with different rating/why | 4xx; original row/receipt unchanged. |
| M7 race | Concurrent identical submits with same key | One logical row and one receipt; no duplicate or unhandled 500. |

`tests/test_player_agent_evals.py` and `tools/run_player_agent_evals.py` extend the fixed-seed stub roleplay. A scripted learner submits a 1-5 score and why while the tutor has already re-rendered a sliding-window step. The scorecard verifies a persisted `ux.feedback` review event beside the golden path from `domains/dsa/sliding-window/golden/conformance-oracle.v0.1.json`, and labels the whole run `synthetic_only`. Wrong/partial/confused personas continue through the same path. A review must not advance the step, change a probe grade, or produce a `learn.*` review event. The harness remains opt-in live (`STUDY_OS_EVAL_LIVE=1`) and stubbed by default.

## Holdouts

The visible RED tests cover edge ratings, whitespace why, wrong step, stale version, same-key mutation, and a double-submit race. These are **development adversaries**, not a hidden-holdout pass. A four-case withheld suite is kept in the Astra checkpoint workspace, outside the public branch; its SHA-256 commitment is `BE14EE65C1615C376DB111DFCD3AA766EA2818C8E70BE49AD0422A792AF372D9`. On the A8 base it ran three green negative cases and one RED positive control. The fixture is not a secure seal against anyone with access to the same workstation. An independent post-executor run must record fixture hash, executor revision, outcome, and evaluator identity; hidden acceptance remains `not_run` until then. Never label public test data or golden material as hidden.

## Commands and gate interpretation

With a disposable Postgres role able to create databases, set `TEST_DATABASE_URL` and run:

```powershell
python -m unittest tests.test_player_step_review_contract tests.test_player_agent_evals -v
python tools/run_player_agent_evals.py --seeds 1 --out evals/out/player-a2a-scorecard.json
```

The first command is expected RED until A8-exec; the harness should report a review contract violation, not silently pass. Without `TEST_DATABASE_URL`, DB contract tests skip and the harness exits early: that is `not_run`, not green. Run repository compile/validation/unittest checks separately and report unrelated baseline failures. Playwright/vision and live InferHub are later gates, not A8 results.
