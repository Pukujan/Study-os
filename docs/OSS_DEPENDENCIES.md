# OSS Dependency and Donor Usage Ledger

Status: **implementation provenance**

Last updated: 2026-08-24

This file records which external tutoring/learning-system projects are actual Study OS runtime dependencies versus research/design donors. It complements `docs/OSS_TUTORING_DONOR_AUDIT.md` and the G0 source/license/assumption gate in Issue #10.

## Runtime dependency: py-fsrs

- Package: `fsrs`
- Accepted version range: `>=6.3.2,<7`
- Upstream: `open-spaced-repetition/py-fsrs`
- License: MIT
- Integration type: **wrapped dependency; no FSRS scheduler source copied into Study OS**
- Study OS module: `study_os.adaptive.fsrs_adapter`
- Purpose: retrievability calculation, review-state update, and next-due scheduling for delayed-retention probes.
- Optimizer extra: **not used** in the initial adapter.

Initial Study OS policy constraints:

- FSRS does not own canonical learner state or checkpoints.
- FSRS receives an explicit `Again|Hard|Good|Easy` rating; the adapter does not infer that rating from a generic assessment `pass/fail`.
- The rating must reference canonical Study OS assessment evidence through the `LearnerSnapshot`.
- FSRS interval fuzzing is disabled initially so shadow/replay results are deterministic and auditable.
- FSRS may eventually control *when* a retention probe is due after promotion gates; it does not control probe content, grading, capability promotion, transfer claims, or delayed-mastery claims.
- Serialized FSRS card/review state is stored only as derived donor state until a dedicated canonical retention projection is explicitly approved.

## Donor-inspired mechanism: Tutor MCP BKT information gain

- Upstream reference: `ArnaudGuiovanna/tutor-mcp`
- Integration type: **research/design donor; small mathematical mechanism reimplemented behind Study OS contracts**
- Study OS module: `study_os.adaptive.diagnostic`
- Purpose: expected reduction in binary mastery entropy for diagnostic candidate ranking.
- Runtime dependency on Tutor MCP: **none**.

Study OS tests the formula independently and keeps the selector in shadow mode. Tutor MCP does not receive Study OS database access or learner-state ownership.

## Donor-inspired mechanism: CAT / 2PL IRT item selection

- Primary references: `douglasrizzo/catsim`, `bigdata-ustc/EduCAT`, standard IRT/CAT definitions
- Integration type: **research/design donor; standard 2PL probability and Fisher-information formulas implemented locally for reproduction/shadow testing**
- Study OS module: `study_os.adaptive.cat`
- Runtime dependency on catsim/EduCAT: **none** in the current slice.
- Purpose:
  - diagnostic item ranking by maximum Fisher information;
  - instructional item ranking by closeness to a target predicted-success probability;
  - explicit item exposure hard gates.

A later decision may wrap an OSS CAT package if its broader estimation/selection functionality is justified by Study OS data. The current small formula implementation avoids importing a large psychometric stack before the assumptions are validated.

## Curriculum and tutor-policy donors not currently imported

The following remain research/design references rather than runtime dependencies:

- Oppia — atomic observable skills, prerequisites, misconceptions, item-authoring discipline;
- OATutor — problem/step/knowledge-component model and hint/scaffold structure;
- ScaffoldLM — ordered intermediate targets with assess/remediate/advance control;
- PedagogicalRL / MathTutorBench — tutor-behavior evaluation ideas;
- pyBKT — candidate future dependency if repeated tagged evidence justifies probabilistic knowledge tracing.

Any future import or source transplant must add an entry here with the exact package/repository, version/revision, license, copied/wrapped/reimplemented classification, assumptions, and bounded authority.
