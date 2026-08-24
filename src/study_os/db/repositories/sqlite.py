"""SQLite repository adapter and commit-time persistence invariants.

The semantic service owns request validation and transaction composition.  The
repository additionally enforces invariants that must still be true immediately
before commit so no transport or service path can durably bypass them.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from typing import Any, Iterator

from ...errors import integrity
from ..connection import Database


class SQLiteRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    @property
    def connection(self) -> sqlite3.Connection:
        return self.database.connection

    @staticmethod
    def _is_passing_state(value: Any) -> bool:
        return isinstance(value, str) and value.strip().lower().startswith("pass")

    @classmethod
    def _validate_checkpoint_capabilities(cls, connection: sqlite3.Connection) -> None:
        """Reject checkpoint pass claims without cited behavioral assessments.

        A capability marked as passing must cite a same-subject assessment for
        that capability whose result is itself passing.  ``pass_unaided`` is
        stricter: the cited assessment must have assistance level ``none``.
        This check executes before the surrounding transaction commits.
        """

        unsupported: list[dict[str, str]] = []
        rows = connection.execute(
            "SELECT checkpoint_id, subject_id, evidence_ids_json, capability_state_json FROM checkpoints"
        ).fetchall()
        for checkpoint in rows:
            try:
                evidence_ids = json.loads(checkpoint["evidence_ids_json"])
                capability_state = json.loads(checkpoint["capability_state_json"])
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise integrity(
                    "Checkpoint capability provenance is malformed",
                    checkpoint_id=checkpoint["checkpoint_id"],
                ) from exc
            if not isinstance(evidence_ids, list) or not isinstance(capability_state, dict):
                raise integrity(
                    "Checkpoint capability provenance has invalid structure",
                    checkpoint_id=checkpoint["checkpoint_id"],
                )

            cited_assessment_ids = [value for value in evidence_ids if isinstance(value, str) and value]
            for capability, state in capability_state.items():
                if not cls._is_passing_state(state):
                    continue
                if not isinstance(capability, str) or not capability.strip():
                    unsupported.append(
                        {
                            "checkpoint_id": checkpoint["checkpoint_id"],
                            "capability": str(capability),
                            "state": str(state),
                        }
                    )
                    continue

                supported = False
                for assessment_id in cited_assessment_ids:
                    assessment = connection.execute(
                        "SELECT result, assistance_level FROM assessments "
                        "WHERE assessment_id = ? AND subject_id = ? AND capability = ?",
                        (assessment_id, checkpoint["subject_id"], capability),
                    ).fetchone()
                    if assessment is None or not cls._is_passing_state(assessment["result"]):
                        continue
                    if str(state).strip().lower() == "pass_unaided" and assessment["assistance_level"].strip().lower() != "none":
                        continue
                    supported = True
                    break

                if not supported:
                    unsupported.append(
                        {
                            "checkpoint_id": checkpoint["checkpoint_id"],
                            "capability": capability,
                            "state": str(state),
                        }
                    )

        if unsupported:
            raise integrity(
                "Checkpoint passing capability lacks supporting assessment evidence",
                unsupported_capabilities=unsupported,
            )

    @contextmanager
    def transaction(self, *, immediate: bool = True) -> Iterator[sqlite3.Connection]:
        with self.database.transaction(immediate=immediate) as connection:
            yield connection
            if immediate:
                self._validate_checkpoint_capabilities(connection)

    def execute(self, sql: str, parameters: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        return self.connection.execute(sql, parameters)

    def close(self) -> None:
        self.database.close()
