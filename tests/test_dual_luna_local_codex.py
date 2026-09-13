from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import run_dual_luna_local_codex as local  # noqa: E402


class FakeRunner:
    def __init__(self, outputs: list[str]) -> None:
        self.outputs = list(outputs)
        self.calls: list[dict[str, Any]] = []

    def __call__(self, args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        self.calls.append({"args": args, **kwargs})
        if not self.outputs:
            raise AssertionError("fake runner has no remaining output")
        return subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout=self.outputs.pop(0),
            stderr="",
        )


def events(thread_id: str, message: str) -> str:
    return (
        '{"type":"thread.started","thread_id":"'
        + thread_id
        + '"}\n'
        + '{"type":"item.completed","item":{"type":"agent_message","text":"'
        + message
        + '"}}\n'
    )


def payload(scenario_id: str = "two-sum-dictionary") -> dict[str, Any]:
    return {
        "type": "dual_luna_student_turn",
        "scenario_id": scenario_id,
        "title": "Two Sum",
        "problem": "Given nums and target, return two indices.",
        "turn_index": 0,
        "learner_signal": "clarification",
        "instruction": "act as learner",
        "conversation": [],
    }


class DualLunaLocalCodexTests(unittest.TestCase):
    def test_new_session_then_resume_same_thread_without_child_tasks(self) -> None:
        fake = FakeRunner(
            [
                events("thread-student-1", "wait what are we finding?"),
                events("thread-student-1", "so indexes not values?"),
            ]
        )
        actor = local.CodexCliActor(role="student", runner=fake)

        first = actor.ask(payload())
        second = actor.ask(payload())

        self.assertEqual(first["student_message"], "wait what are we finding?")
        self.assertEqual(second["student_message"], "so indexes not values?")
        self.assertIn("--dangerously-bypass-approvals-and-sandbox", fake.calls[0]["args"])
        self.assertNotIn("resume", fake.calls[0]["args"])
        self.assertIn("resume", fake.calls[1]["args"])
        self.assertIn("thread-student-1", fake.calls[1]["args"])

    def test_new_problem_gets_fresh_conversation(self) -> None:
        fake = FakeRunner(
            [
                events("thread-one", "first"),
                events("thread-two", "second"),
            ]
        )
        actor = local.CodexCliActor(role="student", runner=fake)

        actor.ask(payload("problem-one"))
        actor.ask(payload("problem-two"))

        self.assertNotIn("resume", fake.calls[0]["args"])
        self.assertNotIn("resume", fake.calls[1]["args"])

    def test_resume_thread_mismatch_fails_closed(self) -> None:
        fake = FakeRunner(
            [
                events("thread-one", "first"),
                events("unexpected-new-thread", "second"),
            ]
        )
        actor = local.CodexCliActor(role="student", runner=fake)
        actor.ask(payload())

        with self.assertRaisesRegex(RuntimeError, "different thread id"):
            actor.ask(payload())

    def test_teacher_contract_requires_real_study_os_path(self) -> None:
        fake = FakeRunner([events("teacher-thread", "visible teaching turn")])
        actor = local.CodexCliActor(role="teacher", runner=fake)
        teacher_payload = payload()
        teacher_payload["type"] = "dual_luna_teacher_turn"
        teacher_payload["learner_message"] = "help"

        result = actor.ask(teacher_payload)

        self.assertEqual(result["teacher_message"], "visible teaching turn")
        sent_prompt = fake.calls[0]["input"]
        self.assertIn("Study OS MCP/product path", sent_prompt)
        self.assertIn("Do not edit the repository", sent_prompt)

    def test_sandbox_can_be_kept_when_explicitly_requested(self) -> None:
        fake = FakeRunner([events("thread-one", "hello")])
        actor = local.CodexCliActor(role="student", full_access=False, runner=fake)
        actor.ask(payload())

        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", fake.calls[0]["args"])


if __name__ == "__main__":
    unittest.main()
