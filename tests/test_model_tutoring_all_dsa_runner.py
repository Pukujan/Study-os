from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

import run_model_tutoring_all_dsa as runner  # noqa: E402
from study_os.prompt_registry import (  # noqa: E402
    DEFAULT_PROMPT_REGISTRY,
    DECOMPOSITION_PROMPT_VERSION,
)
from study_os.teaching_plan import TEACHING_PLAN_SCHEMA_VERSION  # noqa: E402


SCENARIO = {
    "id": "toy-problem",
    "title": "Toy Problem",
    "problem": "Determine whether the input has the required property.",
    "variables": ["items", "cursor", "bucket", "answer"],
    "turns": [{"learner_message": "placeholder", "learner_signal": "clarification"}],
}


def plan_payload() -> dict[str, Any]:
    return {
        "schema_version": TEACHING_PLAN_SCHEMA_VERSION,
        "problem": {"id": SCENARIO["id"], "statement": SCENARIO["problem"]},
        "concepts": [
            {
                "id": "recognize-pattern",
                "prerequisites": [],
                "allowed_variables": ["items", "cursor"],
                "representation_requirement_ids": ["trace-pattern"],
                "semantic_invariant_ids": ["pattern-stable"],
                "completion_evidence_ids": ["pattern-evidence"],
            },
            {
                "id": "track-state",
                "prerequisites": ["recognize-pattern"],
                "allowed_variables": ["items", "cursor", "bucket"],
                "representation_requirement_ids": ["trace-state"],
                "semantic_invariant_ids": ["state-stable"],
                "completion_evidence_ids": ["state-evidence"],
            },
            {
                "id": "decide-result",
                "prerequisites": ["track-state"],
                "allowed_variables": ["items", "cursor", "bucket", "answer"],
                "representation_requirement_ids": ["trace-result"],
                "semantic_invariant_ids": ["result-stable"],
                "completion_evidence_ids": ["result-evidence"],
            },
        ],
        "variables": {
            "items": {"role": "collection", "meaning": "the input values"},
            "cursor": {"role": "index", "meaning": "the current position"},
            "bucket": {"role": "collection", "meaning": "accumulated state"},
            "answer": {"role": "result", "meaning": "the final result"},
        },
        "representation_requirements": [
            {
                "id": "trace-pattern",
                "kind": "stateful",
                "operation": "trace",
                "description": "Trace the input and current position.",
                "required": True,
            },
            {
                "id": "trace-state",
                "kind": "stateful",
                "operation": "trace",
                "description": "Trace the accumulated state.",
                "required": True,
            },
            {
                "id": "trace-result",
                "kind": "formal",
                "operation": "explain",
                "description": "Explain the result.",
                "required": True,
            },
        ],
        "semantic_invariants": [
            {
                "id": "pattern-stable",
                "concept_id": "recognize-pattern",
                "statement": "The pattern remains tied to the input.",
            },
            {
                "id": "state-stable",
                "concept_id": "track-state",
                "statement": "The state contains accumulated information.",
            },
            {
                "id": "result-stable",
                "concept_id": "decide-result",
                "statement": "The result follows from the state.",
            },
        ],
        "completion_evidence": [
            {
                "id": "pattern-evidence",
                "concept_id": "recognize-pattern",
                "evidence_type": "explanation",
                "description": "The learner explains the pattern.",
            },
            {
                "id": "state-evidence",
                "concept_id": "track-state",
                "evidence_type": "explanation",
                "description": "The learner explains the state.",
            },
            {
                "id": "result-evidence",
                "concept_id": "decide-result",
                "evidence_type": "explanation",
                "description": "The learner explains the result.",
            },
        ],
        "terminal_behavior": ["Explain the final result after the state is established."],
        "assistance_ceiling": "A1",
        # parse_plan_response replaces this runtime-owned provenance.
        "provenance": {
            "prompt_version": DECOMPOSITION_PROMPT_VERSION,
            "prompt_hash": DEFAULT_PROMPT_REGISTRY.get(DECOMPOSITION_PROMPT_VERSION).prompt_hash,
            "model_identifier": "fake",
            "teaching_plan_schema_version": TEACHING_PLAN_SCHEMA_VERSION,
            "turn_trace_schema_version": runner.TRACE_SCHEMA_VERSION,
            "run_id": "fake-run",
            "source_problem_id": SCENARIO["id"],
        },
    }


class FakeStudent:
    def __init__(self) -> None:
        self.payloads: list[dict[str, Any]] = []

    def ask(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.payloads.append(payload)
        return {"student_message": f"I can explain turn {payload['turn_index']}"}

    def close(self) -> None:
        pass


class FakeTeacher:
    def __init__(self) -> None:
        self.payloads: list[dict[str, Any]] = []

    def ask(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.payloads.append(payload)
        phase = payload["phase"]
        if phase == "decomposition":
            return {"teacher_message": json.dumps(plan_payload())}
        if phase == "diagnosis":
            message = payload["learner_message"]
            return {
                "teacher_message": json.dumps(
                    {
                        "diagnosis": {
                            "diagnosis_family": "concept_failure",
                            "operation": "probe",
                            "assistance_level": "A0",
                            "decomposition": "check one concept",
                        },
                        "assessment": {
                            "learner_outcome": "demonstrated",
                            "evidence_quote": message,
                            "rationale": "the learner stated the concept",
                        },
                    }
                )
            }
        requirement = payload["generation_contract"]["representation_requirements"][0]
        allowed = payload["generation_contract"]["allowed_variables"]
        return {
            "teacher_message": json.dumps(
                {
                    "response": (
                        f"Representation: {requirement['id']}\n"
                        f"{requirement['kind']} {requirement['operation']}: {allowed[0]}\n?"
                    )
                }
            )
        }

    def close(self) -> None:
        pass


class AllDSARunnerTests(unittest.TestCase):
    def test_public_payloads_do_not_forward_hidden_annotations_to_teacher(self) -> None:
        student_payload = runner.raw.build_student_payload(
            SCENARIO, turn_index=0, conversation=[]
        )
        decomposer_payload = runner.build_decomposer_payload(SCENARIO)
        self.assertNotIn("expected", decomposer_payload)
        self.assertNotIn("learner_signal", decomposer_payload)

        # The learner signal is student-only. Diagnosis and generation receive the
        # actual learner message and generic plan contract, never corpus assertions.
        teacher = FakeTeacher()
        plan = runner.parse_plan_response(
            json.dumps(plan_payload()),
            scenario=SCENARIO,
            run_id="run-1",
            model_identifier="fake-model",
        )
        controller = runner.GenericModelTutoringController(plan)
        auth = runner._diagnose(
            teacher=teacher,
            scenario=SCENARIO,
            controller=controller,
            turn_index=0,
            learner_message="I can explain turn 0",
            conversation=[{"role": "learner", "content": "I can explain turn 0"}],
        )
        runner._generate(
            teacher=teacher,
            scenario=SCENARIO,
            authorization=auth,
            learner_message="I can explain turn 0",
            conversation=[],
            prompt_registry=DEFAULT_PROMPT_REGISTRY,
        )
        self.assertIn("learner_signal", student_payload)
        for payload in teacher.payloads:
            self.assertNotIn("learner_signal", payload)
            self.assertNotIn("expected", payload)

    def test_plan_parser_binds_source_and_runtime_provenance(self) -> None:
        plan = runner.parse_plan_response(
            json.dumps(plan_payload()),
            scenario=SCENARIO,
            run_id="run-42",
            model_identifier="gpt-5.6-luna",
        )
        self.assertEqual(plan.problem.id, SCENARIO["id"])
        self.assertEqual(plan.provenance.run_id, "run-42")
        self.assertEqual(plan.provenance.model_identifier, "gpt-5.6-luna")

        wrong = plan_payload()
        wrong["problem"]["id"] = "other-problem"
        with self.assertRaises(Exception):
            runner.parse_plan_response(
                json.dumps(wrong),
                scenario=SCENARIO,
                run_id="run-42",
                model_identifier="fake",
            )

    def test_teacher_parser_requires_completed_resolve_problem(self) -> None:
        actor = object.__new__(runner.AllDSATeacherActor)
        actor.mcp_name = "study-os-local-test"
        message = json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "ok"}})
        with self.assertRaises(RuntimeError):
            actor._parse_events(message)
        events = "\n".join(
            [
                json.dumps({"type": "thread.started", "thread_id": "t1"}),
                message,
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {
                            "type": "mcp_tool_call",
                            "server": "study-os-local-test",
                            "tool": "resolve_problem",
                            "status": "completed",
                        },
                    }
                ),
            ]
        )
        thread_id, text, completed, errors = actor._parse_events(events)
        self.assertEqual((thread_id, text, completed, errors), ("t1", "ok", True, []))

    def test_short_run_checkpoints_and_resumes_without_duplicate_turns(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {
                "transcript_path": root / "transcript.jsonl",
                "markdown_path": root / "transcript.md",
                "trace_path": root / "trace.jsonl",
                "plans_path": root / "plans.jsonl",
            }
            student = FakeStudent()
            teacher = FakeTeacher()
            first = runner.run_all_dsa(
                {"scenarios": [SCENARIO]},
                student,
                teacher,
                scenario_ids={SCENARIO["id"]},
                turns_per_scenario=2,
                allow_short_run=True,
                **paths,
            )
            self.assertEqual(len(first[0]), 2)
            self.assertEqual(len(first[1]), 2)
            self.assertEqual(len(first[2]), 1)
            self.assertEqual(first[0][0]["controller_state_after"]["concept_index"], 1)
            self.assertEqual(first[0][0]["schema_version"], runner.TRANSCRIPT_SCHEMA_VERSION)
            self.assertEqual(first[1][0]["schema_version"], runner.TRACE_SCHEMA_VERSION)

            resumed = runner.run_all_dsa(
                {"scenarios": [SCENARIO]},
                FakeStudent(),
                FakeTeacher(),
                scenario_ids={SCENARIO["id"]},
                turns_per_scenario=3,
                allow_short_run=True,
                **paths,
            )
            self.assertEqual(len(resumed[0]), 3)
            self.assertEqual(len(resumed[1]), 3)
            self.assertEqual(len({row["turn_index"] for row in resumed[0]}), 3)
            self.assertEqual(len(resumed[2]), 1)
            self.assertTrue(paths["transcript_path"].exists())
            self.assertTrue(paths["markdown_path"].exists())


if __name__ == "__main__":
    unittest.main()
