# Error and Idempotency Contract — Study OS v0.1

This contract defines predictable behavior for local service and MCP operations so retries, model/tool-call repetition, and partial failures do not corrupt longitudinal learner data.

## Stable error categories

Every semantic operation should map failures to one of:

- `validation_error` — malformed/missing/unsupported input field;
- `not_found` — referenced subject/session/evidence/checkpoint does not exist;
- `conflict` — request conflicts with existing durable state, including idempotency-key reuse with different content;
- `integrity_error` — provenance/hash/checkpoint/foreign-key invariant failure;
- `unsupported_version` — schema/contract/runtime version mismatch;
- `unavailable` — required local resource temporarily unavailable/locked;
- `internal_error` — unexpected implementation failure.

Do not return a successful-looking payload when persistence failed.

## Error payload minimum

Machine-facing failures should contain at least:

```json
{
  "error": {
    "category": "validation_error",
    "message": "human-readable summary",
    "retryable": false,
    "details": {}
  }
}
```

`details` must not leak secrets/private transcript bodies by default.

## Retryability defaults

- `validation_error`: false
- `not_found`: false unless caller may legitimately wait for a preceding asynchronous/local operation
- `conflict`: false until caller changes request
- `integrity_error`: false; requires investigation/repair
- `unsupported_version`: false; requires upgrade/migration
- `unavailable`: true when transient (DB busy, temporary storage unavailable)
- `internal_error`: unspecified/false by default; retry only if caller has a bounded policy and idempotency key

## Idempotency requirement

Every durable mutating tool in `contracts/study-os-mcp-tools.v0.1.json` requires an `idempotency_key`.

Required semantics:

1. First valid request with a new key executes transactionally.
2. Durable result is associated with the key and a canonical request fingerprint/hash.
3. Exact retry returns the same logical resource/result without creating a duplicate.
4. Same key + materially different request returns `conflict`.
5. If the transaction fails before commit, the system must not report/create a successful idempotency record.
6. If response delivery fails after commit, a retry must recover the committed logical result.

## Canonical request fingerprint

Normalize the semantic request before hashing/fingerprinting. Exclude transport noise but include every field that changes the durable meaning of the request.

At minimum do not exclude:

- subject/session IDs;
- evidence class/event type;
- payload content;
- assessment result/assistance;
- representation family/operation/version;
- checkpoint capability/resume state;
- source/evidence IDs.

## Example retry case

A model/tool client submits:

```text
record_learning_event(idempotency_key="abc", event_type="confusion_reported", ...)
```

The DB commits but the network response is lost.

Client retries the same request with `abc`.

Expected: return the existing `event_id`; no second event row.

## Example conflicting retry

First request:

```text
key=abc, event_type=confusion_reported
```

Second request:

```text
key=abc, event_type=assessment_passed
```

Expected: `conflict`; never silently reinterpret/reuse the key.

## Atomic checkpoint rule

Checkpoint creation has an additional requirement:

```text
validate evidence/state
  -> insert immutable checkpoint
  -> update subject current pointer
  -> commit
```

All in one transaction.

After any crash/interruption, either:

- old checkpoint remains current and new checkpoint does not exist/was not accepted; or
- new checkpoint exists and is current.

Do not allow a committed new checkpoint with a partially advanced/inconsistent current pointer unless explicitly modeled as `proposed` and not accepted.

## Concurrency

For v0.1/single-user SQLite, avoid unnecessary complexity, but correctness still requires:

- transaction boundaries;
- bounded handling of `database is locked`/busy conditions;
- idempotency on retries;
- no lost update on current checkpoint pointer.

If multiple tutor sessions try to checkpoint the same subject concurrently, one must win deterministically or the second must receive a `conflict`; silent last-write-wins is not acceptable for learner-state history.

## Logging

Log:

- operation name;
- request/idempotency key;
- resource IDs;
- error category;
- timing;
- retry count where known.

Avoid logging full private transcript/event bodies unless explicitly enabled for local debugging.

## Test requirements

Luna must include tests for:

- exact duplicate retry;
- conflicting idempotency reuse;
- response-loss simulation/retry after commit where practical;
- checkpoint atomicity;
- concurrent/stale checkpoint update behavior;
- transient unavailable error behavior;
- malformed payload validation mapping.
