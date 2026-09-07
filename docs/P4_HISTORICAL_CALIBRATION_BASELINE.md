# P4 Historical Calibration Baseline — From Reactive Corrections to Executable Pedagogy

Date: 2026-09-07
Status: proposed planning/evaluation baseline; subordinate to Issue #63, ADR-0016, and PR #73
Evidence source: frozen 2026-09-04 sliding-window pedagogy-calibration transcript + derived handoffs/goldens

## Purpose

Turn the strongest historical Study OS teaching evidence into a proactive product plan before making more learner-facing changes.

The key correction is methodological:

> Do not calibrate Luna by imitating Sol.
>
> Calibrate Study OS against the learner-approved repaired trajectory and the executable invariants extracted from it.

The archived Sol conversation is valuable precisely because it contains both successful teaching and repeated pedagogical failures. The learner repeatedly repaired those failures. Those repair boundaries are product requirements.

## Historical evidence read

The following frozen material was reviewed before defining this plan:

- `sessions/2026-09-04/sliding-window-pedagogy-calibration/raw/chat-visible-transcript-part01.md`
- `...part02.md`
- `...part03.md`
- `...part04.md`
- `...part05.md`
- `...part06.md`
- `...part07.md`
- `...part08.md`
- `sessions/2026-09-04/sliding-window-pedagogy-calibration/derived/pedagogy-findings.md`
- `sessions/2026-09-04/sliding-window-pedagogy-calibration/derived/resume-handoff.md`
- `sessions/2026-09-04/sliding-window-pedagogy-calibration/derived/next-session-analysis-handoff.md`
- `domains/dsa/sliding-window/golden/beginner-progressive-box-index-sum.v0.1.md`
- `domains/dsa/sliding-window/golden/beginner-sum-enumerate-append.v0.1.md`

The prior next-session handoff explicitly required raw-transcript-first analysis before more tutoring. This document follows that instruction.

## What the historical transcript actually proves

### 1. Sol was not the oracle

The successful trajectory was not produced by a consistently correct tutor. The model repeatedly:

- jumped from a working arithmetic relation to a full loop too early;
- compressed multiple new relationships into one turn;
- introduced code before symbol meanings were stable;
- dropped the learner-selected array/index/box representation;
- asked detached symbol exercises that did not test the active relation;
- advanced before the current bridge was stable;
- showed an answer/code line that the learner was supposed to produce;
- added prose after the visual already carried the meaning;
- changed charts unnecessarily;
- generalized from `S[0]`, `S[1]`, `S[2]` to `S[i]` too quickly;
- combined previously separate concepts before the learner had reconstructed the bridge.

The learner repeatedly corrected these failures and selected the repaired form.

Therefore:

```text
Sol output != gold
learner-approved repaired transition + preserved evidence = calibration source
```

Sol can remain a donor/reference candidate in differential evaluation. It must not be a grading authority.

### 2. The strongest pattern is a control-flow protocol, not a style preference

The recurring successful local protocol was:

```text
ONE ACTIVE RELATION
↓
guided representation
↓
one tiny exercise on that same relation
↓
remove answer-revealing cues
↓
learner event
↓
branch deterministically
↓
validate/correct in the same representation
↓
changed retry when needed
↓
verification after recovery
↓
only then introduce one next relation
```

This is not equivalent to "be concise" or "use visuals." It is a state machine with representation continuity and evidence gates.

### 3. Representation transitions were often harder than the underlying fact

The frozen handoff identifies the difficult points as bridges such as:

```text
value -> position -> index
box -> S[i]
S[i] -> S[i+1]
concrete neighboring sums -> recurrence
recurrence -> repeated recurrence -> loop
S[i] = expression -> S.append(expression)
S[0] -> S[i]
explicit S[1]/S[2] -> generalized S[i]
two loops -> one combined loop
if i != 0 -> else
first-window arithmetic -> range(k)
x changes -> same S[i] changes
```

This strongly supports making representation/decomposition bridges first-class nodes rather than assuming a semantically equivalent shortcut is pedagogically equivalent.

### 4. Charts/diagrams are part of semantic state

Historical evidence repeatedly establishes that the visual is not decoration.

Required behavior included:

- preserve array + index + box while the active relation depends on them;
- keep the same layout while teaching one relation;
- explanation/correction mode may include arrows/highlights;
- exercise mode must remove cues that reveal the answer;
- after an answer, validate using the same representation;
- restore the original representation before validating a derived/code result;
- show state changes over repeated turns instead of only a final result;
- prefer the visual relation over redundant prose when the diagram already communicates the semantics.

The current production `RepresentationSpec(learner_visible_markdown, visible_components)` is too weak to enforce this generic behavior.

### 5. "Small" is not sufficient; the probe must target the active relation

A historical failure asked a tiny question about `i` movement that was disconnected from the actual `sum[i] -> sum[i+1]` relation. The learner rejected it immediately.

Therefore exercise quality needs an explicit contract:

```text
active_relation
required_context
held_constant
changed_dimension
forbidden_neighboring_targets
answer_cue_policy
```

A one-line exercise that probes the wrong relation is still a controller failure.

### 6. Meta-feedback is not learner-performance evidence

The archived conversation mixes actual answers with pedagogy instructions, simulated errors, and statements about preferred presentation. Those must not mutate concept mastery or canonical assessment state.

At minimum distinguish:

```text
canonical_response_candidate
learner_difficulty_signal
clarification_or_meta_request
pedagogy_feedback
simulated_error_or_controller_test
```

Only a response valid for the active assessment contract may create the canonical attempt/outcome.

## Proactive cross-domain controller model

The next product slice should encode the following dimensions before trying to make Luna "more like Sol."

### A. Dependency/bridge graph

Each problem/concept path needs explicit nodes and edges for meaningful bridges.

A node is not just a topic label. It should specify:

```yaml
node_ref: string
target_relation: string
prerequisites: [string]
entry_evidence_requirements: [string]
allowed_operations: [string]
representation_intent_ref: string
exercise_contract_ref: string | null
advance_policy_ref: string
forbidden_future_relations: [string]
```

General unfamiliar-problem compilation remains deferred. For current reviewed/synthetic cases, use versioned accepted graphs only.

### B. Representation intent contract

Representation state should be semantic and validateable, not merely final Markdown.

Minimum conceptual fields:

```yaml
representation_intent_id: string
family: table | state_flow | sequence_trace | comparison_view |
        concrete_scenario | pseudocode | source_code | prose
mode: teach | exercise | correction | validation | restore
semantic_roles: [string]
required_relationships: [string]
required_state_variables: [string]
required_boundary_states: [string]
preserve_from_parent: [string]
answer_cues: allowed | forbidden
code_visibility: hidden | optional | secondary | primary | required
information_budget_ref: string
restorable_mapping: object | null
```

A response that uses prose/code when the active representation contract requires a visual/table/trace is a semantic contract failure, not a cosmetic difference.

### C. Information budget

Turn budget should be explicit enough to prevent both overload and under-specification.

Example policy shape:

```yaml
new_relations_max: 1
new_symbols_max: 1
max_explanatory_sentences: 2
questions_max: 1
required_components: [string]
forbidden_components: [string]
```

Budgets should vary by operation, not be a universal character limit.

### D. Exercise contract

Every probe declares exactly what it tests.

```yaml
exercise_target_relation: string
preserve_representation: true
held_constant: [string]
changed_dimension: [string]
answer_revealing_cues: forbidden
allowed_response_kinds: [string]
partial_suboperations: [string]
forbidden_targets: [string]
```

### E. Feedback/correction policy

Historical baseline:

```text
CORRECT
-> validate why in same representation
-> optional/required confirmation according to policy

PARTIAL
-> preserve correct sub-operation
-> isolate only missing operation

INCORRECT
-> correct in same representation
-> changed retry
-> if recovered, verify again before advance

DIFFICULTY/META
-> do not create canonical incorrect attempt
-> diagnose/reroute within authorized operations
```

### F. Output validator

Before a learner-facing turn is accepted, mechanically verify what can be verified:

```text
same required representation family?
required semantic roles present?
required relationships present?
answer cues obey mode?
forbidden future relations absent?
active exercise target preserved?
information budget satisfied?
code visibility policy satisfied?
canonical answer hidden?
progression authorized?
```

The model should regenerate or fail closed when a hard invariant fails.

## Mutation-testing trajectory: planned application

The recent failed local mutation-testing trajectory should be evaluated against the historical control model, not treated as a separate ad-hoc tutoring problem.

Observed learner event:

```text
"I don't know how the code works"
```

Expected control behavior:

```text
code-first parent concept
↓
learner difficulty evidence
↓
NO canonical incorrect parent attempt
↓
diagnosis hypotheses
  - missing_prerequisite
  - representation_interference
  - decomposition_too_coarse
↓
parent progression blocked if prerequisite resolution required
↓
authorized smaller_step / change_representation / show_trace
↓
code visibility becomes hidden or secondary
↓
semantic visual/table/state-flow/concrete representation
↓
micro-probe on prerequisite/bridge
↓
resolve or remain unresolved
↓
deterministic return/bridge toward source code
```

The visual should preserve the semantic target of the mutation/operator behavior while removing unrelated implementation complexity. It must not hard-code a single theater/ticket story.

## Luna–Sol differential calibration: revised authority

The differential harness should compare candidate realization quality under the exact same frozen controller state.

However, the target is now explicitly:

```text
historical learner-approved invariant set
+ reviewed graph/representation/exercise contracts
+ deterministic safety/progression rules
```

not Sol textual similarity.

For each frozen case collect:

- candidate model/provider/version;
- prompt/template version;
- authorized operation;
- requested representation intent;
- actual representation family realized;
- required semantic-role coverage;
- information-budget compliance;
- active-relation exercise compliance;
- answer leakage;
- unauthorized progression;
- partial-preservation behavior;
- correction/retry/verification behavior;
- restoration readiness;
- uncertainty handling.

Classify every failure as one or more of:

```text
GRAPH_OR_BRIDGE_DEFECT
ROUTING_DEFECT
REPRESENTATION_SELECTION_DEFECT
REPRESENTATION_REALIZATION_DEFECT
INFORMATION_BUDGET_DEFECT
EXERCISE_TARGET_DEFECT
FEEDBACK_BRANCH_DEFECT
EVIDENCE_CLASSIFICATION_DEFECT
OUTPUT_VALIDATION_DEFECT
MODEL_CAPABILITY_DEFECT
```

Only the last category should motivate model-tier escalation after structural causes are ruled out.

## Regression corpus to build before implementation promotion

### Historical replay cases

Promote public-safe derived cases from the frozen September-4 trajectory for at least:

1. array -> position -> index bridge;
2. `k` -> visible box without introducing moving `i` early;
3. box -> `S[i]` with box preservation;
4. `S[i] -> S[i+1]` visual equivalence before recurrence;
5. recurrence -> repeated recurrence -> loop bridge;
6. `enumerate(a)` visual pair mapping;
7. `S[i] = expression -> S.append(expression)` storage-form bridge;
8. `S[0] -> S[i]` bridge;
9. explicit comparison -> generalized `S[i] > max_sum`;
10. representation-preserving validation of loop result;
11. answer-leak exercise rejection;
12. detached/wrong-target exercise rejection;
13. partial-suboperation preservation;
14. meta-feedback does not update learner evidence.

### Mutation-routing case

Keep:

`p4.prerequisite-routing.code-confusion.v1`

and require representation-family adaptation + parent blocking + no canonical failure from the difficulty signal.

## Execution sequence after PAM B

PAM B is now independently reported/passed for the exact PR #71 merge baseline.

Next sequence:

1. **PAM C baseline observation** on the exact deployed known-PIR slice. Do not merge PR #73 into that baseline.
2. Preserve the live baseline discrepancy evidence, including any visual/representation failures.
3. Finish extracting the historical public-safe regression matrix above.
4. Review/merge the planning delta only after the baseline evidence chain is closed.
5. Implement the smallest versioned contracts needed for:
   - event classification;
   - prerequisite traversal frame;
   - representation intent;
   - exercise target;
   - output validation.
6. Run historical replay + new mutation-routing regressions.
7. Run paired Luna/Sol differential cases to identify residual model-capability gaps after structural enforcement.
8. Run fresh repo assurance/mutation testing for the new trust surface.
9. Deploy through a new local checkpoint with restart/resume.
10. Dogfood the mutation-testing trajectory again.
11. Only after stable results consider unfamiliar raw-problem compilation or broader curriculum automation.

## Promotion rule

A learner correction should become a durable product rule only when it can be expressed as one of:

- deterministic controller invariant;
- versioned representation/exercise contract;
- replayable regression fixture;
- validated authoring/decomposition rule;
- explicit learner preference with bounded scope.

Do not accumulate hidden prompt folklore.

## Bottom line

The frozen Sol transcript already contains the blueprint for the next system.

The main lesson is not "use Sol" and not even "use charts." It is:

> Study OS needs to execute a versioned pedagogical control-flow graph whose representation, exercise target, information budget, correction branch, evidence classification, and advancement conditions are explicit and mechanically checkable.

Luna then becomes a bounded realization engine inside that system. Sol remains useful as a donor/reference for finding candidate improvements, but neither model owns the pedagogical state machine.