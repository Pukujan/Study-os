from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

LESSON_ID = "mutation-testing.v0"
ASSISTANCE_LEVELS = {"A0", "A1", "A2", "A3", "A4"}


@dataclass(frozen=True)
class Probe:
    node_id: str
    concept: str
    prompt: str
    choices: dict[str, str]
    correct_choice: str
    feedback_correct: str
    feedback_incorrect: str
    representation: tuple[str, ...]
    next_node_id: str | None


PROBES = (
    Probe(
        node_id="survivor_meaning",
        concept="Killed vs survived",
        prompt=(
            "A mutation changes production behavior, the test suite runs, and every test still "
            "passes. What is the mutation-testing status?"
        ),
        choices={
            "A": "Killed",
            "B": "Survived",
            "C": "Skipped",
            "D": "Equivalent by definition",
        },
        correct_choice="B",
        feedback_correct=(
            "Correct. A mutant survives when the selected tests still pass. Survival is a signal "
            "to inspect, not automatically proof of a production bug."
        ),
        feedback_incorrect=(
            "The key observation is that the tests did not fail after the mutation. Mutation "
            "testing has a specific status for that case."
        ),
        representation=("production code", "deliberate mutation", "tests still pass"),
        next_node_id="oracle_strength",
    ),
    Probe(
        node_id="oracle_strength",
        concept="Test oracle strength",
        prompt=(
            "A test executes can_advance(True, False) and only asserts the result is True. "
            "A mutant replaces correct-and-not-stale with unconditional True and survives. "
            "What is the best interpretation?"
        ),
        choices={
            "A": "Coverage is necessarily zero",
            "B": "The mutant proves the production implementation is correct",
            "C": "The test oracle does not discriminate important forbidden cases",
            "D": "The mutation must be equivalent",
        },
        correct_choice="C",
        feedback_correct=(
            "Correct. The line can be covered while the assertions remain too weak to distinguish "
            "the intended rule from a broken implementation."
        ),
        feedback_incorrect=(
            "Separate execution coverage from oracle strength: a test may execute a line yet fail "
            "to constrain the behavior that line is supposed to enforce."
        ),
        representation=("execute code", "assert observable behavior", "distinguish alternatives"),
        next_node_id="equivalent_mutant",
    ),
    Probe(
        node_id="equivalent_mutant",
        concept="Equivalent mutants",
        prompt=(
            "A mutator rewrites x > 0 as 0 < x for ordinary numeric x. No test can distinguish "
            "the two expressions. How should this survivor be classified?"
        ),
        choices={
            "A": "Equivalent mutation",
            "B": "Critical semantic defect",
            "C": "Timeout",
            "D": "No-test mutant",
        },
        correct_choice="A",
        feedback_correct=(
            "Correct. An actually equivalent mutant cannot be killed by a legitimate behavioral "
            "test because it does not change observable semantics in the relevant domain."
        ),
        feedback_incorrect=(
            "Ask whether any valid input in the specified domain can make the original and mutant "
            "behave differently."
        ),
        representation=("original expression", "mutated expression", "same observable semantics"),
        next_node_id="release_policy",
    ),
    Probe(
        node_id="release_policy",
        concept="Mutation score vs assurance",
        prompt=(
            "A run has 300 survivors: 294 are explicitly audited equivalent or diagnostic "
            "mutations, but 6 change learner-authority behavior and remain unexplained. "
            "What should block release?"
        ),
        choices={
            "A": "Nothing; any nonzero mutation score is enough",
            "B": "All 300 must be killed even if equivalent",
            "C": "The 6 unresolved non-equivalent semantic survivors",
            "D": "Only the raw survivor count matters",
        },
        correct_choice="C",
        feedback_correct=(
            "Correct. Release assurance should fail on unresolved behavior-changing authority "
            "mutations while retaining explicit evidence for accepted equivalent or diagnostic "
            "survivors."
        ),
        feedback_incorrect=(
            "Mutation score is evidence, not the release objective. Focus on whether important "
            "promised behavior can be changed without detection."
        ),
        representation=("all survivors", "classification audit", "semantic release blockers"),
        next_node_id="ai_authority_transfer",
    ),
    Probe(
        node_id="ai_authority_transfer",
        concept="Mutation testing around AI authority",
        prompt=(
            "An LLM suggests that a learner mastered a concept, but deterministic Study OS code "
            "must require independent evidence before promoting mastery. Which mutation is the "
            "strongest assurance test of that boundary?"
        ),
        choices={
            "A": "Change the tutor's friendly wording",
            "B": "Change a CSS color",
            "C": "Remove or weaken the evidence gate and verify tests fail",
            "D": "Increase the model temperature",
        },
        correct_choice="C",
        feedback_correct=(
            "Correct. Mutation testing is strongest here against the deterministic authority shell: "
            "state transitions, evidence gates, contracts, permissions, and persistence."
        ),
        feedback_incorrect=(
            "Target the deterministic rule that prevents model output from becoming authoritative "
            "without the required evidence."
        ),
        representation=("LLM proposal", "deterministic evidence gate", "authorized state change"),
        next_node_id=None,
    ),
)

PROBE_BY_ID = {probe.node_id: probe for probe in PROBES}
FIRST_NODE_ID = PROBES[0].node_id


class StudySliceError(ValueError):
    pass


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS study_runs (
            run_id TEXT PRIMARY KEY,
            subject_id TEXT NOT NULL,
            lesson_id TEXT NOT NULL,
            current_node_id TEXT,
            status TEXT NOT NULL CHECK(status IN ('active', 'complete')),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS study_attempts (
            attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL REFERENCES study_runs(run_id),
            node_id TEXT NOT NULL,
            choice TEXT NOT NULL,
            outcome TEXT NOT NULL CHECK(outcome IN ('correct', 'incorrect')),
            assistance_level TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS study_progress (
            run_id TEXT NOT NULL REFERENCES study_runs(run_id),
            node_id TEXT NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            correct INTEGER NOT NULL DEFAULT 0,
            mastered INTEGER NOT NULL DEFAULT 0 CHECK(mastered IN (0, 1)),
            PRIMARY KEY (run_id, node_id)
        );
        """
    )
    return connection


def _load_run(connection: sqlite3.Connection, run_id: str) -> sqlite3.Row:
    row = connection.execute(
        "SELECT * FROM study_runs WHERE run_id = ?", (run_id,)
    ).fetchone()
    if row is None:
        raise StudySliceError("unknown run_id")
    return row


def _turn_payload(row: sqlite3.Row) -> dict[str, Any] | None:
    if row["status"] == "complete":
        return None
    node_id = row["current_node_id"]
    probe = PROBE_BY_ID.get(node_id)
    if probe is None:
        raise StudySliceError(f"run references unknown node: {node_id}")
    return {
        "run_id": row["run_id"],
        "lesson_id": row["lesson_id"],
        "status": row["status"],
        "node_id": probe.node_id,
        "concept": probe.concept,
        "prompt": probe.prompt,
        "choices": dict(probe.choices),
        "representation": list(probe.representation),
    }


def start_run(db_path: str | Path, subject_id: str) -> dict[str, Any]:
    if not isinstance(subject_id, str) or not subject_id.strip():
        raise StudySliceError("subject_id must be a non-empty string")
    run_id = str(uuid.uuid4())
    now = _now()
    with _connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO study_runs (
                run_id, subject_id, lesson_id, current_node_id, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'active', ?, ?)
            """,
            (run_id, subject_id.strip(), LESSON_ID, FIRST_NODE_ID, now, now),
        )
        connection.commit()
        row = _load_run(connection, run_id)
        turn = _turn_payload(row)
    return {"run_id": run_id, "turn": turn, "status": get_status(db_path, run_id)}


def get_turn(db_path: str | Path, run_id: str) -> dict[str, Any]:
    with _connect(db_path) as connection:
        row = _load_run(connection, run_id)
        turn = _turn_payload(row)
    return {"run_id": run_id, "turn": turn, "status": get_status(db_path, run_id)}


def submit_choice(
    db_path: str | Path,
    run_id: str,
    choice: str,
    assistance_level: str = "A0",
) -> dict[str, Any]:
    if assistance_level not in ASSISTANCE_LEVELS:
        raise StudySliceError("assistance_level must be one of A0, A1, A2, A3, A4")

    with _connect(db_path) as connection:
        row = _load_run(connection, run_id)
        if row["status"] != "active":
            raise StudySliceError("completed run does not accept responses")

        probe = PROBE_BY_ID.get(row["current_node_id"])
        if probe is None:
            raise StudySliceError("active run references unknown node")

        normalized_choice = choice.strip().upper() if isinstance(choice, str) else ""
        if normalized_choice not in probe.choices:
            raise StudySliceError(
                "choice must be one of " + ", ".join(sorted(probe.choices))
            )

        correct = normalized_choice == probe.correct_choice
        outcome = "correct" if correct else "incorrect"
        now = _now()

        connection.execute(
            """
            INSERT INTO study_attempts (
                run_id, node_id, choice, outcome, assistance_level, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (run_id, probe.node_id, normalized_choice, outcome, assistance_level, now),
        )
        connection.execute(
            """
            INSERT INTO study_progress (run_id, node_id, attempts, correct, mastered)
            VALUES (?, ?, 1, ?, ?)
            ON CONFLICT(run_id, node_id) DO UPDATE SET
                attempts = attempts + 1,
                correct = correct + excluded.correct,
                mastered = MAX(mastered, excluded.mastered)
            """,
            (run_id, probe.node_id, int(correct), int(correct)),
        )

        advanced = False
        if correct:
            advanced = True
            if probe.next_node_id is None:
                connection.execute(
                    """
                    UPDATE study_runs
                    SET current_node_id = NULL, status = 'complete', updated_at = ?
                    WHERE run_id = ?
                    """,
                    (now, run_id),
                )
            else:
                connection.execute(
                    """
                    UPDATE study_runs
                    SET current_node_id = ?, updated_at = ?
                    WHERE run_id = ?
                    """,
                    (probe.next_node_id, now, run_id),
                )
        else:
            connection.execute(
                "UPDATE study_runs SET updated_at = ? WHERE run_id = ?",
                (now, run_id),
            )

        connection.commit()
        updated = _load_run(connection, run_id)
        turn = _turn_payload(updated)

    return {
        "run_id": run_id,
        "submitted_node_id": probe.node_id,
        "outcome": outcome,
        "advanced": advanced,
        "feedback": probe.feedback_correct if correct else probe.feedback_incorrect,
        "turn": turn,
        "status": get_status(db_path, run_id),
    }


def get_status(db_path: str | Path, run_id: str) -> dict[str, Any]:
    with _connect(db_path) as connection:
        row = _load_run(connection, run_id)
        progress_rows = connection.execute(
            """
            SELECT node_id, attempts, correct, mastered
            FROM study_progress
            WHERE run_id = ?
            """,
            (run_id,),
        ).fetchall()

    progress = {
        item["node_id"]: {
            "attempts": int(item["attempts"]),
            "correct": int(item["correct"]),
            "mastered": bool(item["mastered"]),
        }
        for item in progress_rows
    }
    nodes = []
    for probe in PROBES:
        item = progress.get(
            probe.node_id,
            {"attempts": 0, "correct": 0, "mastered": False},
        )
        nodes.append(
            {
                "node_id": probe.node_id,
                "concept": probe.concept,
                **item,
            }
        )
    mastered = sum(1 for item in nodes if item["mastered"])
    return {
        "run_id": run_id,
        "subject_id": row["subject_id"],
        "lesson_id": row["lesson_id"],
        "run_status": row["status"],
        "current_node_id": row["current_node_id"],
        "mastered_nodes": mastered,
        "total_nodes": len(PROBES),
        "nodes": nodes,
    }
