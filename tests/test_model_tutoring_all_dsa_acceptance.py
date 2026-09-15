from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

import check_model_tutoring_all_dsa as checker  # noqa: E402
import run_model_tutoring_all_dsa as runner  # noqa: E402


SCENARIO = {
    "id": "toy-acceptance",
    "title": "Toy acceptance problem",
    "problem": "Determine whether the input has the required property.",
    "variables": ["items", "cursor", "bucket"],
    "visual_family": "array-trace",
    "forbidden_aliases": ["renamed_bucket"],
    "turns": [
        {"learner_message": "I can explain the input pattern.", "learner_signal": "clarification", "expected": {"must_include_any": ["items"]}},
        {"learner_message": "The state is accumulated in bucket.", "learner_signal": "recovery_or_check", "expected": {"must_include_any": ["bucket"]}},
    ],
}


def make_artifacts(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    class Student:
        def ask(self, payload: dict[str, Any]) -> dict[str, Any]:
            return {"student_message": payload["conversation"][0]["content"] if payload["conversation"] else "I can explain the input pattern."}

        def close(self) -> None:
            pass

    class Teacher:
        def ask(self, payload: dict[str, Any]) -> dict[str, Any]:
            if payload["phase"] == "decomposition":
                plan = {
                    "schema_version": "study-os.teaching-plan.v0.1",
                    "problem": {"id": SCENARIO["id"], "statement": SCENARIO["problem"]},
                    "concepts": [
                        {"id": "recognize", "prerequisites": [], "allowed_variables": ["items", "cursor"], "representation_requirement_ids": ["trace-items"], "semantic_invariant_ids": ["items-stable"], "completion_evidence_ids": ["items-evidence"]},
                        {"id": "track", "prerequisites": ["recognize"], "allowed_variables": ["items", "cursor", "bucket"], "representation_requirement_ids": ["trace-bucket"], "semantic_invariant_ids": ["bucket-stable"], "completion_evidence_ids": ["bucket-evidence"]},
                    ],
                    "variables": {"items": {"role": "collection", "meaning": "input"}, "cursor": {"role": "index", "meaning": "current position"}, "bucket": {"role": "state", "meaning": "accumulated values"}},
                    "representation_requirements": [
                        {"id": "trace-items", "kind": "stateful", "operation": "trace", "description": "Trace the input items and current position.", "required": True},
                        {"id": "trace-bucket", "kind": "stateful", "operation": "trace", "description": "Trace the accumulated bucket state.", "required": True},
                    ],
                    "semantic_invariants": [
                        {"id": "items-stable", "concept_id": "recognize", "statement": "Items remain tied to the input."},
                        {"id": "bucket-stable", "concept_id": "track", "statement": "Bucket contains accumulated values."},
                    ],
                    "completion_evidence": [
                        {"id": "items-evidence", "concept_id": "recognize", "evidence_type": "explanation", "description": "Learner explains items."},
                        {"id": "bucket-evidence", "concept_id": "track", "evidence_type": "explanation", "description": "Learner explains bucket."},
                    ],
                    "terminal_behavior": ["Explain the accumulated bucket state."],
                    "assistance_ceiling": "A1",
                }
                return {"teacher_message": json.dumps(plan)}
            if payload["phase"] == "diagnosis":
                learner = payload["learner_message"]
                return {"teacher_message": json.dumps({"diagnosis": {"diagnosis_family": "concept_failure", "operation": "probe", "assistance_level": "A0"}, "assessment": {"learner_outcome": "demonstrated", "evidence_quote": learner, "rationale": "evidence"}})}
            requirement = payload["generation_contract"]["representation_requirements"][0]
            variable = payload["generation_contract"]["allowed_variables"][0]
            return {"teacher_message": json.dumps({"response": f"| {variable} |\nstateful trace: {variable}; {requirement['id']}\n?"})}

        def close(self) -> None:
            pass

    paths = {"transcript_path": root / "transcript.jsonl", "markdown_path": root / "transcript.md", "trace_path": root / "trace.jsonl", "plans_path": root / "plans.jsonl"}
    result = runner.run_all_dsa({"scenarios": [SCENARIO]}, Student(), Teacher(), scenario_ids={SCENARIO["id"]}, turns_per_scenario=2, allow_short_run=True, **paths)
    return result


class AllDSAAcceptanceTests(unittest.TestCase):
    def test_valid_evidence_passes_and_calibration_is_reported(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            transcript, trace, plans = make_artifacts(root)
            report = checker.evaluate({"scenarios": [SCENARIO]}, transcript, trace, plans, scenario_ids={SCENARIO["id"]}, allow_short_run=True)
            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["visible_message_count"], 4)
            self.assertGreaterEqual(report["calibration"]["checks"], 1)

    def test_mutations_are_killed_by_the_gate(self) -> None:
        mutations = ("teacher_message", "evidence_quote", "advance_state")
        for mutation in mutations:
            with self.subTest(mutation=mutation), TemporaryDirectory() as directory:
                root = Path(directory)
                transcript, trace, plans = make_artifacts(root)
                if mutation == "teacher_message":
                    transcript[0]["teacher_message"] = "prose only"
                elif mutation == "evidence_quote":
                    transcript[0]["model_assessment"]["evidence_quote"] = "fabricated"
                else:
                    transcript[0]["controller_state_after"]["concept_index"] = 2
                report = checker.evaluate({"scenarios": [SCENARIO]}, transcript, trace, plans, scenario_ids={SCENARIO["id"]}, allow_short_run=True)
                self.assertEqual(report["status"], "failed")
                self.assertTrue(report["failures"])

    def test_forbidden_alias_and_trace_drift_are_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            transcript, trace, plans = make_artifacts(root)
            transcript[0]["teacher_message"] += " renamed_bucket"
            report = checker.evaluate({"scenarios": [SCENARIO]}, transcript, trace, plans, scenario_ids={SCENARIO["id"]}, allow_short_run=True)
            self.assertEqual(report["status"], "failed")
            trace[0]["advance"] = not trace[0]["advance"]
            report = checker.evaluate({"scenarios": [SCENARIO]}, transcript, trace, plans, scenario_ids={SCENARIO["id"]}, allow_short_run=True)
            self.assertEqual(report["status"], "failed")

    def test_metamorphic_public_problem_payload_preserves_variables(self) -> None:
        paraphrase = copy.deepcopy(SCENARIO)
        paraphrase["problem"] = "Decide if the supplied input satisfies the property."
        payload = runner.build_decomposer_payload(paraphrase)
        self.assertEqual(payload["variable_names"], SCENARIO["variables"])
        self.assertNotIn("expected", payload)
        numeric = copy.deepcopy(SCENARIO)
        numeric["problem"] = "Determine whether input [4, 7, 4] has the required property."
        self.assertEqual(runner.build_decomposer_payload(numeric)["declared_variable_names"], SCENARIO["variables"])

    def test_completion_driven_gate_requires_final_evidence_marker(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            transcript, trace, plans = make_artifacts(root)
            report = checker.evaluate(
                {"scenarios": [SCENARIO]}, transcript, trace, plans,
                scenario_ids={SCENARIO["id"]}, allow_short_run=True,
                completion_driven=True, max_exchanges_per_problem=10,
            )
            self.assertEqual(report["status"], "passed")
            transcript[-1]["completion_candidate"] = False
            report = checker.evaluate(
                {"scenarios": [SCENARIO]}, transcript, trace, plans,
                scenario_ids={SCENARIO["id"]}, allow_short_run=True,
                completion_driven=True, max_exchanges_per_problem=10,
            )
            self.assertEqual(report["status"], "failed")
            self.assertTrue(any(item["category"] == "INCOMPLETE_PLAN" for item in report["failures"]))


if __name__ == "__main__":
    unittest.main()
