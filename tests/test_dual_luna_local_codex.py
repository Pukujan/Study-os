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
    def __init__(
        self,
        outputs: list[str] | None = None,
        *,
        results: list[subprocess.CompletedProcess[str]] | None = None,
    ) -> None:
        self.outputs = list(outputs or [])
        self.results = list(results or [])
        self.calls: list[dict[str, Any]] = []

    def __call__(self, args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        self.calls.append({"args": args, **kwargs})
        if self.results:
            return self.results.pop(0)
        if not self.outputs:
            raise AssertionError("fake runner has no remaining output")
        return subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout=self.outputs.pop(0),
            stderr="",
        )


def events(
    thread_id: str,
    message: str,
    *,
    mcp: bool = False,
    mcp_name: str = local.DEFAULT_MCP_NAME,
    mcp_status: str = "completed",
) -> str:
    lines = [f'{{"type":"thread.started","thread_id":"{thread_id}"}}']
    if mcp:
        lines.append(
            '{"type":"item.completed","item":'
            f'{{"type":"mcp_tool_call","server":"{mcp_name}",'
            f'"tool":"resolve_problem","status":"{mcp_status}"}}}}'
        )
    lines.append(
        '{"type":"item.completed","item":{"type":"agent_message","text":"'
        + message
        + '"}}'
    )
    return "\n".join(lines) + "\n"


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

    def test_resume_thread_change_is_self_healed_and_becomes_new_resume_target(self) -> None:
        fake = FakeRunner(
            [
                events("thread-one", "first"),
                events("thread-two", "second"),
                events("thread-two", "third"),
            ]
        )
        actor = local.CodexCliActor(role="student", runner=fake)

        actor.ask(payload())
        second = actor.ask(payload())
        third = actor.ask(payload())

        self.assertEqual(second["student_message"], "second")
        self.assertEqual(third["student_message"], "third")
        self.assertIn("thread-one", fake.calls[1]["args"])
        self.assertIn("thread-two", fake.calls[2]["args"])

    def test_failed_resume_retries_as_fresh_session_with_full_payload(self) -> None:
        failure = subprocess.CompletedProcess(
            args=["codex"],
            returncode=1,
            stdout="",
            stderr="missing session",
        )
        fake = FakeRunner(
            results=[
                subprocess.CompletedProcess(
                    args=["codex"],
                    returncode=0,
                    stdout=events("thread-one", "first"),
                    stderr="",
                ),
                failure,
                subprocess.CompletedProcess(
                    args=["codex"],
                    returncode=0,
                    stdout=events("thread-two", "recovered"),
                    stderr="",
                ),
            ]
        )
        actor = local.CodexCliActor(role="student", runner=fake)
        actor.ask(payload())
        second_payload = payload()
        second_payload["conversation"] = [
            {"role": "learner", "content": "first"},
            {"role": "teacher", "content": "answer"},
        ]

        recovered = actor.ask(second_payload)

        self.assertEqual(recovered["student_message"], "recovered")
        self.assertIn("resume", fake.calls[1]["args"])
        self.assertNotIn("resume", fake.calls[2]["args"])
        self.assertIn('"content": "answer"', fake.calls[2]["input"])

    def test_teacher_requires_completed_real_study_os_mcp_call(self) -> None:
        fake = FakeRunner(
            [
                events("teacher-one", "freeform answer"),
                events("teacher-two", "still freeform"),
            ]
        )
        actor = local.CodexCliActor(role="teacher", runner=fake)
        teacher_payload = payload()
        teacher_payload["type"] = "dual_luna_teacher_turn"
        teacher_payload["learner_message"] = "help"

        with self.assertRaisesRegex(RuntimeError, "required Study OS MCP call"):
            actor.ask(teacher_payload)

    def test_teacher_with_completed_study_os_mcp_call_succeeds(self) -> None:
        fake = FakeRunner(
            [events("teacher-thread", "visible teaching turn", mcp=True)]
        )
        actor = local.CodexCliActor(role="teacher", runner=fake)
        teacher_payload = payload()
        teacher_payload["type"] = "dual_luna_teacher_turn"
        teacher_payload["learner_message"] = "help"

        result = actor.ask(teacher_payload)

        self.assertEqual(result["teacher_message"], "visible teaching turn")
        sent_prompt = fake.calls[0]["input"]
        self.assertIn(local.DEFAULT_MCP_NAME, sent_prompt)
        self.assertIn("Do not edit the repository", sent_prompt)

    def test_sandbox_can_be_kept_when_explicitly_requested(self) -> None:
        fake = FakeRunner([events("thread-one", "hello")])
        actor = local.CodexCliActor(role="student", full_access=False, runner=fake)
        actor.ask(payload())

        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", fake.calls[0]["args"])

    def test_configure_local_mcp_replaces_only_test_entry(self) -> None:
        fake = FakeRunner(
            results=[
                subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="missing"),
                subprocess.CompletedProcess(args=[], returncode=0, stdout="added", stderr=""),
                subprocess.CompletedProcess(args=[], returncode=0, stdout="{}", stderr=""),
            ]
        )

        local.configure_local_study_os_mcp(
            "codex",
            "/usr/bin/python3",
            "study-os-local-test",
            runner=fake,
        )

        self.assertEqual(fake.calls[0]["args"][:3], ["codex", "mcp", "remove"])
        add_args = fake.calls[1]["args"]
        self.assertEqual(add_args[:4], ["codex", "mcp", "add", "study-os-local-test"])
        self.assertIn("/usr/bin/python3", add_args)
        self.assertIn(str(local.STUDY_OS_CLI), add_args)
        self.assertEqual(add_args[-1], "mcp")
        self.assertEqual(
            fake.calls[2]["args"],
            ["codex", "mcp", "get", "study-os-local-test", "--json"],
        )

    def test_unhealthy_runtime_is_migrated_then_rechecked(self) -> None:
        fake = FakeRunner(
            results=[
                subprocess.CompletedProcess(args=[], returncode=1, stdout="bad", stderr=""),
                subprocess.CompletedProcess(args=[], returncode=0, stdout="migrated", stderr=""),
                subprocess.CompletedProcess(args=[], returncode=0, stdout="healthy", stderr=""),
            ]
        )

        local.ensure_local_runtime("python3", runner=fake)

        self.assertEqual(fake.calls[0]["args"][-1], "doctor")
        self.assertEqual(fake.calls[1]["args"][-1], "migrate")
        self.assertEqual(fake.calls[2]["args"][-1], "doctor")


if __name__ == "__main__":
    unittest.main()
