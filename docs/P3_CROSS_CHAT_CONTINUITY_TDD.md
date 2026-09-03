# P3 Cross-Chat Continuity TDD

Status: implementation acceptance plan  
Date: 2026-09-03  
Parent: #52  
Related: #56, #59

## Test-first rule

Do not change live learner data to make a test pass.

Implement on disposable/synthetic runtime roots first. Preserve the real `/root/.study-os` runtime until synthetic/focused tests are green and the exact live action is understood.

## CT1 — Existing checkpoint resumes normally

Given a subject with an accepted current checkpoint:

- existing `resume(subject_id)` behavior remains valid;
- `resume_learning_context(subject_id)` returns the same accepted checkpoint values without mutation;
- continuity status is `checkpoint_only` or `checkpoint_plus_recent_evidence` depending on newer evidence.

## CT2 — No checkpoint + durable prior evidence returns continuity

Given a subject with no `subject_current_checkpoint` but with durable session/message evidence:

- `resume(subject_id)` may retain historical not-found semantics;
- `resume_learning_context(subject_id)` returns `evidence_only`;
- bounded recent evidence is returned;
- no checkpoint row is synthesized.

Use a synthetic subject analogous to the existing source-turn smoke case.

## CT3 — Checkpoint + newer evidence is separated

Given:

- accepted checkpoint at time T;
- durable messages/events/attempts after T;

then continuity returns:

- accepted checkpoint unchanged;
- separate `post_checkpoint_evidence`;
- no silent mutation of capability/current focus/next action.

## CT4 — Transcript evidence does not become mastery

Given source turns discussing or correctly answering a concept without an accepted assessment:

- continuity may report that the learner worked on/discussed the concept;
- capability/mastery fields must not be invented or upgraded.

Assert absence of derived mastery unless supported by existing accepted learner-state evidence.

## CT5 — Subject isolation

Create two subjects with different histories.

Assert that continuity for subject A never returns:

- session IDs;
- message IDs;
- artifact IDs;
- event IDs;
- attempt IDs;
- checkpoint IDs;

owned by subject B.

## CT6 — Runtime/identity mismatch is detectable

Test at least two distinguishable failure cases:

1. requested subject does not exist in the current runtime;
2. integration expects a different configured runtime identity/fingerprint than the server reports, if runtime-instance checking is implemented.

The result must not masquerade as authoritative “learner has no history.”

A bounded explicit diagnostic/error is acceptable.

## CT7 — Restart preserves continuity

Create checkpoint/evidence continuity state, close service, reopen service, then assert identical semantic continuity result apart from fields that are explicitly runtime-generated/noncanonical.

## CT8 — Backup/restore preserves continuity

For both:

- checkpoint-backed continuity;
- evidence-only continuity;

backup, restore, and assert equivalent results plus healthy doctor state.

## CT9 — Source artifact integrity remains valid

After continuity reads:

- no message/artifact content is mutated;
- every message artifact reference resolves;
- every content SHA agrees;
- continuity access is read-only.

Corrupt a disposable fixture and prove `doctor` still detects the corruption rather than continuity hiding it.

## CT10 — Real GPT fresh-chat continuity

This is a manual/live acceptance test and cannot be replaced by synthetic HTTP.

Procedure:

1. verify the Study OS GPT is configured for the intended live runtime;
2. verify the stable real learner `subject_id`;
3. in GPT conversation A, perform a small distinctive learning interaction;
4. verify its durable source evidence locally;
5. open a fresh Study OS GPT conversation B;
6. ask what was being studied previously;
7. Study OS must recover useful context grounded in the durable evidence/checkpoint;
8. record IDs/hashes/timestamps only in public verification artifacts; do not publish raw private text.

Pass requires evidence that conversation B queried the same real learner identity/runtime and recovered context from Study OS, not from ChatGPT conversation memory alone.

## CT11 — Real GPT user turn is durably stored

In the real Study OS GPT:

1. send a distinctive user turn;
2. identify the corresponding `append_conversation_turn` durable result or local record;
3. verify one `messages` row with role `user`;
4. verify backing `raw_artifacts` row and SHA;
5. verify private artifact bytes equal the actual user content;
6. verify no duplicate on retry/repeated transport result.

Pass requires the live GPT path, not a manual curl/local `/actions` call.

## CT12 — Exact real GPT assistant response is durably stored

In the real Study OS GPT:

1. capture the assistant response actually displayed to the learner;
2. verify one `messages` row with role `assistant`;
3. verify backing private artifact;
4. verify stored bytes exactly equal the displayed assistant response for the tested turn;
5. verify the stored response was committed before or as part of the integration sequence required by the PDD/SDD;
6. if the integration cannot guarantee this, test must remain blocked rather than be downgraded to synthetic evidence.

## Regression requirements

After implementation, run:

```text
python -m unittest discover -s tests -v
python tools/validate_repo.py
python tools/check_engineering_baseline.py
```

Also rerun the source-turn durability suite including ST1–ST21 and retain ST22 status until CT10–CT12 prove the real GPT path.

## `/actions` semantic-error regression

Add focused tests proving `/actions` preserves at least:

```text
validation_error
not_found
conflict
integrity_error
```

when raised by Study OS semantics, while unexpected exceptions become `internal_error`.

## Historical reconciliation verification

Where a private historical transcript is available, perform reconciliation only after backup and only with reviewed source input.

Verify:

- existing structured attempts/events/checkpoints remain unchanged;
- only missing source turns are added;
- rerun is idempotent;
- source/live vs reconciliation origin is preserved;
- ambiguity is review-required;
- no public raw transcript is created.

Historical reconciliation is not required to make CT1–CT9 green on synthetic data, but it is required to repair real gaps where source material is available.

## Completion report

Luna must report:

```text
implementation SHA
schema migration: yes/no
live runtime root
stable real subject_id policy
files changed
CT1–CT12 results
ST1–ST22 results
full test count/result
doctor result
backup/restore result
real GPT capture IDs/hashes (no private content)
real GPT fresh-chat continuity result
historical reconciliation performed/pending
known limitations
```

Do not close #56 or #59 while CT10–CT12 remain blocked.
