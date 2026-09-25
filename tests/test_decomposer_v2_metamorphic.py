"""SOS-0012 metamorphic tests M1-M3 (plan-property §2).

The generator is deterministic (no LLM in the loop), so no response cache is
needed. Run under pytest and unittest discover.

M1 — paraphrase invariance: rewriting the problem statement must not change
     strategy/concept sets; topology stays valid.
M2 — independent-concept reorder: permuting the declaration order of
     topologically-unrelated concepts in the spec must not change the DAG.
M3 — representation re-render: re-rendering visuals keeps step identity,
     concept sequence, goals; only presentation artifacts change.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os.decomposer import ProblemSpec, decompose, validate_decomposition  # noqa: E402
from study_os.decomposer.presentation import render_visual_as  # noqa: E402

STATEMENTS = {
    "two-sum": "Given an array of integers nums and an integer target, "
    "return the indices of the two numbers in the array that add up to the target.",
    "reverse-linked-list": "Given the head of a singly linked list, reverse the list "
    "by rewiring the next pointers and return the new head.",
    "binary-search": "Given a sorted array of integers and a target value, "
    "search the array for the target by halving the search interval each step.",
    "sliding-window-max-sum": "Given an array of integers and a window size k, "
    "find the maximum sum of any fixed-size window using a sliding window.",
}

PARAPHRASES = {
    "two-sum": [
        "You receive a list of whole numbers and one goal number; output the positions "
        "of two entries whose values combine to the goal number.",
        "Find two different elements in the numeric list whose total equals the given "
        "sum value, and report where they sit.",
        "Locate a pair of array entries that sum to the target number and give both "
        "of their indexes.",
    ],
    "reverse-linked-list": [
        "Take the front pointer of a one-way chain of nodes and flip every next "
        "pointer so the chain runs backwards; hand back the new front.",
        "Turn a singly linked sequence around by redirecting its links and return "
        "the node that used to be last.",
        "Invert the direction of a linked list by rewiring node links and provide "
        "the resulting head node.",
    ],
    "binary-search": [
        "An ascending array holds distinct values; repeatedly split the remaining "
        "range in half to locate where the wanted value lives.",
        "On an ordered list, compare the target with the middle element and discard "
        "the wrong half each round until the value is found or proven absent.",
        "Search a sorted sequence for one value by bisecting the interval between "
        "the low and high bounds at every step.",
    ],
    "sliding-window-max-sum": [
        "Slide a fixed-length frame of size k across the numbers and report the "
        "largest total the frame ever contains.",
        "Move a window that always covers k consecutive elements over the array and "
        "output the biggest possible sum inside it.",
        "Track sums of k adjacent entries as the window advances one position per "
        "step and return the maximum seen.",
    ],
}


def _spec(problem_id: str, statement: str | None = None, declared_concepts=None) -> ProblemSpec:
    return ProblemSpec(
        problem_id=problem_id,
        statement=statement or STATEMENTS[problem_id],
        declared_concepts=declared_concepts,
    )


# ------------------------------------------------------------------- M1 tests


class M1ParaphraseInvarianceTests(unittest.TestCase):
    @settings(max_examples=25, deadline=None)
    @given(st.data())
    def test_m1_stable_sets(self, data: st.DataObject) -> None:
        problem_id = data.draw(st.sampled_from(sorted(STATEMENTS)))
        paraphrase = data.draw(st.sampled_from(PARAPHRASES[problem_id]))
        base = decompose(_spec(problem_id))
        para = decompose(_spec(problem_id, paraphrase))
        self.assertEqual(set(base.concepts), set(para.concepts), "concept set must be invariant")
        self.assertEqual(
            {s.concept_id for s in base.steps},
            {s.concept_id for s in para.steps},
            "step-concept set must be invariant",
        )

    @settings(max_examples=25, deadline=None)
    @given(st.data())
    def test_m1_topo(self, data: st.DataObject) -> None:
        problem_id = data.draw(st.sampled_from(sorted(STATEMENTS)))
        paraphrase = data.draw(st.sampled_from(PARAPHRASES[problem_id]))
        para = decompose(_spec(problem_id, paraphrase))
        self.assertEqual([], validate_decomposition(para.to_dict()))

    def test_m1_paraphrase_bank_covers_all_problems(self) -> None:
        for problem_id in STATEMENTS:
            with self.subTest(problem_id=problem_id):
                self.assertGreaterEqual(len(PARAPHRASES[problem_id]), 3)
                for text in PARAPHRASES[problem_id]:
                    out = decompose(_spec(problem_id, text))
                    self.assertEqual(set(decompose(_spec(problem_id)).concepts), set(out.concepts))


# ------------------------------------------------------------------- M2 tests


class M2ReorderTests(unittest.TestCase):
    def _independent_groups(self, concepts: list[str], edges: list[tuple[str, str]]) -> list[list[str]]:
        """Group concepts that share no path via the DAG algebra."""

        reach: dict[str, set[str]] = {c: set() for c in concepts}
        adj: dict[str, set[str]] = {c: set() for c in concepts}
        for a, b in edges:
            adj[a].add(b)
        for start in concepts:
            stack, seen = list(adj[start]), set()
            while stack:
                n = stack.pop()
                if n in seen:
                    continue
                seen.add(n)
                stack.extend(adj[n])
            reach[start] = seen
        groups: list[list[str]] = []
        used: set[str] = set()
        for c in concepts:
            if c in used:
                continue
            group = [c] + [d for d in concepts if d != c and d not in reach[c] and c not in reach[d]]
            used.update(group)
            groups.append(sorted(group))
        return [g for g in groups if len(g) > 1]

    def test_m2_reorder(self) -> None:
        for problem_id in sorted(STATEMENTS):
            base_spec = _spec(problem_id)
            base = decompose(base_spec)
            edges = [(e["from"], e["to"]) for e in base.to_dict()["concept_dag"]["edges"]]
            groups = self._independent_groups(sorted(base.concepts), edges)
            self.assertTrue(groups, f"{problem_id}: expected at least one independent group")
            for group in groups:
                for perm in (list(reversed(group)),):
                    declared = [c for c in sorted(base.concepts) if c not in group]
                    # splice permuted group at the group's first original position
                    pos = min(sorted(base.concepts).index(c) for c in group)
                    declared[pos:pos] = perm
                    out = decompose(_spec(problem_id, declared_concepts=declared))
                    self.assertEqual(
                        set(base.concepts),
                        set(out.concepts),
                        f"{problem_id}: concept set invariant under reorder",
                    )
                    self.assertEqual(
                        base.to_dict()["concept_dag"]["edges"],
                        out.to_dict()["concept_dag"]["edges"],
                        f"{problem_id}: DAG edges invariant under independent-concept reorder",
                    )
                    self.assertEqual(
                        base.strategy.approach,
                        out.strategy.approach,
                        f"{problem_id}: strategy invariant under reorder",
                    )

    def test_m2_emitted_order_stays_topological_after_reorder(self) -> None:
        base = decompose(_spec("two-sum"))
        declared = list(reversed(sorted(base.concepts)))
        out = decompose(_spec("two-sum", declared_concepts=declared))
        self.assertEqual([], validate_decomposition(out.to_dict()))


# ------------------------------------------------------------------- M3 tests


class M3ReRenderTests(unittest.TestCase):
    FORMATS = ["ascii", "mermaid", "code", "none"]

    def test_m3_preservation(self) -> None:
        for problem_id in sorted(STATEMENTS):
            out = decompose(_spec(problem_id))
            for step in out.steps:
                for fmt in self.FORMATS:
                    rerendered = render_visual_as(step.visual, fmt)
                    self.assertEqual(step.step_id, rerendered.step_id)
                    self.assertEqual(step.concept_id, rerendered.concept_id)
                    self.assertEqual(step.goal, rerendered.goal)
                    self.assertEqual(fmt, rerendered.visual.format)
                    # question/example slots untouched by visual re-render
                    self.assertEqual(step.question.md, rerendered.question.md)
                    self.assertEqual(step.example.md, rerendered.example.md)

    def test_m3_render_is_deterministic(self) -> None:
        step = decompose(_spec("two-sum")).steps[0]
        first = render_visual_as(step.visual, "ascii")
        second = render_visual_as(step.visual, "ascii")
        self.assertEqual(first.visual.artifact, second.visual.artifact)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
