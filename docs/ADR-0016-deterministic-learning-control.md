# ADR-0016 — Deterministic Learning Control, Bounded AI Representation, and Versioned Operational Improvement

Date: 2026-09-03
Status: accepted by product owner for P4 planning
Related: #63

## Context

Study OS is now usable across GPT sessions with durable source-turn evidence and cross-chat continuity.

Real learning has clarified the central product problem: course/source material can impose unnecessary representational difficulty through author-specific terminology, identifiers, notation, code style, decomposition, context amount, and modality.

AI is useful for transforming these representations, but allowing the LLM to also own curriculum progression, assistance escalation, mastery, and learner-state mutation would make the learning path difficult to reproduce, audit, version, or later replace with cheaper specialized components.

The project also needs longitudinal operational transcripts to improve Study OS itself as the learner progresses into harder DSA/system-design material.

## Decision

Study OS will separate deterministic learning control from AI representation realization.

### Deterministic authority

Code/state owns:

- course node/version;
- prerequisites;
- learner-control state;
- allowed pedagogical operations;
- assistance ceiling;
- progression/blocking;
- fade/restoration requirements;
- transfer/retention requirements where applicable;
- evidence semantics;
- module-version provenance.

### AI authority

AI may:

- propose derived diagnosis hypotheses;
- realize explicitly authorized pedagogical operations;
- generate/transform learner-facing representations under constraints.

AI may not silently:

- advance curriculum;
- mark prerequisites satisfied;
- declare mastery;
- exceed the assistance ceiling;
- change the target concept;
- mutate historical evidence/state.

## Representation principle

> Preserve productive target difficulty while reducing unnecessary representation difficulty.

Adapted representations are versioned and linked to source representations. Where an operation claims reversibility, source/authentic representation must remain restorable and should later be retested as appropriate.

Representation change, task decomposition, information amount, and assistance are separate intervention dimensions. If multiple dimensions change together, Study OS records all of them rather than attributing the outcome to one variable.

## Operational improvement principle

Real learning is the primary product-development data stream.

Meaningful trajectories preserve the state/evidence/operation/version/outcome chain so later module versions can be evaluated against historical cases.

Module changes are explicit versions, not silent prompt drift.

Offline replay is counterfactual system evaluation and never becomes learner evidence as if the learner actually experienced the replayed intervention.

Prospective learner behavior remains required for new outcome evidence.

## Modular substitution consequence

Interfaces should allow future implementations to replace large-LLM work with cheaper deterministic/specialized components without changing controller semantics.

Possible later implementations include parsers/AST/compiler transforms, deterministic traces, retrieval, templates, sentence embeddings/transformers, small classifiers/models, and IR/language/notation converters, with constrained LLM fallback for genuinely generative/ambiguous work.

This is future architecture optionality, not a current optimization milestone.

## Evidence-scope consequence

Subject 001 longitudinal trajectories are valuable within-learner product evidence. They do not establish population-level efficacy.

Authenticated/beta users are a later validation phase for testing generalization and personalization requirements after the deterministic control/representation contracts have been stressed on harder real material.

## Consequences

Positive:

- learner path is reproducible and auditable;
- AI behavior is bounded without giving up generative flexibility;
- source representations remain recoverable;
- intervention effects can be attributed more carefully;
- module upgrades are comparable over time;
- historical evidence remains valid across implementation changes;
- future lower-cost components can replace LLM-backed modules incrementally.

Costs:

- requires explicit course/control/operation/version semantics;
- requires decision/outcome provenance beyond raw transcript capture;
- controller policy errors become first-class product failures;
- not every tutoring interaction can be treated as unconstrained chat.

## Invariants

1. Same canonical controller inputs and controller version produce the same authorized next action.
2. Course progression is never an unrecorded LLM side effect.
3. AI diagnosis is a hypothesis, not learner truth.
4. Transcript language alone never becomes mastery.
5. Multi-dimensional interventions remain multi-dimensional in data.
6. Source evidence and experienced outcomes are immutable across module upgrades.
7. Replay/counterfactual outputs are explicitly non-experienced evidence.
8. Module evolution is explicitly versioned and attributable.
9. Future non-LLM implementations may fulfill representation/diagnosis contracts without changing course/controller authority.

## Supersession

This decision sharpens D014. D014 remains valid for operational dogfooding, durable evidence, structured curriculum, and representation-first development. ADR-0016 makes deterministic control + bounded/versioned representation the primary P4 architecture.
