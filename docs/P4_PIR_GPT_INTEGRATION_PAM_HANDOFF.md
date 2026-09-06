# PAM Handoff — P4/PIR Study OS GPT Integration

Date: 2026-09-05
Status: active implementation handoff template
Tracker: #66

## Purpose

Use the Project Assurance Modules (PAM) method to separate planned work from proven work for the first Study OS GPT canonical-PIR integration.

The GitHub issue is the task/acceptance ledger. This handoff defines what evidence must exist before each material assurance checkpoint can be claimed.

## Authority order

1. live repository code/contracts/tests at the exact revision under evaluation;
2. `docs/P4_PIR_GPT_INTEGRATION_PDD.md`;
3. `docs/P4_PIR_GPT_INTEGRATION_SDD.md`;
4. `docs/P4_PIR_GPT_INTEGRATION_TDD.md`;
5. `docs/P4_PIR_GPT_INTEGRATION_THREAT_MODEL.md`;
6. issue #66 acceptance ledger;
7. PAM checkpoint/handoff records.

A historical checkpoint never overrides live code/CI truth.

## Required revision identities

Every checkpoint pins:

```text
study_os_revision
pir_revision
canonical_problem_id
canonical_pir_revision
controller_revision
renderer_revision
assessment_revision
mcp_contract_version
local_db_schema_version if applicable
```

Unknown/unavailable values are recorded as unknown, not invented.

## Checkpoint A — design + executable verification

Claim allowed only when:

- PDD, SDD, TDD and threat model are committed;
- production-facing contracts/controller/renderer for the slice are implemented;
- public CI is green at the exact commit;
- historical September-4 replay tests are green;
- required pedagogical data mutations are rejected/detected;
- critical implementation mutation testing has no unresolved non-equivalent survivors, or any exception is explicitly documented as blocking the checkpoint;
- existing application/MCP regressions are green;
- no hidden/sealed benchmark material is present in runtime code/fixtures.

Receipt fields:

```text
checkpoint: design_verified
study_os_revision: ...
pir_revision: ...
ci_run: ...
historical_replay: pass/fail
data_mutations: pass/fail
implementation_mutations: pass/fail/not_run
mcp_regression: pass/fail
known_risks: [...]
unproven_claims: [...]
```

## Checkpoint B — local MCP deployment

Performed by Luna/local operator only after Checkpoint A or an explicitly approved pre-checkpoint integration trial.

Required pre-state capture:

- local Study OS revision/runtime version;
- DB schema version;
- MCP contract/tool inventory;
- doctor/health state;
- current configured GPT action/MCP route identity where safely observable;
- backup receipt for local DB/private runtime state.

Required deployment actions:

1. install exact reviewed Study OS commit;
2. apply only reviewed migrations;
3. regenerate/install reviewed GPT Actions/MCP schema if required;
4. run full local test suite;
5. restart Study OS service/private transport;
6. verify doctor/health;
7. verify prior MCP tools remain compatible;
8. verify new PIR tools are present;
9. run known sliding-window smoke path;
10. restart service mid-run;
11. verify same problem-run/pinned PIR/current state resumes;
12. verify retry/idempotency behavior where practicable.

Luna must not:

- modify PDD/SDD/TDD/threat model to match local behavior;
- change canonical graph or assessment answers;
- weaken tests;
- import benchmarker/sealed oracles;
- silently make local-only semantic code changes.

Any reusable semantic fix returns to a reviewed GitHub branch/PR before the deployment checkpoint is accepted.

Receipt fields:

```text
checkpoint: local_mcp_deployed
study_os_revision: ...
runtime_version: ...
db_schema_before: ...
db_schema_after: ...
mcp_contract_before: ...
mcp_contract_after: ...
tools_before: [...]
tools_after: [...]
backup: pass/fail
local_tests: pass/fail
doctor: pass/fail
sliding_window_smoke: pass/fail
restart_resume: pass/fail
local_only_changes: []
errors_or_repairs: [...]
```

## Checkpoint C — live Study OS GPT dogfood

Required evidence from a real GPT session against the deployed MCP:

- known sliding-window problem resolves to the pinned canonical asset;
- backend-authorized first TeachingTurn appears;
- GPT preserves critical representation output;
- at least one learner response is submitted through the PIR run;
- PARTIAL routing is exercised if feasible in the validation script/session;
- clarification/expansion does not skip canonical state;
- durable learner/assistant source turns remain available in Study OS evidence;
- final historical frontier, if traversed, is `assembled_mastery_unproven`;
- no answer leakage or unsupported progression observed.

Sanitize private learner text before public checkpoint material unless explicit authorization permits otherwise.

Receipt fields:

```text
checkpoint: live_gpt_pir_validated
study_os_revision: ...
pir_revision: ...
problem_run_id: sanitized-or-local-ref
canonical_problem_id: ...
canonical_pir_revision: ...
observed_path: [...]
partial_branch: pass/not_exercised/fail
expansion_nonadvance: pass/not_exercised/fail
durable_capture: pass/fail
final_status: ...
regressions_found: [...]
claim_boundary:
  - integration/control validation only
  - no arbitrary-problem generalization claim
  - no learning-efficacy claim
```

## Failure handling

A failed local/live validation does not justify editing the checkpoint until green.

Instead:

```text
failure
→ preserve exact revision/input/result
→ classify against TDD/threat taxonomy
→ open/update #66 with evidence
→ implement reviewed fix
→ rerun public CI
→ redeploy exact new commit
→ revalidate
```

Do not overwrite or reinterpret a failed receipt as a pass.

## Next-action rule

The next action should always be the smallest unresolved item blocking the next checkpoint. Do not create unrelated infrastructure while a pedagogical/control failure remains reproducible.
