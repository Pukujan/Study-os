# P4 Prerequisite-Sensitive Traversal — Implementation Handoff Boundary

This handoff is intentionally non-executable until the design delta in `docs/P4_PREREQUISITE_SENSITIVE_TRAVERSAL_DELTA.md` is reviewed and PAM B has established the local baseline for the PR #71 merge revision.

## Persistent local executor may later implement

- additive controller/state persistence required by the accepted design;
- prerequisite detour/return semantics inside the existing P4/PIR control boundary;
- semantic representation-contract validation;
- public regression tests based on `tests/fixtures/pir/mutation_testing_prerequisite_routing.v1.json`;
- deterministic/property/mutation tests for new authority logic;
- reviewed DB migration and restart/resume behavior if persistence changes are approved;
- local service/MCP integration and deployment validation;
- exact candidate SHA + sanitized receipts.

## Persistent local executor may not

- redefine progression or mastery;
- decide that a prerequisite is satisfied without the accepted evidence policy;
- replace the controller with tutor/model judgment;
- hard-code a particular concrete story as the representation policy;
- weaken regression or mutation oracles;
- lower thresholds or exclude new authority logic to obtain green;
- introduce arbitrary raw-problem compilation into the learner-facing runtime;
- make local-only semantic repairs.

## Stop condition

Return to review with an exact candidate SHA when all accepted deterministic tests/regression fixtures are green and any required migration/restart receipts are available. Any proposed invariant/gate change returns to design authority before implementation continues.
