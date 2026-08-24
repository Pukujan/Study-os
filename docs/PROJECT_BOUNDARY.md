# Project Boundary

## Mission

Build a repeatable learning procedure that can observe where a learner succeeds or fails while translating a technical concept between representations, adapt the representation, and test whether the change produces durable understanding and transfer.

The first research domain is Data Structures & Algorithms (DSA).

## Core research object

The system studies **representation transitions**, for example:

- problem statement -> pattern recognition;
- pattern -> mental model;
- mental model -> invariant;
- invariant -> state transition;
- state transition -> pseudocode;
- pseudocode -> code;
- code -> debugging;
- known problem -> novel transfer.

A learner can be strong in one transition and weak in another. Study OS must not collapse these into a single mastery score.

## Initial learner dimensions

Track evidence separately for:

1. recognition;
2. mental model;
3. state prediction;
4. invariant explanation;
5. pseudocode reconstruction;
6. implementation;
7. debugging;
8. transfer;
9. delayed retention.

## Representation families

### Textual
- concise explanation;
- causal explanation;
- analogy;
- Socratic prompt.

### Structural
- Mermaid flowchart;
- dependency graph;
- decision tree;
- concept map.

### Stateful
- array + pointers;
- queue/stack state;
- recursion tree;
- execution/state trace;
- deterministic animation.

### Formal
- invariant;
- precondition/postcondition;
- complexity;
- proof sketch.

### Procedural
- semantic operations;
- pseudocode;
- scaffolded code;
- executable code.

### Multimodal (later)
- narrated audio;
- generated illustration;
- generated/assembled video.

Authoritative algorithm state should use deterministic representations before generative media.

## Representation operations

Study OS should record not only the modality but the operation performed on the knowledge:

- TRANSLATE — code -> diagram, diagram -> prose, etc.;
- DECOMPOSE — break an algorithm into smaller state transitions;
- EXPAND — expose compressed expert reasoning;
- CONTRAST — compare nearby concepts;
- TRACE — execute a concrete example;
- HIDE — remove assistance for retrieval;
- PREDICT — ask for the next state/action;
- RECONSTRUCT — recreate a representation from memory;
- ABSTRACT — concrete example -> general rule/invariant;
- SPECIALIZE — general rule -> concrete instance;
- TRANSFER — apply the concept to a changed surface problem.

## Difficulty model

Do not equate difficulty with LeetCode Easy/Medium/Hard.

Use learning-operation levels:

- L0 Observe
- L1 Predict
- L2 Explain
- L3 Reconstruct
- L4 Pseudocode
- L5 Scaffolded code
- L6 Blank implementation
- L7 Debug
- L8 Recognize in an unfamiliar problem
- L9 Transfer to changed surface form
- L10 Derive/modify under a new constraint

A learner may occupy different levels for different representation transitions.

## First vertical slice

### Domain
DSA / Python

### Concept family
Sliding Window

### Initial representation set
- plain explanation;
- static pointer figure;
- Mermaid flowchart;
- explicit state trace;
- invariant;
- semantic pseudocode;
- Python scaffold;
- blank Python implementation.

### Initial evidence loop

`attempt -> confusion/failure -> learner explanation -> representation change -> immediate assessment -> no-help reconstruction -> hidden transfer -> delayed retention`

## Non-goals for v0.1

- proving a universal theory of learning;
- supporting many learners;
- building a polished course marketplace;
- generating large amounts of lesson content;
- making FOSSIL or a knowledge graph a runtime dependency;
- using video/image generation before deterministic learning representations are measured.

## Success criterion for v0.1

Given one longitudinal learner, Study OS can preserve enough evidence to answer:

1. Where did the learner fail?
2. Which representation/operation was changed?
3. What did the learner report changed in their understanding?
4. Did objective behavior improve immediately?
5. Did the improvement survive assistance removal?
6. Did it transfer to an unseen problem?
7. Did it persist after a delay?
