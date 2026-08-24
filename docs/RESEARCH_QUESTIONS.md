# Research Questions and Falsification Criteria

Study OS should be able to fail its own hypotheses.

## H1 — Representation-transition diagnosis is useful

**Hypothesis:** A meaningful portion of Subject 001's DSA failures can be localized to a transition such as `mental model -> invariant` or `procedure -> Python`, and targeted probes/interventions improve performance more efficiently than restarting the whole explanation.

**Evidence for:** repeated episodes where diagnosis predicts a targeted intervention followed by unaided improvement.

**Evidence against:** diagnosis labels are unstable, probes do not discriminate competing explanations, or generic re-teaching performs as well.

## H2 — Active representation operations outperform passive presentation

**Hypothesis:** prediction, explanation, reconstruction, debugging, or translation performed on a representation produces stronger unaided outcomes than simply viewing the same representation.

**Evidence for:** matched/alternating cases with better fade/transfer/retention outcomes.

**Evidence against:** passive viewing performs similarly or better under controlled content/time conditions.

## H3 — Representation switching can resolve specific bottlenecks

**Hypothesis:** when a representation fails, changing representation/operation can produce a measurable improvement.

**Evidence for:** repeated, versioned switches associated with improved matched-item performance that survives fading.

**Evidence against:** “breakthrough” self-reports do not predict behavior, or gains vanish once the representation is removed.

## H4 — AI can scaffold without producing permanent dependency

**Hypothesis:** staged AI assistance followed by deliberate fading can increase independent performance.

**Evidence for:** lower assistance levels over time with stable or improving correctness/transfer.

**Evidence against:** performance collapses without AI or hint depth increases across repeated practice.

## H5 — Subjective feedback is informative but insufficient

**Hypothesis:** Subject 001's detailed reports of confusion/helpfulness improve intervention selection, but behavioral validation prevents false-positive “learning” events.

**Evidence for:** self-report predicts some useful switches while a meaningful subset of high-confidence reports disagree with later performance.

**Evidence against:** self-report adds no predictive value beyond behavior, or system overweights it and systematically misclassifies mastery.

## H6 — The Study OS procedure is more reusable than any one preferred modality

**Hypothesis:** after optimizing the procedure for Subject 001, the same observation/probe/intervention/fade/transfer method can be used with another learner even if their effective representations differ.

**Not testable in R0.** Requires R2 or later.

## Explicit null-friendly stance

The project remains successful as research even if it finds:

- visuals do not consistently help;
- Subject 001 benefits more from semantic pseudocode than diagrams;
- AI tutoring creates unacceptable dependency;
- learning-state classification is too noisy to automate;
- a simpler worked-example + retrieval system performs equally well;
- the instrumentation overhead is not worth the learning benefit.

Those outcomes should change or stop the product rather than be hidden.