# Model tutoring experiment history

This is the concise human-readable history behind `manifest.json`. It records the status of approaches without rewriting older evidence to fit the newest theory.

## Status vocabulary

- **supported**: useful claim/architecture supported under the recorded conditions;
- **insufficient**: useful partial result, but acceptance/product goal was not met;
- **running**: active work whose result is not yet established;
- **implemented_unrun**: the experiment harness exists, but no measured run has been reviewed/accepted yet;
- **superseded**: replaced as the preferred execution path while historical evidence remains valid;
- **failed**: use only when the explicit hypothesis/acceptance condition was actually contradicted or could not be met for a documented reason.

## MT-H001 — learner-calibrated Sliding Window trajectory

**Status: supported historical reference.**

The September 4, 2026 learner-driven Sliding Window session remains the strongest known learner-facing calibration reference. The raw visible trajectory is preserved in eight transcript parts, with derived findings and partial reviewed goldens.

What it established for the current learner/problem context:

- very fine prerequisite/bridge granularity can be materially easier than expert-sized algorithm stages;
- one new semantic relation at a time reduced friction;
- stable visual/state representation across neighboring concepts mattered;
- grounded concrete state preceded useful abstraction/code;
- correction → changed retry → verification was more reliable than repeated explanation;
- learner difficulty often revealed a missing bridge or representation problem rather than a need for more prose.

Authority boundary: this is calibration evidence, not population proof and not yet a complete runtime-authoritative compiled golden.

Primary discovery entrypoint: `docs/CALIBRATION_INDEX.md`.

## MT-H002 — deterministic learning control / prerequisite-sensitive remediation

**Status: supported architecture foundation; not a failed decomposition experiment.**

Study OS retained deterministic authority over progression, evidence, assistance, and legal state transitions. PR #75 and Issue #63 record the prerequisite-remediation work prompted by real dogfood failures.

What the evidence showed was **not** that deterministic control itself failed. It showed that deterministic control/structure does not automatically produce good learner-facing teaching. A controller can be correct about legal transitions while the generated decomposition, representation, or explanation is still poor.

This distinction remains important:

```text
deterministic controller/validation: retained
hand-authored or structurally valid decomposition as proof of good pedagogy: insufficient
```

References:

- `docs/ADR-0016-deterministic-learning-control.md`
- PR #75
- Issue #63

## MT-H003 — fixed-turn prompt-led model tutoring

**Status: insufficient; fixed-turn success criterion superseded.**

Prompt/model-driven tutoring was tested through fixed-turn regression scenarios. The approach demonstrated that a model could produce superficially coherent learner-facing turns, but manual review exposed semantic drift, repetitive turns, progression errors, and cases where a learner could remain stuck while automated acceptance still appeared green.

The strongest documented false-positive: a public all-DSA run could remain on concept 0 throughout the allotted turns and still pass the then-current structural acceptance. This invalidated fixed turn count as a completion criterion.

Lesson retained:

> Prompt quality matters, but prompt success cannot be the acceptance boundary.

References:

- Issue #63 model-tutoring evidence/comments
- `docs/ALL_DSA_MODEL_TUTORING_HANDOFF.md`
- PR #77 historical artifacts

## MT-H004 — generic TeachingPlan + prompt + schema + deterministic validation

**Status: insufficient as learner-facing proof; operational generalization was useful.**

The next architecture externalized model-generated TeachingPlans and separated responsibilities:

- prompt/skill steers decomposition, diagnosis, vocabulary, representation, and prose generation;
- schema externalizes the model's claims;
- deterministic code validates semantics/state and owns progression;
- acceptance/manual review judges learner-visible quality.

This generalized operationally across the public DSA corpus, but generated plans could still be far too coarse. Structural/schema validity did not guarantee that the learner received the micro-bridges observed in the successful Sliding Window calibration.

Manual review therefore invalidated aggregate green status as sufficient product evidence and drove the completion-driven vNext work.

References:

- `docs/MODEL_TUTORING_COMPLETION_DRIVEN_VNEXT.md`
- Issue #63
- PR #77

## MT-H005 — completion-driven decomposition/reliability qualification

**Status: running / not yet proven.**

The current PR #77 direction attempts to repair the above limitations using:

- algorithm graph first;
- backward prerequisite expansion into a learning graph;
- grounded vocabulary/symbols;
- fine-grained bridges;
- completion-driven rather than fixed-turn acceptance;
- correction/retry/verification behavior;
- rotating public regression and isolated hidden promotion;
- explicit prompt/schema/model provenance.

This is the current architecture attempt, not a finished calibration result. Do not describe it as proven merely because the runner or deterministic gates execute.

References:

- `docs/MODEL_TUTORING_COMPLETION_DRIVEN_VNEXT.md`
- `docs/MODEL_TUTORING_DECOMPOSITION_RELIABILITY_QUALIFICATION_V1.md`
- PR #77

## MT-E001 — Sol calibration-artifact transfer to Two Sum

**Status: implemented, not yet run/reviewed.**

This is deliberately different from the autonomous Luna qualification loop. It tests a much narrower question:

> Can a fresh Sol tutoring session, given the frozen pedagogical calibration distilled from the successful Sliding Window session but not the raw transcript, independently teach Two Sum well against a seeded synthetic beginner whose replies vary across correct, wrong, partial, slightly misaligned, uncertain, why, smaller-step, and representation-confusion states?

The purpose is to test whether the durable calibration artifact actually transfers useful teaching behavior before trying to make Luna imitate it cheaply.

Implementation:

- calibration input: `calibration/cases/sliding-window.subject-001.2026-09-04/transfer-calibration.v0.1.json`
- runner: `tools/run_sol_calibration_transfer.py`
- default command: `python tools/run_sol_calibration_transfer.py`
- outputs: `artifacts/model-tutoring-experiments/MT-E001/run-NNN/`
- primary review surface: self-contained `review.html`

The runner does not use the production Study OS controller or the historical Two Sum stage script. Sol derives the learning path itself. The actors run from an empty temporary working directory; tool use is forbidden by the role contract and known Codex command/file/MCP/web tool events are rejected. This is not claimed as perfect filesystem isolation.

A run is not evidence of success merely because Sol eventually emits completion. The complete learner-visible interaction still requires owner review in the generated HTML.

See `proposals/MT-E001-sol-calibration-transfer-two-sum.md`.
