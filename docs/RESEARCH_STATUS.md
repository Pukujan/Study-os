# Research Status

## Current conclusion

There is enough external evidence to justify a **small research prototype**, but not enough evidence to justify building a broad adaptive/multimodal DSA platform yet.

The most defensible thesis is narrower than “people learn better visually”:

> Different technical tasks expose different representation bottlenecks. Structured AI may help diagnose and scaffold those bottlenecks, but improvement must be validated through active behavior, scaffold fading, transfer, and retention.

## Evidence supporting a prototype

- worked examples and subgoal labels can help novices acquire procedural schemas;
- active prediction/explanation around program visualization can be more useful than passive viewing;
- retrieval and spacing improve durable retention;
- carefully structured AI tutoring can produce strong learning results in some contexts;
- AI-assisted programming research highlights a real risk of overreliance and a continuing need for debugging, logic, and code-comprehension skills;
- single-case methodology provides tools for disciplined repeated measurement within one participant.

## Evidence cautioning against the naive version

- fixed learning-style matching is unsupported;
- more representations can increase cognitive load or redundancy;
- visualization effects are mixed and depend on learner engagement/design;
- AI tutors can hallucinate or scaffold poorly without external structure;
- self-report and perceived usefulness can diverge from actual learning;
- AI-generated code can be difficult for students to evaluate/correct;
- Subject 001 cannot establish population generality.

## Recommended action

Do not build the broad product yet.

Build only enough deterministic infrastructure to run Research Gate R0 on Sliding Window, then allow the evidence to decide what the product should become.

## Key decision rule

When evidence conflicts with the original vision, change the vision before changing the evidence.