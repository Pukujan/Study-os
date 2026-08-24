# Measurement Model

Study OS should measure learning as a vector of capabilities, not one mastery score.

## Capability dimensions

- recognition — identify the relevant pattern or concept;
- mental_model — explain what the algorithm/data structure is doing;
- state_prediction — predict the next state/action;
- invariant_reasoning — state what remains true and why;
- procedure — describe semantic steps independent of syntax;
- pseudocode — encode the procedure structurally;
- implementation — produce correct code;
- debugging — identify and repair incorrect code/state;
- transfer — apply the concept under changed surface conditions;
- retention — retrieve/reconstruct after delay;
- ai_oversight — evaluate and correct AI-generated code/explanations.

## Assistance dimensions

Record correctness separately from assistance:

- A0 none;
- A1 reminder of task/goal;
- A2 small cue;
- A3 structural/subgoal hint;
- A4 partial representation or code scaffold;
- A5 worked example;
- A6 complete solution.

A correct answer at A5/A6 is not equivalent to a correct answer at A0.

## Representation dimensions

Record at least:

- representation family;
- representation version;
- learning operation;
- number of simultaneous representations;
- whether representation was learner-requested, tutor-selected, or experiment-assigned.

## Outcome windows

### Immediate
Within the same learning episode.

### Faded
After removing or reducing assistance.

### Transfer
Changed wording/structure requiring recognition of the same underlying concept.

### Delayed
Later session without re-showing the original lesson first.

## Self-report

Useful self-report fields:

- confidence;
- perceived difficulty;
- perceived clarity;
- perceived overload;
- explicit confusion statement;
- explicit breakthrough statement;
- learner explanation of why an intervention helped/did not help.

These should never overwrite behavioral outcomes.

## Derived diagnosis

A diagnosis should be represented as a hypothesis, for example:

```yaml
diagnosis:
  label: invariant_to_control_flow_translation_gap
  confidence: 0.62
  supported_by:
    - event-014
    - event-018
  alternatives:
    - label: python_while_loop_syntax_gap
      confidence: 0.31
  probe_needed: true
```

The tutor should test ambiguous diagnoses with a small probe before choosing a large intervention.

## Learning efficiency

Track time/effort but do not treat speed as learning.

Possible efficiency measures:

- time to first correct unaided answer;
- number of hints;
- number of failed attempts;
- number of representation changes;
- subjective effort;
- retention per minute of study.

## Promotion thresholds

### Subject observation
One event or episode.

### Repeated subject finding
Observed across multiple matched problems/sessions.

### Lesson hypothesis
A repeated subject finding judged worth testing as an instructional rule.

### Cross-subject finding
Replicated with additional participants and explicit study design.

No automated process should promote directly from one session event to universal lesson policy.