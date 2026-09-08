# P4 Test Design — Prerequisite-Sensitive Remediation

Date: 2026-09-07
Status: focused verification delta
Parent specs:

- `docs/P4_PREREQUISITE_REMEDIATION_PDD.md`
- `docs/P4_PREREQUISITE_REMEDIATION_SDD.md`

## Verification objective

Prove that learner confusion about a required representation does not silently become a canonical parent-task failure and that any prerequisite traversal remains deterministic, bounded by the canonical graph, and auditable by module/prompt/schema version.

Primary public-safe regression fixture:

`tests/fixtures/p4_mutation_lab_representation_failure.v0.1.json`

The fixture is a curated summary, not a raw private transcript.

## Invariant matrix

| ID | Invariant | Threat | Required evidence |
| --- | --- | --- | --- |
| PR-001 | Diagnosis is derived/non-authoritative | model output directly advances learner | strict schema/parser contains no progression authority; controller remains separate |
| PR-002 | Parent confusion is not a canonical incorrect attempt | transcript language is graded as failure | proposal marks parent attempt recording forbidden until behavioral parent probe |
| PR-003 | Parent progression remains blocked during remediation | tutor/model skips ahead | deterministic proposal reports `progression_blocked=true` |
| PR-004 | Prerequisite target comes only from canonical graph | model invents a concept | suspected IDs cannot authorize a non-canonical prerequisite |
| PR-005 | Ambiguous prerequisite diagnosis fails closed | controller guesses among multiple missing prerequisites | no selected action; diagnostic probe required |
| PR-006 | Representation-only failure preserves target competency | visual rewrite changes skill | same parent target retained |
| PR-007 | Assistance remains bounded | remediation self-escalates | selected assistance never exceeds supplied ceiling |
| PR-008 | Representation intent is structured | “chart” becomes unconstrained prose | family/roles/structure/forbidden/code/granularity surfaced in policy output |
| PR-009 | Representation policy cannot switch task/competency | renderer bypasses upstream controller | existing hard gates remain active |
| PR-010 | Same canonical inputs replay identically | hidden stochastic controller behavior | exact DecisionProposal equality on repeat |
| PR-011 | Prompt/schema evolution is explicit | hidden prompt drift | exact prompt/schema versions pinned in proposal and controller evidence |
| PR-012 | Raw-problem compilation remains deferred | remediation feature becomes generic live compiler | no compiler/live graph-authority implementation in this slice |

## Focused unit tests

File:

`tests/test_p4_prerequisite_remediation.py`

Required cases:

1. **Mutation-lab regression routes to prerequisite**
   - three prerequisites initially unproven;
   - structured diagnosis suspects comparison semantics;
   - controller selects that exact canonical prerequisite;
   - parent progression remains blocked;
   - required next evidence is a behavioral micro-probe.

2. **Confusion is not parent failure**
   - no canonical parent attempt is authorized merely from the confusion statement;
   - parent probe remains pending.

3. **Diagnosis parser is strict/versioned**
   - unknown authority-like field such as `can_advance` is rejected;
   - schema and prompt versions are exact.

4. **Ambiguous missing prerequisite fails closed**
   - multiple prerequisites unproven;
   - hypothesis names none;
   - controller selects none and asks for diagnostic evidence.

5. **Representation-only remediation keeps parent target**
   - no missing-prerequisite hypothesis;
   - representation interference present;
   - operation changes representation but target competency is unchanged.

6. **Visual intent reaches renderer envelope**
   - decision-tree representation is semantically validated;
   - output contains semantic roles;
   - explicit boundary structure is required;
   - source-code-primary/dense-table-primary are forbidden;
   - code visibility is hidden;
   - interaction granularity is a single probe.

7. **Deterministic replay**
   - identical canonical inputs produce identical serialized proposals.

## Additional negative cases before live promotion

The focused branch should later add or reuse tests proving:

- hypothesis references a competency not present in canonical prerequisites → cannot traverse there;
- hypothesis references an already-independent prerequisite while a different prerequisite is missing → fail closed rather than silently retarget;
- representation candidate uses different task → excluded;
- representation candidate uses different competency → excluded;
- representation semantic validation false → excluded;
- requested representation exceeds assistance ceiling → excluded;
- malformed schema version → rejected;
- malformed prompt version → rejected;
- diagnosis without source evidence → rejected;
- rendering failure never drops source-turn durability.

## Persistence / evidence test for later live authority

Before promoting this path beyond shadow/advisory mode, add an integration test that records:

```text
observed learner difficulty event
→ derived DiagnosisProposal
→ derived controller DecisionProposal
→ learner-facing representation turn
→ observed behavioral micro-probe response
```

and proves no parent `INCORRECT`/canonical attempt row is fabricated before the behavioral parent probe.

This persistence test should reuse existing evidence tables and service boundaries rather than introduce a parallel transcript store.

## Prompt/schema contract checks

Validate that:

- `schemas/p4-diagnosis-proposal.schema.json` parses as JSON;
- schema uses `additionalProperties: false` at the proposal and nested structured objects;
- prompt explicitly forbids progression/mastery authority;
- prompt instructs uncertain/mixed output instead of forced certainty;
- prompt requires canonical prerequisite IDs supplied by caller;
- prompt treats syntax/visual confusion as possible representation evidence.

## Repository checks

Minimum focused commands when run locally:

```bash
PYTHONPATH=src python -m unittest tests.test_p4_prerequisite_remediation -v
python -m compileall src/study_os/adaptive tests/test_p4_prerequisite_remediation.py
python -m ruff check src/study_os/adaptive tests/test_p4_prerequisite_remediation.py
python -m pyright src/study_os/adaptive
python tools/validate_repo.py
```

Normal pull-request CI remains the independent clean-environment attestation.

## Acceptance boundary

Passing these tests establishes:

- deterministic routing correctness for the represented cases;
- explicit diagnosis/prompt/schema provenance;
- bounded representation intent;
- protection against grading pre-probe confusion as a parent failure.

It does **not** establish:

- that a decision tree is universally the best representation;
- that the diagnosis model is empirically calibrated;
- that the intervention caused learning improvement;
- that arbitrary raw-problem compilation is safe;
- population-level efficacy.
