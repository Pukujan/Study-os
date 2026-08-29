# Study OS methodology capture — 2026-08-29

status: draft
authority: non-authoritative
evidence status: reconstructed

This capture records a public-safe derivative of the shared Study OS
conversation. It is a research input and personal study aid, not a mastery
record, clinical assessment, universal learning rule, or accepted runtime
policy.

## Source boundary

- Shared source: <https://chatgpt.com/share/6a90f29f-c14c-83ea-a688-5ecdf6518933>
- FOSSIL review: <https://github.com/Pukujan/fossil-core/pull/240>
- FOSSIL commit preserving the reconstructed source and pack: `9c142da7c5fef05562208b8d84c33e84f23f1f77`
- Curated dataset: [`datasets/learner-methodology/2026-08-29-study-os-methodology-capture.json`](../datasets/learner-methodology/2026-08-29-study-os-methodology-capture.json)
- FOSSIL export pointer: [`fossil/exports/research/2026-08-29-study-os-methodology.json`](../fossil/exports/research/2026-08-29-study-os-methodology.json)

The source was reconstructed from a shared-page route payload rather than
received as an original conversation export. FOSSIL preserves the complete
reconstructed learner-facing projection and its hashes. This public
repository intentionally contains neither that transcript nor the raw route
payload.

## What the source supports

The learner states a preference for writing code independently, receiving
questions and hints before full solutions, and using visual traces for DSA.
They also describe isolated pattern drills as feeling like memorization,
syntax as a recurring friction point, and failure/version tracing as part of
their learning process. They want practical engineering ability and
interview readiness to develop together.

The interaction records a correction from a completed visual answer to an
incomplete prompt, a later transformation after an ASCII-tree hint, repeated
syntax-translation errors alongside relevant algorithmic logic, and reported
gaps in attempt persistence and checkpoint freshness.

These are evidence-classed records, not a single blended learner score.

## Draft protocol to test

1. Start with a realistic requirement and make the system behavior explicit.
2. Let the learner write the relevant logic and preserve meaningful attempts.
3. Diagnose conceptual, state/invariant, representation, and syntax issues
   separately when the evidence supports that distinction.
4. Use the smallest useful representation change: trace, pseudocode, ASCII
   state, or partial hint.
5. After assisted success, remove the external aid and test reconstruction,
   transfer, and later retention separately.
6. Keep practical engineering scenarios and interview reconstruction connected.

This protocol remains a proposal. The next Study OS implementation work is to
capture these dimensions through canonical session events and assessments,
not to treat this one conversation as proof that the protocol works.

## Public-safety and authority notes

- `self_reported`, `observed`, and `derived` records are separate in the JSON
  dataset.
- The FOSSIL pack is dedicated research/personal scope and remains
  `not_promoted`.
- Tutor-generated research citations and interpretations in the source were
  not independently revalidated here.
- A correct assisted response is not equivalent to unaided mastery.
- This capture does not alter the R0 gate, runtime authority, or canonical
  Study OS session/checkpoint store.
