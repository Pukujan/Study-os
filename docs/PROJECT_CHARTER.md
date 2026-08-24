# Project Charter

## Problem statement

AI can make a novice/intermediate programmer productive before the programmer has internalized every syntax rule, algorithmic pattern, or debugging procedure. That productivity is valuable, but it creates a learning gap: working code can exist before the learner can independently explain, trace, modify, test, or reconstruct it.

Study OS investigates whether AI can be used not only to generate solutions, but to **instrument and improve the translation from understanding to independent technical control**.

## Mission

Create a repeatable, evidence-producing learning procedure that detects where a learner's representation of a concept breaks, changes the instructional representation or operation, and validates the result through behavior, transfer, and retention.

## Initial participant

`subject-001` is the first longitudinal design participant.

The initial context is intentionally specific:

- prior coding experience centered on JavaScript;
- no completed formal Python curriculum;
- active use of AI to build scripts/projects;
- working-code productivity can exceed unaided implementation fluency;
- desire to strengthen Python, DSA, manual code reasoning, debugging, and interview-relevant fundamentals;
- willingness to provide live, detailed feedback on confusion and breakthrough moments.

This makes the participant highly informative for the **AI-assisted productivity vs internalized competence** problem. It does not establish representativeness.

## Initial scope

- Domain: Data Structures and Algorithms
- Language: Python
- First concept family: Sliding Window
- Research design: longitudinal N=1 / single-case-inspired repeated measures
- Canonical unit: learning episode

## In scope before Research Gate R0

- transcript preservation and provenance;
- learner-event and episode schemas;
- deterministic DSA reference/state models;
- figures, Mermaid diagrams, state traces, semantic pseudocode, and code scaffolds;
- assessment and hidden-transfer fixtures;
- representation-operation experiments;
- scaffold fading;
- delayed retention measurement;
- CI and research-integrity validation;
- agent handoff/manifest;
- optional FOSSIL export design.

## Out of scope before R0

- production web/mobile app;
- broad DSA curriculum;
- generalized learner model trained from one subject;
- production video/image generation pipelines;
- public effectiveness claims;
- automated production deployment.

## Core invariant

The system must distinguish:

`what happened` from `what the learner reported` from `what the model inferred`.

## North-star outcome

The learner can solve, explain, debug, and adapt a concept **without the representation or AI scaffold that originally made it understandable**.

## Secondary outcome

The system can explain—with evidence—which representation transition failed, what intervention was applied, and what happened afterward.

## Product principle

Study OS is not a multimedia content library. It is a **representation-learning and evidence system**.
