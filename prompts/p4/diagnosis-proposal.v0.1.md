# Study OS P4 diagnosis proposal prompt — v0.1

Purpose: produce a **derived diagnosis proposal** from canonical learner evidence.
This prompt does not authorize progression, mastery, assistance escalation, or a learner-facing response.

## Inputs

The caller supplies:

- active course node / competency and its canonical prerequisite IDs;
- current learner-control state;
- relevant source evidence IDs and public-safe evidence excerpts/normalized observations;
- current representation family and any explicit learner representation request;
- known capability state for relevant prerequisites.

## Output contract

Return exactly one JSON object conforming to:

`schemas/p4-diagnosis-proposal.schema.json`

Required version pins:

- `schema_version`: `0.1.0`
- `prompt_version`: `p4-diagnosis-proposal.v0.1`

All hypotheses are derived and non-authoritative. Use `status: proposed` for model-generated hypotheses.
Every hypothesis must cite one or more supplied canonical source evidence IDs.

## Allowed diagnosis families

- `missing_prerequisite`
- `concept_failure`
- `representation_interference`
- `identifier_interference`
- `information_overload`
- `information_underload`
- `decomposition_too_coarse`
- `over_decomposition`
- `over_help`
- `uncertain_mixed`

## Rules

1. Do not claim mastery or lack of mastery from transcript language alone.
2. Do not decide whether the learner advances.
3. Do not invent prerequisite IDs. `suspected_competency_ids` must come from the supplied canonical graph.
4. If evidence supports more than one explanation, emit multiple hypotheses or `uncertain_mixed`; do not force certainty.
5. Treat explicit learner statements about confusing syntax, notation, wording, charts, tables, or code as representation evidence, not automatically as concept failure.
6. If the learner cannot parse the representation needed to answer the current probe, prefer a `missing_prerequisite` and/or `representation_interference` hypothesis over recording a canonical task failure.
7. `representation_signals` describe observed/requested presentation needs only. They do not authorize a renderer.
8. Use `interaction_granularity: single_probe` when the evidence indicates that multi-part explanations/questions are overwhelming or ambiguous.
9. Use `code_visibility: hide_initially` only when the learner evidence indicates code/syntax is blocking access to the target semantics.
10. Keep requested/avoided representation families structural, such as `decision_tree`, `state_flow`, `sequence_trace`, `comparison_view`, `table`, `source_code`, or `concrete_scenario`. Do not encode a one-off story as policy.

## Example interpretation boundary

If the current task is a boundary-condition mutation problem and the learner says they do not understand how the shown code works, a plausible proposal may contain:

- `missing_prerequisite` for an existing canonical comparison-semantics prerequisite;
- `representation_interference` for a code-first presentation;
- representation signals requesting a concrete/decision-tree form, hiding code initially, and using a single micro-probe.

The deterministic controller decides whether those hypotheses justify prerequisite traversal and which operation is legal.
