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
