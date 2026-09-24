# Sliding Window

First Study OS concept family.

This folder owns concept- and lesson-level material for Sliding Window. It must not contain Subject 001's raw session evidence.

Planned structure:

```text
sliding-window/
  concept.yaml
  knowledge/
  lessons/
    001-window-as-region/
    002-maintaining-validity/
    003-invariant-to-code/
  problems/
  assessments/
```

## Initial learning transitions

Study OS should separately test:

1. problem statement -> recognize contiguous-window structure;
2. pattern -> mental model of a moving region;
3. mental model -> invariant;
4. invariant -> state transitions (`expand`, `detect violation`, `shrink`, `record`);
5. state transitions -> semantic pseudocode;
6. pseudocode -> Python;
7. known examples -> unfamiliar transfer problems.

## Initial representation set

- concise prose;
- pointer/array figure;
- Mermaid decision/flow diagram;
- explicit state trace;
- invariant phrased in technical and plain language;
- semantic operation blocks;
- pseudocode;
- Python scaffold;
- blank implementation.

Representations must be versioned independently and linked to learning events when used.

## Goldens and the shipped lesson

`golden/` holds learner-calibrated teaching sequences from live Study OS use. The shipped PIR lesson for `sliding-window.max-sum-k.sep4.v1` (`src/study_os/pir/sliding_window.py`) is generated from them step by step, and its scope stops where they stop (`enumerate(a)` and `append`).

`golden/conformance-oracle.v0.1.json` records the golden order, representation rules, forbidden future concepts, and mastery policy. It pins the sha256 of each golden and the `Pukujan/study-os-benchmarker` commit whose rules it mirrors. `tests/test_pir_golden_conformance.py` runs `src/study_os/pir/conformance.py` against the shipped asset and against targeted mutations. If you edit a golden, update the lesson and the oracle hash in the same change.
