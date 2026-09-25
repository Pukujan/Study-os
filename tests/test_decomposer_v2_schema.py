"""SOS-0012 P1 property tests: decomposition.v2 schema + DAG acyclicity/order/coverage.

Run under both pytest and ``python -m unittest discover -s tests`` (CI).
Test ids: P1_ACYCLIC, P1_ORDER, P1_COVERAGE (plan-property §1).
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os.decomposer import DecompositionError, ProblemSpec, decompose, validate_decomposition  # noqa: E402

SCHEMA_PATH = ROOT / "schemas" / "decomposition.v2.schema.json"

PUBLIC_PROBLEMS = ("two-sum", "reverse-linked-list", "binary-search", "sliding-window-max-sum")

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


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _spec(problem_id: str, statement: str | None = None) -> ProblemSpec:
    return ProblemSpec(
        problem_id=problem_id,
        statement=statement or STATEMENTS[problem_id],
        declared_concepts=None,
    )


# ---------------------------------------------------------------- schema gate


class CanonicalOutputSchemaTests(unittest.TestCase):
    """Canonical generator output validates against the frozen v2 schema."""

    def test_canonical_output_validates_against_v2(self) -> None:
        from jsonschema import Draft202012Validator

        schema = _load_schema()
        validator = Draft202012Validator(schema)
        for problem_id in PUBLIC_PROBLEMS:
            with self.subTest(problem_id=problem_id):
                data = decompose(_spec(problem_id)).to_dict()
                errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
                self.assertEqual([], [e.message for e in errors])
                self.assertEqual([], validate_decomposition(data))

    def test_rejects_unknown_extra_property(self) -> None:
        data = decompose(_spec("two-sum")).to_dict()
        data["bogus_field"] = 1
        self.assertTrue(validate_decomposition(data))


# ------------------------------------------------------------ DAG generators


@st.composite
def _dag_shape(draw: st.DrawFn) -> tuple[list[str], list[tuple[str, str]]]:
    """Acyclic-by-construction DAG: edges only go from lower to higher index."""

    n = draw(st.integers(min_value=1, max_value=8))
    nodes = [f"n{i}" for i in range(n)]
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    edge_idx = draw(
        st.lists(st.sampled_from(pairs) if pairs else st.nothing(), max_size=min(6, len(pairs)))
    )
    edges = [(nodes[i], nodes[j]) for i, j in sorted(set(edge_idx))]
    return nodes, edges


def _decomposition_dict(nodes: list[str], edges: list[tuple[str, str]], order: list[str]) -> dict:
    node_set = set(nodes)
    assert set(order) == node_set and len(order) == len(nodes)
    return {
        "schema_version": "study-os.decomposition.v2",
        "problem_id": "p1-property",
        "problem_statement_scrubbed": "synthetic property fixture",
        "revision": "p1-property.v2",
        "strategy": {"summary": "s", "approach": "a", "invariants": []},
        "concept_dag": {
            "nodes": [{"concept_id": n, "label": n.upper()} for n in nodes],
            "edges": [{"from": a, "to": b} for a, b in edges],
        },
        "learning_order": order,
        "steps": [
            {
                "step_id": f"step-{n}",
                "step_index": i,
                "concept_id": n,
                "goal": f"reach {n}",
                "presentation": {
                    "question": {"md": f"What does {n} establish?"},
                    "example": {"md": f"Worked example for {n}."},
                    "visual": {"format": "none", "artifact": "", "caption": None},
                },
            }
            for i, n in enumerate(order)
        ],
        "provenance": {
            "module_version": "decomposer-v2.1",
            "generator": "deterministic",
            "route": "deterministic:template",
            "model": None,
            "prompt_sha256": None,
            "problem_sha256": None,
            "created_at": "2026-09-25T00:00:00+00:00",
        },
    }


def _kahn_order(nodes: list[str], edges: list[tuple[str, str]], tie_break: int) -> list[str]:
    """Deterministic randomized Kahn (tie-break by arithmetic jitter of tie_break)."""

    remaining = set(nodes)
    indeg = {n: 0 for n in nodes}
    out: dict[str, list[str]] = {n: [] for n in nodes}
    for a, b in edges:
        indeg[b] += 1
        out[a].append(b)
    order: list[str] = []
    while remaining:
        ready = sorted(n for n in remaining if indeg[n] == 0)
        pick = ready[(tie_break + len(order)) % len(ready)]
        order.append(pick)
        remaining.discard(pick)
        for nxt in out[pick]:
            indeg[nxt] -= 1
    return order


class P1AcyclicTests(unittest.TestCase):
    @settings(max_examples=50, deadline=None)
    @given(data=st.data(), inject_cycle=st.booleans(), tie_break=st.integers(0, 1000))
    def test_p1_acyclic(self, data: st.DataObject, inject_cycle: bool, tie_break: int) -> None:
        nodes, edges = data.draw(_dag_shape())
        if inject_cycle:
            if len(nodes) < 2:
                return
            edges = sorted(set(edges) | {(nodes[1], nodes[0])})
            errors = validate_decomposition(_decomposition_dict(nodes, edges, nodes))
            self.assertTrue(errors, "cycle edge must be rejected")
        else:
            order = _kahn_order(nodes, edges, tie_break)
            self.assertEqual([], validate_decomposition(_decomposition_dict(nodes, edges, order)))


class P1OrderTests(unittest.TestCase):
    @settings(max_examples=50, deadline=None)
    @given(data=st.data(), tie_break=st.integers(0, 1000))
    def test_p1_order(self, data: st.DataObject, tie_break: int) -> None:
        nodes, edges = data.draw(_dag_shape())
        order = _kahn_order(nodes, edges, tie_break)
        # Valid topological order must be accepted.
        self.assertEqual([], validate_decomposition(_decomposition_dict(nodes, edges, order)))
        # Any topological violation must be rejected: a reversed order breaks the
        # chain edge n0->n1 whenever at least one edge exists (ensure one).
        edges_with_chain = sorted(set(edges) | {(nodes[0], nodes[-1])}) if len(nodes) > 1 else edges
        if len(nodes) > 1:
            reversed_order = list(reversed(order))
            errors = validate_decomposition(
                _decomposition_dict(nodes, edges_with_chain, reversed_order)
            )
            self.assertTrue(errors, "non-topological learning_order must be rejected")


class P1CoverageTests(unittest.TestCase):
    @settings(max_examples=25, deadline=None)
    @given(data=st.data(), tie_break=st.integers(0, 1000))
    def test_p1_coverage_unknown_step_concept(self, data: st.DataObject, tie_break: int) -> None:
        nodes, edges = data.draw(_dag_shape())
        order = _kahn_order(nodes, edges, tie_break)
        payload = _decomposition_dict(nodes, edges, order)
        payload["steps"][0]["concept_id"] = "zz-unknown-concept"
        errors = validate_decomposition(payload)
        self.assertTrue(any("concept" in e.lower() for e in errors))

    @settings(max_examples=25, deadline=None)
    @given(data=st.data(), tie_break=st.integers(0, 1000))
    def test_p1_coverage_every_concept_needs_a_step(self, data: st.DataObject, tie_break: int) -> None:
        nodes, edges = data.draw(_dag_shape())
        if len(nodes) < 2:
            return
        order = _kahn_order(nodes, edges, tie_break)
        payload = _decomposition_dict(nodes, edges, order)
        payload["steps"] = payload["steps"][:-1]  # drop one step -> uncovered node
        for i, step in enumerate(payload["steps"]):
            step["step_index"] = i
        errors = validate_decomposition(payload)
        self.assertTrue(any("cover" in e.lower() for e in errors))

    def test_p1_coverage_step_index_must_be_contiguous(self) -> None:
        nodes, edges = ["a", "b"], [("a", "b")]
        payload = _decomposition_dict(nodes, edges, ["a", "b"])
        payload["steps"][1]["step_index"] = 7
        errors = validate_decomposition(payload)
        self.assertTrue(any("step_index" in e for e in errors))

    def test_decompose_raises_on_cycle(self) -> None:
        # The generator itself can never emit a cycle; order.toposort guards it.
        from study_os.decomposer import order as order_mod

        with self.assertRaises(DecompositionError):
            order_mod.toposort(["a", "b"], [("a", "b"), ("b", "a")])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
