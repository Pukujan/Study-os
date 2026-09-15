# Model tutoring pilot — focused SDD

## Components

`src/study_os/model_tutoring.py` contains the bounded pure-Python kernel:

- `ModelDiagnosis`: strict model proposal (`diagnosis_family`, `operation`,
  `assistance_level`);
- `ModelTutoringState`: current stage and explicit evidence flags;
- `ModelTutoringController.authorize`: clamps the model proposal to the current stage,
  validates the assistance ceiling, and returns a generation contract plus the exact
  v0.1 trace fields;
- `validate_generated_response`: deterministic learner-visible validation; and
- `commit_turn`: advances at most one stage only after a recovery/check signal.

The kernel contains policy and constraints, not canonical teaching prose.

## Authorization contract

For `contains-duplicate-set`, the controller maps the current stage to one target
concept and the minimum variables required for that stage. Every contract includes:

- required anchor terms and forbidden future/alias terms from the calibrated behavior;
- visual-before-explanation, question, relation, and non-empty-line budgets;
- allowed/forbidden variables;
- `advance_allowed`, which is false for clarification and wrong/uncertain signals; and
- prompt/model provenance values.

The model cannot request a different target, add a forbidden variable, exceed A2, or
mark mastery. The response validator rejects those conditions and rejects full code
before the loop stage.

## Runtime seam

The local pilot runner reuses `CodexCliActor` from the existing dual-Luna runner. The
teacher is instructed to call the existing local Study OS MCP (`resolve_problem`) on
every turn, then return a strict JSON object containing its diagnosis and generated
response. The runner applies the deterministic kernel and retries generation with the
validation failure if necessary. This keeps Study OS MCP in the execution path without
adding a public MCP tool or a canonical asset.

The persisted artifacts are:

- `artifacts/model-tutoring-contains-duplicate.jsonl` (learner + final teacher response);
- `artifacts/model-tutoring-contains-duplicate-trace.jsonl` (one schema trace per turn); and
- `artifacts/model-tutoring-contains-duplicate-acceptance.json` (gate receipt).

## Failure and recovery

Each accepted turn is appended atomically to both JSONL files. On restart, the runner
loads matching turn indexes, reconstructs the deterministic stage from prior signals,
and resumes at the first missing turn. A stale local Codex session is replaced while
the full conversation payload is retained. No partial response is exposed or treated
as evidence.

## Test-first acceptance

Unit tests cover strict proposals, authorization, advancement, output validation, and
trace schema. Differential tests compare stage/variable/visual/assistance semantics to
the calibrated corpus. Metamorphic tests cover paraphrases and numeric substitutions.
Stateful/property tests exercise valid and invalid signal sequences. Mutation-style
tests flip each authority boundary and assert rejection. The real 15-turn local run
then passes `tools/check_model_tutoring_acceptance.py`.
