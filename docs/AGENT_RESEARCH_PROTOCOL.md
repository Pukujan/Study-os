# Agent Research Protocol

This protocol keeps agents useful while Subject 001 focuses on learning.

## Agent role

Agents are responsible for maintaining the research harness around the learner, not for turning every conversation into a feature request.

During/after learning sessions, an agent may:

- preserve/hash transcript evidence in the approved private boundary;
- normalize transcript structure;
- propose observed/self-reported/derived learning events;
- propose episode boundaries;
- identify competing learner-state hypotheses;
- create follow-up assessment proposals;
- update the living handoff and project manifest when project state changes;
- maintain source/research indices;
- suggest experiment changes from accumulated evidence;
- prepare FOSSIL promotion candidates after Study OS review.

## Agent must not

- invent missing learner statements or outcomes;
- mark mastery from conversational confidence;
- silently promote subject-specific findings to lesson/domain truth;
- change hidden eval answers after seeing learner performance merely to make metrics look better;
- commit raw private transcripts to the public repo;
- expand scope past the active build gate without recording the decision;
- rewrite historical raw/observed events to fit a later theory.

## Session closeout procedure

After a learning session:

1. Capture evidence/hashes.
2. Normalize messages with stable IDs/spans.
3. Extract event proposals.
4. Separate evidence classes.
5. Propose episode boundaries.
6. Summarize unresolved learning transitions.
7. Propose delayed/transfer checks.
8. Update `docs/HANDOFF.md` only if project/experiment state changed.
9. Update `PROJECT_MANIFEST.yaml` only if machine-readable state changed.
10. Add durable research decisions to `docs/DECISIONS.md`.

The learner should not need to manually maintain repository state during normal study.

## Self-updating boundary

“Self-updating” means agents are instructed and CI-checked to keep explicit project-state artifacts current when they modify the project. It does **not** mean the repository changes itself asynchronously.

The required state surfaces are:

- `AGENTS.md` — stable operating rules;
- `PROJECT_MANIFEST.yaml` — current machine-readable state;
- `docs/HANDOFF.md` — current operational snapshot;
- `docs/DECISIONS.md` — durable boundary/architecture decisions;
- GitHub Issues — work/history/acceptance criteria.

## Research-source policy

When an agent adds an empirical learning claim to project docs:

- prefer peer-reviewed reviews/meta-analyses/RCTs/controlled studies;
- distinguish evidence from design inference;
- include DOI or durable source URL;
- record important contrary/limiting evidence;
- do not use competitor marketing as pedagogical validation;
- note when evidence is outside programming/DSA and therefore only indirectly applicable.

## Change severity

### Low
Typos, examples, refactors with no semantic change.

No manifest/handoff update normally required.

### Medium
New schema field, evaluator, representation renderer, ingest stage, experiment fixture.

Review manifest/handoff and update if current behavior/state changed.

### High
Research hypothesis, evidence-class semantics, project boundary, privacy rule, FOSSIL ownership, build gate, learner state model, deployment decision.

Must update manifest/handoff and add a decision record.

## Agent completion report

Agents should report:

- what changed;
- why;
- evidence/research basis when relevant;
- tests/checks run;
- data/privacy implications;
- unresolved questions;
- next recommended learner/research action.
