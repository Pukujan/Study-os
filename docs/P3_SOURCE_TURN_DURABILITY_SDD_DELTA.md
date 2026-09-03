# P3.0 Source-Turn Durability — System Design Delta

Status: accepted implementation specification once merged

Parent tracker: #52

Focused issue: #56

Extends: `docs/P3_DURABLE_EVIDENCE_CAPTURE_SDD.md`

Companion product delta: `docs/P3_SOURCE_TURN_DURABILITY_PDD_DELTA.md`

Date: 2026-09-03

## 1. Design conclusion from the current repository

Study OS does **not** need a new transcript database for the first repair.

The initial schema already contains the correct durable primitives:

- `raw_artifacts` — immutable private evidence metadata;
- `messages` — per-session message occurrence records with `role`, `artifact_id`, `content_sha256`, `created_at`, and extensible `metadata_json`;
- `idempotency_records` — durable operation identity/fingerprint/result mapping;
- `EvidenceStore` — private immutable file capture with SHA-256 verification;
- backup/restore support that already includes the evidence root.

The current runtime already exposes `capture_evidence`, but that operation stores a raw artifact only. It does not create a message occurrence, has no append-turn idempotency contract, and is not part of the GPT-facing semantic MCP surface.

Therefore the preferred MVP is:

> Reuse the existing `raw_artifacts` + `messages` + `idempotency_records` architecture and add the missing semantic source-turn operation. Do not add a migration unless implementation proves the existing schema cannot satisfy a required invariant.

## 2. Preferred application/runtime operation

Add one canonical application/runtime operation with semantics equivalent to:

`append_conversation_turn`

### Required inputs

```text
idempotency_key
session_id
subject_id
role
content
source_conversation_ref? 
source_message_ref?
source_parent_ref?
source_timestamp?
source_sequence?
source_client?
```

`role` must support at least `user` and `assistant` for the first implementation.

`content` is the exact learner-facing UTF-8 string supplied to Study OS for this turn. Empty content is rejected unless a future explicit non-text turn contract is added.

Optional source fields are provenance. They are never invented when unavailable.

### Required result

```text
message_id
artifact_id
sha256
created
capture_origin
local_captured_at
```

Exact field names may follow existing application-contract conventions, but these semantics must be available.

## 3. Storage mapping

### 3.1 Immutable content

Store exact turn bytes in the existing private evidence store.

For MCP string input:

```text
turn_bytes = UTF-8(content)
sha256 = SHA256(turn_bytes)
```

Create one `raw_artifacts` record referencing the immutable evidence-store path.

Recommended `capture_method` values:

```text
conversation_turn_live
conversation_turn_reconciliation
```

### 3.2 Message occurrence

Create one `messages` row per turn occurrence.

Mapping:

```text
message_id          -> stable local occurrence ID
session_id          -> existing Study OS session
role                -> user | assistant
artifact_id         -> raw_artifacts.artifact_id
content_sha256      -> exact raw artifact hash
created_at          -> actual local durable capture time
metadata_json       -> source/reconciliation provenance
```

### 3.3 Message metadata

`metadata_json` should carry versioned occurrence/provenance metadata such as:

```json
{
  "metadata_version": "study-os.source-turn.v1",
  "capture_origin": "live",
  "source_client": "chatgpt",
  "source_conversation_ref": null,
  "source_message_ref": null,
  "source_parent_ref": null,
  "source_timestamp": null,
  "source_sequence": null,
  "reconciliation_source_ref": null
}
```

For backfill, set `capture_origin = reconciliation` and preserve an immutable source/transcript artifact reference or equivalent provenance identifier.

Do not overload `created_at` with source time.

## 4. Identity model

### 4.1 Local identity

`message_id` is the authoritative local occurrence identity.

It does not have to equal a ChatGPT/platform message ID.

### 4.2 Source identity

When available, preserve external conversation/message identifiers in message metadata.

External IDs are provenance and reconciliation evidence, not the sole local primary key.

### 4.3 Idempotency identity

Use `idempotency_records` with operation name equivalent to:

`append_conversation_turn`

Fingerprint all fields that define the logical append request, including at minimum:

```text
session_id
subject_id
role
content hash
source conversation/message refs when supplied
source timestamp/sequence when supplied
capture origin
```

Rules remain:

```text
same key + same fingerprint
    -> return original message/artifact result

same key + different fingerprint
    -> conflict; no mutation
```

Repeated identical text with a **different** idempotency key is a different message occurrence and is allowed.

## 5. Write protocol

Preferred live append sequence:

```text
1. validate minimal request envelope
2. open SQLite transaction
3. check idempotency record
4. validate session belongs to subject
5. generate local message_id + artifact_id
6. write immutable evidence bytes using EvidenceStore
7. insert raw_artifacts row
8. insert messages row
9. insert idempotency record containing final result
10. commit SQLite transaction
11. only after commit return durable success
```

The existing evidence store is filesystem-backed rather than transactionally coupled to SQLite. Preserve the current compensation pattern on ordinary exceptions: if the file was written but the DB transaction fails, remove the uncommitted file when safe.

A process crash can still leave an unreferenced private artifact between filesystem replacement and SQLite commit. Such an orphan is **not canonical message evidence** because no `raw_artifacts/messages` commit exists. The exact retry may create one new canonical artifact/message. `doctor` should be able to detect unreferenced/orphan evidence files if this failure is practically observable.

Do not falsely treat an orphan file as a committed message.

## 6. Post-commit unknown-result behavior

The append operation must use the same commit-before-ack rule as the parent P3 design.

If SQLite commits the artifact row, message row, and idempotency result but transport fails before the caller receives success:

```text
retry same key/fingerprint
    -> idempotency lookup
    -> original message_id/artifact_id/result
    -> no duplicate message
```

This is mandatory because the original incident involved caller-visible 502/unknown-result behavior.

## 7. Semantic processing boundary

`append_conversation_turn` performs **source capture only**.

It does not require:

- event classification;
- attempt detection;
- learner-state update;
- failure-signature inference;
- intervention grading.

Those operations may run after source capture and should reference the message/artifact evidence where supported.

A downstream failure therefore leaves the source turn intact.

## 8. MCP surface decision

The current MCP v0.1 contract contains exactly 13 semantic tools and has no turn-append operation.

Issue #56 authorizes one bounded semantic addition because the current surface cannot satisfy the already-accepted Study OS transcript/source ownership decision without abusing `record_learning_event` or exposing generic file mutation.

Preferred GPT-facing operation:

`append_conversation_turn`

Implementation should:

1. add canonical application request/result contracts;
2. add the runtime-port/application-service operation;
3. project it through MCP;
4. version the MCP contract rather than silently altering the meaning of v0.1;
5. update exact-tool-count/schema/public-surface tests to the new version;
6. preserve all existing 13 tool semantics unchanged.

Recommended semantic version: MCP contract `0.2.0`, because one backward-compatible capability is added.

The exact file/version update should follow existing repository contract conventions.

No generic transcript DB read/write shell is authorized.

## 9. GPT integration protocol

After the new MCP capability is deployed, the Study OS GPT configuration/instructions should use it as follows:

### Learner turn

Before deriving structured learning semantics, append the learner's current turn.

### Assistant turn

After composing the learner-facing response but before final emission when the product harness allows it, append that planned response and then emit the same text.

If append fails because Study OS is unavailable:

- do not claim local durability;
- still allow the tutor to respond so studying can continue;
- retain the interaction in the conversation source for later reconciliation;
- mark/remember the session as reconciliation-required where the harness permits.

The local runtime cannot guarantee data for a turn it never receives.

## 10. Reconciliation design

Reconciliation should reuse the same internal append semantics with `capture_origin = reconciliation` rather than maintaining a second data model.

### 10.1 First recovery surface

Prefer a local reviewed CLI/tooling path for the first implementation.

A new GPT-facing reconciliation MCP tool is **not required** for Issue #56.

### 10.2 Input

The recovery workflow begins from actual private source evidence such as:

- original/exported transcript;
- user-preserved lossless Markdown transcript;
- platform export with message IDs;
- existing immutable Study OS raw transcript artifact.

Preserve/hash the source artifact before deriving turns.

### 10.3 Matching order

```text
1. exact source conversation + message ID
2. exact local/source correlation identity
3. role + content hash + adjacent stable IDs
4. role + content hash + chronology/source sequence
5. manual review if more than one plausible match remains
```

### 10.4 Outcomes

```text
already_present_exact
backfilled_missing
ambiguous_review_required
rejected_invalid_source
```

A backfilled message gets:

- original/source metadata where available;
- actual local recovery `created_at`;
- `capture_origin = reconciliation`;
- source transcript/artifact provenance.

Reconciliation never edits a live-captured message to pretend it was recovered or vice versa.

## 11. Read/query needs

Issue #56 does not require another public MCP read tool.

Local/runtime code must nevertheless be able to enumerate a session's message occurrences for:

- reconciliation matching;
- diagnostics;
- tests;
- backup/restore verification.

Use an internal repository/service query or bounded local CLI surface.

A future learner-facing transcript viewer can be designed later.

## 12. `doctor` delta

Add checks only where needed for source-turn integrity:

- every message artifact reference resolves;
- every `content_sha256` agrees with the referenced artifact hash;
- duplicate/conflicting idempotency state does not exist;
- message metadata is valid enough for the declared metadata version;
- reconciliation records do not reference missing source artifacts;
- unreferenced evidence-store files are reported if the implementation can observe them reliably;
- unresolved/ambiguous reconciliation state is visible.

`doctor` reports; it does not rewrite history.

## 13. Backup/restore delta

Existing backup already includes SQLite plus the private evidence root.

Extend verification to prove that after restore:

- `messages` rows remain;
- `raw_artifacts` rows remain;
- evidence files verify against SHA-256;
- message -> artifact links remain valid;
- idempotent append retry returns the original message result;
- reconciliation provenance remains intact.

No separate transcript backup mechanism should be introduced unless the existing backup path cannot preserve these assets.

## 14. Migration decision

**Default implementation target: no migration.**

The current schema can represent the MVP source-turn record through `raw_artifacts`, `messages`, `metadata_json`, and `idempotency_records`.

Luna may introduce a migration only if tests demonstrate a missing invariant that cannot safely be enforced in the existing schema. Examples could include a required uniqueness constraint that application/idempotency logic cannot safely guarantee.

If a migration is proposed, Luna must explain why the existing schema is insufficient before writing it.

## 15. Compatibility decision

Existing learning events, attempts, assessments, interventions, checkpoints, retention probes, and FOSSIL exports retain their current semantics.

`record_learning_event` must **not** be redefined to mean raw transcript append.

Existing `capture_evidence` remains useful as a lower-level runtime helper but is not itself the new public semantic contract.

## 16. Rollout sequence

```text
A. add source-turn application/runtime tests
B. implement append operation using existing schema
C. add application/MCP contract v0.2 projection
D. verify post-commit retry + restart
E. add local reviewed reconciliation path
F. extend doctor + backup/restore checks
G. synthetic MCP smoke
H. update GPT instructions/config for live append
I. real two-turn GPT smoke
J. reconcile known outage transcript after live path is trustworthy
```

## 17. Stop conditions

Luna should stop and report if:

- existing local data/schema differs materially from repository `main`;
- the current GPT/app platform cannot invoke the new semantic tool at all;
- safe raw turn content cannot be kept inside the accepted private evidence boundary;
- implementing append requires destructive migration without verified backup;
- reconciliation identity is ambiguous;
- a proposed shortcut would store only derived summaries rather than source evidence.

## 18. Architectural result

After Issue #56, the intended durable chain is:

```text
GPT learner/user or assistant turn
        ↓
append_conversation_turn
        ↓
EvidenceStore immutable bytes
        +
raw_artifacts metadata
        +
messages occurrence
        +
idempotency result
        ↓
optional semantic learning operations
        ↓
derived learner/system state
```

That chain makes the existing Study OS data architecture operational rather than inventing a second transcript system.
