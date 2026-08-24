# Current State

Date: 2026-08-23
Status: v0.1 experiment design

## What exists conceptually

Study OS begins from the hypothesis that much technical learning difficulty is representation friction: experts communicate in compressed representations while learners spend substantial effort reconstructing missing intermediate steps.

The planned system treats AI as an adaptive translation layer rather than only an answer generator.

The first use case is DSA learning with a learner who can provide high-resolution live feedback about:

- what is understood;
- what is not understood;
- which explanation/figure/flowchart makes understanding worse or better;
- why a representation caused a breakthrough;
- where understanding stops when translating into code.

This creates the opportunity to build a longitudinal Golden Learning Trajectory dataset rather than a static Q&A dataset.

## Current hypothesis

A useful learning record is not “question -> answer.” It is:

`learner state -> task -> attempt -> observed failure -> self-report -> intervention -> re-attempt -> assessment -> transfer/retention`

## Initial test subject

Subject 001 is the first longitudinal test subject.

This is intentionally N=1. Results are valid as evidence about this learner and as development data for the procedure; they must not be promoted into universal learning claims without later replication.

## Initial domain

- DSA
- Python
- Sliding Window first

The project should expand only after the instrumentation and evidence loop work on one concept family.

## Known design requirements

- preserve full raw transcripts;
- never overwrite original evidence;
- keep observed, self-reported, and derived labels separate;
- version lessons, representations, schemas, assessments, and learner-model derivations independently;
- organize data by domain/concept/lesson and by time/session;
- allow one lesson to span sessions and one session to contain many learning episodes;
- support deterministic figures/flowcharts/state traces before relying on generative media;
- support later image, audio, and video representations without making them canonical truth;
- preserve hidden transfer and delayed retention tests separately from training examples.

## Immediate build sequence

1. Define canonical Study OS schemas.
2. Define session/transcript ingest contract.
3. Capture the first real ChatGPT learning session verbatim.
4. Extract learning events and episodes with transcript-span provenance.
5. Build one Sliding Window lesson IR with several representations.
6. Run instrumented learning sessions.
7. Record subjective breakthrough claims and objective assessments separately.
8. Build hidden-transfer and delayed-retention checks.
9. Compare representation versions and interventions.
10. Only then expand to a second DSA pattern.

## Open questions

- best transcript export format from each LLM provider;
- how to normalize timestamps/roles/tool messages while preserving raw source bytes;
- which learner-state labels should remain human-confirmed versus model-derived;
- how to generate deterministic state animations from Lesson IR;
- when to promote a repeated subject-specific observation into a lesson-level hypothesis;
- what subset of Study OS artifacts should be exported to FOSSIL;
- whether later multi-subject experiments need anonymized/pseudonymous subject boundaries.
