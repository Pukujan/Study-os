# DSA decomposer skill + local hidden-holdout boundary rationale

Date synthesized: 2026-09-15 UTC
Scope: Study OS completion-driven model tutoring
Evidence class: project/domain design rationale synthesized from conversation + current PR #77 repository state

## Decision

Study OS should use a reusable **DSA decomposition skill** plus a deterministic checklist/schema gate.

The skill owns the strong-inference procedure:

```text
raw problem
→ derive algorithm graph
→ infer state / invariant / transition / base condition
→ work backward from the solution
→ expand learner prerequisites and representation bridges
→ reverse into learning order
→ choose grounded vocabulary / symbols / representation
→ adversarially critique the candidate plan
→ emit structured TeachingPlan candidate
```

The checklist/schema/controller do not replace this reasoning. They verify that the resulting plan has the properties learned from the calibrated evidence: no missing prerequisite, stable meanings, grounded symbols/terms, legal correction/retry/verification, and completion based on learner evidence rather than a fixed turn count.

The skill must not expose or persist private chain-of-thought. It persists only structured conclusions and compact rationale.

## Why skill + checklist rather than checklist alone

A checklist is good at catching omissions after the fact, but it does not reliably produce the reverse-solution derivation needed for a new algorithm.

A skill supplies the reusable inference process; the checklist supplies the trust boundary.

This separation also prevents hard-coding a per-problem lesson table into deterministic code.

## Prompt versioning

The current PR contains `src/study_os/prompt_registry.py`, an immutable content-addressed prompt registry with versions + SHA-256 hashes for decomposition, diagnosis, and generation.

The decomposer skill does not replace prompt provenance. Material changes to the decomposition behavior should register a new prompt version rather than editing historical `study-os.model-tutoring-decompose.v1` semantics in place.

Candidate identity must bind at least code commit + prompt versions/hashes + schema versions + model ID + decomposer skill version + evaluation-policy version.

## Local long-running loop

The intended engineering loop can run locally as a resumable state machine:

```text
build/fix
→ tests/type/lint/mutation
→ freeze candidate
→ select 4 rotating public problems
→ completion-driven runs
→ deterministic acceptance + visible review
→ generic diagnosis/fix
→ new candidate / different public batch
→ eventually hidden promotion evaluation
```

The durable evaluation ledger makes this restartable and prevents reselection/reseeding after a crash.

## Hidden holdout boundary

Do not give the engineering/prompt-fixing Luna raw hidden holdout access.

The practical local boundary is an isolated evaluator process/agent:

- engineering process: writable repo, no `STUDY_OS_HOLDOUT_DIR`;
- holdout evaluator: private holdout directory + read-only frozen candidate;
- measured decomposer/teacher/student: receive only the current hidden problem statement as injected input, not the holdout filesystem path and not the oracle;
- hidden evaluator oracle stays evaluator-only;
- engineering receives a sanitized verdict/failure category, not raw hidden content.

This is stronger than allowing the main engineering Luna to see hidden cases while attempting to hide them only from subagents. If the agent that edits prompts can see a hidden case, it can overfit directly or indirectly.

## Burn rule

If raw hidden case details are required to diagnose/fix a failure, the case is no longer a holdout.

```text
hidden failure token
→ explicit burn
→ export reviewed case to public regression
→ remove from future hidden eligibility
→ engineering Luna may inspect/fix
→ replenish private hidden bank
```

This keeps holdout administration lightweight while preserving a real generalization boundary.

## Who checks measured runs

Authority is layered:

1. TeachingPlan/schema validation before teaching;
2. deterministic per-turn semantic/vocabulary/progression validation;
3. per-problem completion acceptance after the run;
4. learner-visible reviewer (Luna or Terra) for uncoded pedagogical pathologies;
5. hidden evaluator oracle only for private promotion cases.

A model's own claim that it succeeded is never acceptance authority.

## Durable implementation surfaces

- `plugins/study-os-dsa-decomposer/skill.md`
- `plugins/study-os-dsa-decomposer/checklist.md`
- `contracts/model-tutoring-agent-boundaries.v0.1.json`
- `docs/MODEL_TUTORING_LOCAL_AUTONOMOUS_LOOP_V1.md`
- `docs/MODEL_TUTORING_ROTATING_HOLDOUT_EVAL_V1.md`
- `src/study_os/prompt_registry.py`

These choices should be read before changing decomposition, prompt iteration, local autonomous evaluation, or hidden-holdout access policy.
