# Model tutoring experiment history

This is the concise human-readable history behind `manifest.json`. It records the status of approaches without rewriting older evidence to fit the newest theory.

## Status vocabulary

- **supported**: useful claim/architecture supported under the recorded conditions;
- **insufficient**: useful partial result, but acceptance/product goal was not met;
- **running**: active work whose result is not yet established;
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

## MT-E001 — proposed Sol calibration-artifact transfer to Two Sum

**Status: proposed.**

This is a deliberately different experiment from the existing autonomous Luna qualification loop.

Question:

> Can a fresh Sol tutoring session, given a durable artifact distilled from the successful Sliding Window calibration but not the raw transcript, transfer the decomposition/pedagogical method to Two Sum and teach a frozen synthetic learner through the problem with comparable clarity?

The purpose is to test whether we have captured reusable pedagogy before trying to make Luna imitate it cheaply.

See `proposals/MT-E001-sol-calibration-transfer-two-sum.md`.
