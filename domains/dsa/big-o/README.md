# Big O Growth Families Curriculum Slice

This slice is the entry point for the DSA lane: it teaches the vocabulary of
*how much work* an approach does before any pattern is named.

It decomposes "Big O" into separately observable competencies: why growth
language comes first, constant work O(1), logarithmic work O(log n), linear work
O(n), n-log-n work O(n log n), quadratic work O(n^2), and comparing families at
the same n.

It is the precursor to arrays, two pointers, and sliding windows: those lessons
assume the learner can already say whether an approach grows flat, slowly, in
step, n-log-n, or explosively.

## Files

- `src/study_os/web/player/lessons/big-o-growth-families.v1.json` - the player
  lesson (`study-os.player-lesson.v1`) with a `growth_table` representation.

## Representation boundary

The counts in the lesson are small, deterministic, and hand-checkable. The
`growth_table` frame renders those counts; it is a teaching picture, not a
benchmark and not canonical algorithm state.

## Promotion boundary

Finishing this lesson is lesson progress, not mastery. Canonical learner
evidence and checkpoint promotion remain Study OS runtime responsibilities.

## Data boundary

No private study-log content, transcripts, or learner-identifying material is
mirrored here. This directory holds curriculum structure only.
