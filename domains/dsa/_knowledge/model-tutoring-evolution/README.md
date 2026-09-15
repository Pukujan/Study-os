# FOSSIL knowledge pack — Study OS DSA model tutoring evolution

Pack ID: `pack_3b5bd2d571fd2238ff15e10a5502d3d7`

Purpose: preserve the **why** behind the transition from fixed 14×15 DSA replay to completion-driven, fine-grained model tutoring so future agents do not rediscover or accidentally reverse the same lessons.

## FOSSIL Core contract

This pack is authored against the canonical FOSSIL Core contracts from `Pukujan/fossil-core`:

- knowledge-pack contract: `dkg.pack.v1` / `schemas/knowledge-pack/v1.schema.json`;
- durable event contract: `dkg.event.v1` / `schemas/events/v1.schema.json`;
- reviewed-evidence policy: preserve evidence first, emit `claim.proposed`, and require explicit review/promotion before shared/domain claims become accepted authority.

FOSSIL Core reference inspected when this pack was created: repository `Pukujan/fossil-core`, main at the 2026-09-14/15 session boundary (search results resolved around commit `2b20dc8a7704d4bf93f2e00fa26e229ac529cba4`).

## Contents

```text
manifest.json
sources/
  2026-09-14-fixed-turn-to-completion-driven-rationale.md
  2026-09-15-rotating-holdout-vocabulary-policy.md
events/
  2026-09-15-rationale-proposals.jsonl
  2026-09-15-rotating-holdout-vocabulary-proposals.jsonl
```

The source notes are reviewed **conversation + repository evidence syntheses**, not byte-exact ChatGPT exports. The original learner-calibration raw evidence remains under:

`/sessions/2026-09-04/sliding-window-pedagogy-calibration/`

The proposal events preserve the rationale for:

- why 14×15 is regression/calibration, not completion;
- why manual semantic review can invalidate mechanically green acceptance;
- completion-driven acceptance;
- fine-grained dependency/bridge decomposition;
- grounded symbolic/algebraic/state-transition learner preference;
- correction → changed retry → verification policy;
- the rule that the learner must not debug the tutor;
- prompt/schema/deterministic-controller responsibility separation;
- four-problem rotating public development batches;
- reproducible shuffle-bag + structural-family diversity;
- a separate genuinely hidden promotion lane;
- holdout burn → public regression → replenish lifecycle;
- grounded vocabulary simplicity and stable terminology;
- dual algorithm-graph + learning-graph strong inference;
- future regression/watch-out classes.

## Authority and promotion

The events intentionally use `claim.proposed`.

This is consistent with FOSSIL Core's reviewed-evidence policy: domain/shared knowledge requires explicit promotion rather than silently becoming accepted truth during ingestion.

For Study OS execution, the current code/spec authority is:

1. `docs/MODEL_TUTORING_COMPLETION_DRIVEN_VNEXT.md`;
2. `docs/MODEL_TUTORING_ROTATING_HOLDOUT_EVAL_V1.md`;
3. the current local execution handoff, when present;
4. current Issue #63 / PR #77 evidence;
5. exact code, tests, traces, and acceptance artifacts on the evidence-bearing head.

This pack is the durable **rationale / institutional-memory layer** explaining why those rules exist and which regressions to watch for.

## Runtime-ingest boundary

This ChatGPT/GitHub session can write the repository pack but does not expose a running FOSSIL node or local `ReviewedEvidenceIngestService`. Therefore no claim is made that these files were committed through a live FOSSIL event store/source-snapshot service in this session.

The repository representation is FOSSIL-contract-shaped and preserves stable pack/event identities. When Local Luna has FOSSIL Core available, it should validate this pack against the canonical schemas and, if a live mounted FOSSIL node is desired, preserve the source notes through `ReviewedEvidenceIngestService` rather than inventing a second interpretation.

Do not change claim identities merely because the pack is later mounted, moved, or projected.

## Future-agent reading rule

Before changing any of these areas, read the pack source and proposal events:

- model-tutoring turn budgets;
- teaching-plan granularity;
- learner-evidence progression;
- prompt evaluation;
- representation selection;
- vocabulary/term grounding;
- correction/retry/verification;
- tutor semantic validation;
- rotating-batch selection;
- hidden-holdout lifecycle;
- tree/graph/linked-list tutoring generalization.

The most important remembered rules are:

> A valid-looking conversation is not necessarily a completed teaching trajectory. Completion is defined by fine-grained dependency evidence and integration, never by reaching a fixed number of turns.

> A public rotating regression batch is not a hidden holdout. Hidden cases stop being hidden once they influence a fix.

> Simplify vocabulary only when the simpler expression preserves the concept's semantics; ground meaning before introducing the technical term or symbol.
