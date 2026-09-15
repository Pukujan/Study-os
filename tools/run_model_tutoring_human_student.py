#!/usr/bin/env python3
"""Run one completion-driven Study OS tutoring session with a human learner.

Only the learner actor is replaced. Luna still owns decomposition, diagnosis,
and learner-visible generation through the same local Study OS MCP path and
GenericModelTutoringController used by the automated qualification harness.
The accepted transcript, trace, and generated TeachingPlan are checkpointed so
human review can be compared directly with automated evidence.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import run_dual_luna_local_codex as local  # noqa: E402
import run_dual_luna_transcript as raw  # noqa: E402
import run_model_tutoring_all_dsa as tutoring  # noqa: E402


DEFAULT_TRANSCRIPT = ROOT / "artifacts" / "human-student-model-tutoring-transcript.jsonl"
DEFAULT_MARKDOWN = ROOT / "artifacts" / "human-student-model-tutoring-transcript.md"
DEFAULT_TRACE = ROOT / "artifacts" / "human-student-model-tutoring-trace.jsonl"
DEFAULT_PLANS = ROOT / "artifacts" / "human-student-model-tutoring-plans.jsonl"


class HumanStudentActor:
    """Interactive stdin/stdout adapter implementing the tutoring Actor protocol.

    Teacher text is shown only after it has entered the validated conversation
    supplied by the core runner on the next learner turn. This prevents rejected
    generation retries from leaking into the human evaluation surface.
    """

    def __init__(self) -> None:
        self._seen_scenario: str | None = None
        self._last_teacher_message: str | None = None

    def _show_teacher_from_conversation(self, conversation: object) -> None:
        if not isinstance(conversation, Sequence) or isinstance(conversation, (str, bytes)):
            return
        for item in reversed(conversation):
            if not isinstance(item, Mapping) or item.get("role") != "teacher":
                continue
            content = item.get("content")
            if isinstance(content, str) and content.strip():
                self.show_teacher(content)
            return

    def show_teacher(self, message: str) -> None:
        message = message.strip()
        if not message or message == self._last_teacher_message:
            return
        self._last_teacher_message = message
        print("\nStudy OS >")
        print(message)
        print()

    def ask(self, payload: dict[str, Any]) -> dict[str, Any]:
        scenario_id = str(payload.get("scenario_id", ""))
        if scenario_id != self._seen_scenario:
            self._seen_scenario = scenario_id
            print("\n" + "=" * 72)
            print(f"Problem: {payload.get('title', scenario_id)}")
            print(str(payload.get("problem", "")))
            print("=" * 72)
            print(
                "Type naturally as the learner. Use Ctrl+C to stop; "
                "the run checkpoints every accepted exchange.\n"
            )

        self._show_teacher_from_conversation(payload.get("conversation", []))

        while True:
            try:
                message = input("You > ").strip()
            except EOFError as exc:
                raise KeyboardInterrupt from exc
            if message:
                return {"student_message": message}
            print("Please enter a learner message.")

    def close(self) -> None:
        return None


def _scenario_exists(corpus: Mapping[str, Any], scenario_id: str) -> bool:
    scenarios = corpus.get("scenarios", [])
    return any(
        isinstance(item, Mapping) and str(item.get("id", "")) == scenario_id
        for item in scenarios
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one real Study OS/Luna tutoring session with a human learner"
    )
    parser.add_argument("--scenario", required=True, help="public DSA scenario id")
    parser.add_argument("--corpus", type=Path, default=raw.DEFAULT_CORPUS)
    parser.add_argument("--model", default=tutoring.DEFAULT_MODEL)
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--python-bin", default=sys.executable)
    parser.add_argument("--mcp-name", default=tutoring.DEFAULT_MCP_NAME)
    parser.add_argument(
        "--turn-timeout-seconds",
        type=int,
        default=tutoring.DEFAULT_TURN_TIMEOUT_SECONDS,
    )
    parser.add_argument(
        "--max-exchanges",
        type=int,
        default=250,
        help="anti-loop ceiling; the session normally stops on earned completion",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="resume a validated checkpoint instead of starting this scenario fresh",
    )
    parser.add_argument("--transcript", type=Path, default=DEFAULT_TRANSCRIPT)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE)
    parser.add_argument("--plans", type=Path, default=DEFAULT_PLANS)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    corpus = raw.load_corpus(args.corpus)
    if not _scenario_exists(corpus, args.scenario):
        available = ", ".join(
            str(item.get("id"))
            for item in corpus.get("scenarios", [])
            if isinstance(item, Mapping)
        )
        raise SystemExit(f"unknown scenario {args.scenario!r}; available: {available}")

    version = local.ensure_codex_available(args.codex_bin)
    print(f"local Codex: {version}")
    local.ensure_local_runtime(args.python_bin)
    local.configure_local_study_os_mcp(
        args.codex_bin,
        args.python_bin,
        args.mcp_name,
    )
    print(f"Study OS MCP ready: {args.mcp_name}")

    student = HumanStudentActor()
    teacher = tutoring.AllDSATeacherActor(
        role="teacher",
        codex_bin=args.codex_bin,
        model=args.model,
        mcp_name=args.mcp_name,
        timeout_seconds=args.turn_timeout_seconds,
    )

    try:
        transcript, trace, plans = tutoring.run_all_dsa(
            corpus,
            student,
            teacher,
            scenario_ids={args.scenario},
            model_identifier=args.model,
            transcript_path=args.transcript,
            markdown_path=args.markdown,
            trace_path=args.trace,
            plans_path=args.plans,
            fresh=not args.resume,
            allow_short_run=True,
            completion_driven=True,
            max_exchanges_per_problem=args.max_exchanges,
        )
    except KeyboardInterrupt:
        print("\nStopped by learner. Accepted exchanges were already checkpointed.")
        return 130
    finally:
        student.close()
        teacher.close()

    scenario_rows = [row for row in transcript if row.get("scenario_id") == args.scenario]
    if scenario_rows:
        final_teacher = scenario_rows[-1].get("teacher_message")
        if isinstance(final_teacher, str):
            student.show_teacher(final_teacher)
    completed = bool(scenario_rows and scenario_rows[-1].get("completion_candidate") is True)
    print("\nSession complete." if completed else "\nSession ended without completion.")
    print(f"accepted exchanges: {len(scenario_rows)}")
    print(f"transcript: {args.markdown}")
    print(f"trace: {args.trace}")
    print(f"plan: {args.plans}")
    print(f"total persisted plans: {len(plans)}; total trace rows: {len(trace)}")
    return 0 if completed else 1


if __name__ == "__main__":
    raise SystemExit(main())
