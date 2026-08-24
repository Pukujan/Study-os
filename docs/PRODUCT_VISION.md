# Product Vision

## Mission

Help a learner develop durable technical understanding by detecting where translation between representations breaks and adapting the learning operation until the learner can perform independently.

Study OS does not optimize for producing answers quickly. It optimizes for **independent reconstruction, debugging, transfer, and retention** while still allowing AI to act as a powerful scaffold.

## First problem

The first target is DSA learning in Python for an AI-assisted programmer who can often make software work through generated guidance but wants stronger manual understanding of algorithms, code execution, debugging, and implementation.

This is a particularly relevant learning problem in an AI-heavy programming environment: code generation reduces the cost of syntax production, but it does not remove the need to judge whether code is correct, understand state and complexity, repair subtle failures, or adapt a solution to a new requirement.

## Subject 001

Subject 001 is the initial design participant and longitudinal case study.

Public-safe context:

- prior coding experience centered on JavaScript;
- no completed formal Python learning sequence;
- substantial use of AI in technical projects;
- can often create or repair scripts with AI support;
- explicitly wants to increase unaided Python/DSA fluency rather than reject AI assistance;
- able to report live when an explanation fails, which representation is confusing, and what change makes a concept click;
- willing to repeat assessments later so retention and transfer can be measured.

This profile is valuable because Study OS is trying to understand the boundary between **AI-assisted productivity** and **internalized procedural competence**.

Subject 001 is not described as a representative sample or proof of general effectiveness.

## Core product thesis

A tutoring system should not merely ask:

> Does the learner know Sliding Window?

It should be able to ask:

> Can the learner recognize a contiguous-range problem?
> Can they model the changing window state?
> Can they state the invariant?
> Can they predict the next transition?
> Can they translate the invariant into semantic control flow?
> Can they translate that procedure into Python?
> Can they debug a flawed version?
> Can they recognize the pattern again when the problem looks different?
> Can they still do it later without the tutor?

A learning failure may occur between any two of those representations.

## What AI should do

AI is useful for:

- expanding expert-compressed explanations;
- generating targeted probe questions;
- translating a concept between representations;
- adapting explanation detail;
- asking Socratic/prediction questions;
- producing alternative examples;
- explaining errors after the learner attempts a solution;
- extracting proposed learning events from session transcripts;
- summarizing longitudinal evidence;
- proposing the next experiment.

AI should **not** be trusted alone for:

- canonical algorithm correctness;
- deciding mastery from conversational fluency;
- silently labeling learner state as fact;
- protecting hidden evaluation sets;
- deciding that a subject-specific result generalizes;
- enforcing all pedagogical sequencing solely through a prompt.

## Why manual coding still matters in an AI-assisted workflow

“Manual coding” here does not mean memorizing every method name or banning autocomplete. It means maintaining enough internal competence to:

- trace execution;
- reason about state and invariants;
- recognize algorithmic structure;
- construct small solutions without generated completion;
- understand generated code;
- test it;
- detect logic errors;
- debug it;
- compare alternatives;
- explain tradeoffs;
- modify behavior when requirements change.

The desired outcome is **AI leverage with human technical control**, not AI abstinence.

## Product loop

```text
attempt
  -> observe
  -> diagnose hypothesis
  -> probe
  -> choose representation + operation
  -> learner acts
  -> assess behavior
  -> fade assistance
  -> transfer
  -> delay
  -> update learner evidence
```

## Long-term vision

If the DSA slice works, the architecture may eventually support other representation-heavy domains such as:

- ML/math concepts;
- graph theory;
- databases;
- distributed systems;
- formal methods;
- systems/networking;
- statistics;
- technical interview preparation.

The project should only expand after the procedure—not merely the content—demonstrates value.