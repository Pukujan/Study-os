# All-DSA generic model tutoring — Test Design Document

Status: test plan for the generic 14-problem proof. Existing unit and pilot
tests cover part of the foundation; the generic full-corpus runner, evaluator,
metamorphic suite, and real acceptance execution are pending.

## Test principles

- Test deterministic authority before judging model prose.
- Compare semantic behavior and required properties, not exact generated
  wording.
- Keep `observed`, `self_reported`, and `derived` fields separate.
- Use model stubs/fixtures for deterministic unit tests; use real local Luna only
  for the explicit acceptance runs.
- Keep hidden calibration expectations in the evaluator process, never in the
  teacher prompt or learner-visible output.
- A full-corpus pass requires every problem to pass individually; aggregate rate
  is not a compensating score.

## Fixtures and test lanes

| Fixture/lane | Purpose |
| --- | --- |
| `tests/test_teaching_plan.py` synthetic payload | Plan schema, cross-record semantics, immutability, and provenance. |
| `tests/test_generic_model_tutoring.py` synthetic plan | Generic controller, contracts, evidence, assistance, provenance, and response boundary. |
| `tests/test_model_tutoring_pilot.py` | Historical one-problem regression, including semantic `box` behavior and pilot metamorphic/stateful checks. |
| `tests/test_model_tutoring_acceptance.py` | Historical Contains Duplicate calibrated checker contract and negative controls. |
| `tests/test_model_tutoring_mutation_contract.py` | Historical pilot authority-boundary mutation tests. Generic equivalents are required. |
| `datasets/dsa-conversation-replay.v0.1.json` | Public 14-scenario/210-turn input. Its hidden `expected` assertions are evaluator-only. |
| Redacted plan/trace fixtures | One valid and one invalid plan/trace per representative structural failure; no private transcript. |
| Metamorphic fixture generator | Paraphrases, numeric substitutions, equivalent statements, altered examples, and wrong/uncertain phrasings. |

## Unit and contract matrix

| ID | Target | Concrete test | Expected result | Status |
| --- | --- | --- | --- | --- |
| U-TP-01 | `TeachingPlan.from_payload` | Load a valid v0.1 payload, round-trip with `to_payload`, and validate against `contracts/teaching-plan.v0.1.schema.json`. | Structural and cross-record validation succeeds; payload is equivalent. | Existing foundation test |
| U-TP-02 | Plan immutability | Mutate the source payload after construction and attempt to mutate nested plan/provenance values. | Stored plan remains unchanged; frozen/mapping-proxy guards reject mutation. | Existing foundation test |
| U-TP-03 | Plan references | Remove a variable, representation, invariant, or evidence reference; duplicate an ID; or add an unreferenced invariant/evidence record. | `TeachingPlanValidationError`. | Existing/extend coverage |
| U-TP-04 | Prerequisite graph | Add an unknown prerequisite, a cycle, or reorder concepts so ordered concepts violate prerequisites. | Plan or controller construction rejects the case. | Existing foundation test |
| U-TP-05 | Plan provenance | Change source problem ID, plan schema version, or prompt hash shape. | Rejected; source and schema identity must match. | Existing foundation test |
| U-PR-01 | `PromptDefinition` | Create a definition and recompute its UTF-8 SHA-256 content hash. | Stored hash equals content digest. | Existing code; add direct test if needed |
| U-PR-02 | `PromptRegistry` immutability | Register a candidate, reuse a version, resolve by role, and verify a wrong hash. | Registration returns a new registry; version reuse/hash mismatch reject. | Existing code; extend |
| U-PR-03 | Prompt provenance | Build provenance for decomposition, diagnosis, and generation roles. | Version/hash/model/schema/run/source fields remain present and resolvable. | Pending generic lifecycle test |
| U-GM-01 | Decision parser | Parse valid JSON, fenced JSON, aliases, missing fields, invalid JSON, and non-object JSON. | Valid forms parse; malformed forms reject without state change. | Partial existing coverage |
| U-GM-02 | Evidence binding | Use a demonstrated assessment with an exact learner substring, a fabricated quote, an empty quote, and a non-demonstrated outcome. | Only demonstrated + verbatim quote is eligible; fabricated/empty demonstrated evidence rejects. | Existing generic/pilot tests |
| U-GM-03 | State progression | Authorize `not_yet`, `uncertain`, and `demonstrated` outcomes from each concept. | No advance unless demonstrated; advance is at most one concept; final concept does not advance to mastery. | Existing generic tests; expand |
| U-GM-04 | Assistance ceiling | Request A0/A1/A2 under each plan ceiling and request A3. | Requests above the plan ceiling or unknown levels reject. | Existing generic/pilot tests |
| U-GM-05 | Contract binding | Inspect a returned `GenerationContract`. | Active concept, allowed variables, representations, invariants, completion evidence, terminal behavior, and plan provenance exactly match the plan. | Existing generic test; expand |
| U-GM-06 | Prompt construction | Build generation prompt with six-plus history items and a registered/wrong prompt hash. | Only bounded history is included; valid provenance resolves; wrong provenance rejects. | Partial existing coverage |
| U-GM-07 | Response parser/boundary | Test empty, over-character, over-line, internal-marker, missing-representation, and forbidden-variable responses. | `validate_generated_response` rejects each invalid response and never creates replacement prose. | Existing generic tests; expand |
| U-GM-08 | Trace shape | Serialize a generic authorization trace and validate it against the chosen generic trace schema. | Required fields, `model_generated`, evidence, state, plan identity, prompt identity, and source identity are present. | Pending schema alignment |
| U-GM-09 | Cross-scenario isolation | Construct controllers for two plans and interleave authorizations. | State, active concept, variables, and provenance never bleed between runs. | Pending |

## Differential and calibrated matrix

These tests use a trusted, evaluator-only semantic representation of each
scenario. They must not require exact model prose, exact concept IDs, or a
particular variable alias unless the plan/fixture explicitly requires that
binding.

| ID | Scope | Concrete comparison | Expected result | Status |
| --- | --- | --- | --- | --- |
| D-01 | Plan semantics | For each of 14 plans, compare source identity, concept prerequisite order, variable roles/meanings, required representations, invariants, completion evidence, terminal behavior, and assistance ceiling to a calibrated oracle. | Semantic agreement; no missing required contract. | Pending all-DSA evaluator |
| D-02 | Per-turn control | For each of the 15 learner turns, compare active concept, allowed variables, assistance, operation class, advancement, and evidence binding to the current state and actual learner message. | No skipped prerequisite, unsupported advance, role drift, or evidence fabrication. | Pending generic evaluator |
| D-03 | Visible stage behavior | Compare each teacher response to stage-level required anchors, representation presence, question/back-and-forth rule, output budget, forbidden future terms, and terminal/base condition. | Semantic requirements pass without exact prose matching. | Existing only for Contains Duplicate; all-DSA pending |
| D-04 | Semantic regression | Inject the Contains Duplicate `box` boolean-result mistake. | Failure includes the existing box-semantic regression category; `box` remains earlier values. | Existing pilot test; preserve in generic suite |
| D-05 | Generic path identity | Inspect every plan/trace/transcript row and source diff. | All rows identify the model-generated path; no canonical asset/`needs_compilation` leakage or new per-problem controller/lesson. | Pending full runner/checker |
| D-06 | Prompt differential | Run candidate prompt versions against all 14 scenarios and the same deterministic fixtures. | Report per-problem validity, semantic agreement, progression, leakage, assistance, and failure categories; candidate is promotable only if non-regressive and no severe per-problem regression. | Pending prompt-evaluation runner |
| D-07 | Independent oracle boundary | Capture the teacher prompt/input and inspect for `expected` assertions, hidden answers, or evaluator-only fields. | Hidden calibration material is absent from teacher input. | Pending runner boundary test |

## Metamorphic paraphrase and numeric matrix

Each metamorphic case is evaluated against the same stateful policy, not against
the same prose. Where a transformation changes the semantic problem, it must be
classified as a new fixture rather than silently accepted.

| ID | Transformation | Invariant to assert | Status |
| --- | --- | --- | --- |
| M-01 | Paraphrase a learner clarification (“what is this?”, “I’m lost here”, “can you slow down?”). | Same active concept and no unsupported advance; diagnosis may vary only within the allowed generic contract. | Partial pilot coverage; generic pending |
| M-02 | Paraphrase a demonstrated explanation while preserving its meaning. | Evidence quote is still drawn from the actual message; progression policy is unchanged. | Pending |
| M-03 | Rephrase a wrong answer or uncertainty using different words. | Outcome is not upgraded by surface wording; no evidence-free advance. | Pending |
| M-04 | Substitute numeric values/examples while preserving the algorithmic relation. | Concept order, variable roles, invariants, representation family, and operation policy remain stable. | Pending |
| M-05 | Rephrase the problem statement with an equivalent surface form. | Plan semantics agree with the calibrated problem family; no memorized fixed wording dependency. | Pending |
| M-06 | Change harmless example sizes, labels, or values. | No arbitrary change to progression, assistance, or terminal behavior. | Pending |
| M-07 | Use an equivalent representation where the plan marks it allowed. | Representation family/operation remains contract-compliant; forbidden role/alias and invariant drift still fail. | Pending |

The existing pilot has a small paraphrase-policy test and numeric examples in
fixtures, but it is not a 14-problem metamorphic evaluation. That broader lane
is pending.

## Property and stateful matrix

Use seeded property generation so failures are reproducible. A generated plan
must first satisfy the plan contract; invalid plans are separate negative
fixtures.

| ID | Generated sequence/input | Property | Status |
| --- | --- | --- | --- |
| P-01 | Random valid/invalid outcome sequences over a plan’s concepts. | State never skips, backtracks, or advances more than one concept; advancement requires `demonstrated`. | Existing pilot/generic partial; expand |
| P-02 | Random learner messages with fabricated, empty, case/spacing-altered, or unrelated evidence quotes. | No fabricated evidence becomes demonstrated evidence. | Existing partial; generic expansion pending |
| P-03 | Random assistance levels against A0/A1/A2 plans. | Assistance overflow always rejects and never commits state. | Existing partial |
| P-04 | Random valid prerequisite DAGs plus cycle/reference mutations. | Valid ordered plans load; malformed references/cycles reject deterministically. | Partial; expand |
| P-05 | Interleaved representation and variable-binding contracts. | Required representation IDs and active concept variable bindings are preserved; out-of-scope variables cannot appear in accepted output. | Existing generic validator partial; expand |
| P-06 | Repeated `authorize` calls before commit and repeated commit attempts. | Uncommitted authorization does not mutate state; runner-level duplicate identity is rejected or idempotently replays the same record. | Controller half existing; runner idempotency pending |
| P-07 | Restart after every prefix of a 15-turn scenario. | Resume reconstructs exactly the validated prefix and produces no duplicate or conflicting evidence. | Pending runner |
| P-08 | Random model diagnosis/response failures. | Failed parse/validation causes no learner-visible partial output and no state advance. | Pending runner |
| P-09 | Random plan/model/prompt/run identities. | Traces preserve matching source, run, schema, prompt version/hash, and model identity. | Pending generic trace schema |
| P-10 | Two or more scenarios interleaved in one test process. | No plan/state/provenance cross-contamination. | Pending |
| P-11 | Generated model outcome claims on the final concept. | Final concept remains active and no mastery flag is synthesized. | Existing generic behavior; add property coverage |

## Mutation matrix

Mutation testing is a negative-control gate. Each mutant below must be killed by
the generic tests/evaluator; surviving mutants are failures of the test design,
not acceptable implementation variance.

| ID | Mutant | Killing assertion |
| --- | --- | --- |
| X-01 | Advance on `not_yet`/`uncertain` or on a scripted learner signal. | Stateful and differential tests require demonstrated outcome plus verbatim evidence. |
| X-02 | Advance two concepts in one authorization. | `next_state.concept_index - current` is never greater than one. |
| X-03 | Accept fabricated or paraphrased evidence as a demonstrated quote. | Quote must be present in the actual learner message. |
| X-04 | Remove the assistance-ceiling comparison or allow A3. | Overflow tests reject and do not commit. |
| X-05 | Mutate a variable’s semantic role or allow an out-of-scope alias. | Plan binding, visible-output, and trace continuity tests fail. |
| X-06 | Remove required representation validation. | Required-representation response mutants are rejected. |
| X-07 | Remove completion/base/terminal evidence. | Plan/visible terminal behavior tests fail. |
| X-08 | Remove prompt version/hash/schema/run/source provenance. | Trace/schema/provenance tests fail. |
| X-09 | Bypass `model_generated` path identity or substitute a canonical asset. | Generic-path acceptance fails. |
| X-10 | Permit `needs_compilation`, reviewed-asset, or internal routing text. | Learner-visible leakage test fails. |
| X-11 | Permit final-concept advancement or model-derived mastery. | Final-state and no-mastery tests fail. |
| X-12 | Make retry append a duplicate or commit after failed generation. | Restart/idempotency and no-partial-response tests fail. |
| X-13 | Send hidden calibration assertions to the teacher. | Input-boundary test detects evaluator-only fields. |

The existing `tests/test_model_tutoring_mutation_contract.py` kills several
pilot mutants. It must not be treated as coverage of the generic all-DSA
mutation gate until it exercises `TeachingPlan` and
`GenericModelTutoringController`.

## Real acceptance matrix

These tests require the pending runner and local model integration. They are not
replaced by synthetic teacher responses.

| ID | Run | Pass condition | Status |
| --- | --- | --- | --- |
| A-01 | Per-problem run | Run each of the 14 scenarios through the same generic model/schema/controller path for exactly 15 exchanges. | Pending |
| A-02 | Aggregate run | Produce 14×15 = 210 exchanges and 420 nonempty learner-visible messages. | Pending |
| A-03 | Plan artifacts | Persist fourteen schema-valid plans with immutable plan provenance and source-problem identity. | Pending |
| A-04 | Turn artifacts | Persist 210 generic, schema-valid traces and corresponding transcript rows; every turn has prompt/model/schema/run/source provenance. | Pending |
| A-05 | Per-problem evaluator | Each problem has zero fatal failures for progression, variables, representations, assistance, semantic invariants, terminal behavior, leakage, and provenance. | Pending |
| A-06 | No masking | The aggregate report fails if any one of fourteen problem reports fails, regardless of aggregate percentage. | Pending |
| A-07 | Genericity review | Static/code review finds no new per-problem canonical lesson, stage table, or controller branch; all rows use the generic generated path. | Pending |
| A-08 | Prompt regression | Candidate prompt report covers all fourteen plus metamorphic variants and records per-problem non-regression. | Pending |
| A-09 | Recovery | Interrupt and resume at every turn boundary without duplicate evidence or changed prior output. | Pending |
| A-10 | Manual review | Review final plans, traces, transcripts, failure report, prompt report, and data-boundary receipt. | Pending |

## Required validation sequence

The repository’s baseline checks remain the required pre-acceptance checks:

```bash
python -m compileall tools tests
python tools/validate_repo.py
python -m unittest discover -s tests -v
```

The pending generic sequence then adds:

1. plan/schema and generic controller unit tests;
2. differential/calibrated tests over all fourteen scenarios;
3. metamorphic paraphrase, numeric, equivalent-statement, and wrong-answer
   tests;
4. seeded property/stateful and retry/resume tests;
5. mutation execution and survivor review;
6. prompt-version differential/regression evaluation;
7. one real 15-turn run per problem;
8. the complete 210-turn aggregate acceptance run; and
9. manual review of the final evidence.

The runner and evaluation steps above are explicitly pending. No artifact or
acceptance claim is created by this documentation-only change.

