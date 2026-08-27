from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os import RuntimeConfig, StudyOSService  # noqa: E402
from study_os.application.contracts import CreateFossilExportRequest  # noqa: E402
from study_os.application.service import (  # noqa: E402
    ApplicationService,
    project_create_fossil_export_to_mcp,
)
from study_os.mcp.server import MCPServer  # noqa: E402


class MalformedFossilExportService:
    def export_fossil(self, **_: Any) -> dict[str, Any]:
        return {
            "export_id": 123,
            "created": True,
            "artifact_type": "study_fossil",
            "source_ids": ["attempt-broken"],
        }


class FossilExportApplicationConformanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.service = StudyOSService(RuntimeConfig.from_env(self.temp_dir.name))
        self.session_id, self.attempt_id = self.seed_attempt(
            self.service,
            subject_id="subject-fossil",
            suffix="fossil-local",
        )

    def tearDown(self) -> None:
        try:
            self.service.close()
        finally:
            self.temp_dir.cleanup()

    @staticmethod
    def seed_attempt(
        service: StudyOSService,
        *,
        subject_id: str,
        suffix: str,
        attempt_id: str | None = None,
    ) -> tuple[str, str]:
        session = service.start_session(
            idempotency_key=f"{suffix}-session",
            subject_id=subject_id,
            project_id=f"{suffix}-project",
            domain_id=f"{suffix}-domain",
        )
        arguments = {
            "idempotency_key": f"{suffix}-attempt",
            "session_id": session["session_id"],
            "subject_id": subject_id,
            "task_id": "fossil-source-task",
            "response": {"prediction": "right"},
            "assistance_level": "none",
        }
        if attempt_id is None:
            attempt = service.record_attempt(**arguments)
        else:
            with patch("study_os.services.runtime_base.new_id", return_value=attempt_id):
                attempt = service.record_attempt(**arguments)
        return session["session_id"], attempt["attempt_id"]

    def test_direct_application_and_mcp_are_differentially_equivalent_on_disk(self) -> None:
        roots = [tempfile.TemporaryDirectory() for _ in range(3)]
        services = [StudyOSService(RuntimeConfig.from_env(root.name)) for root in roots]
        for index, service in enumerate(services):
            self.seed_attempt(
                service,
                subject_id="subject-fossil-differential",
                suffix=f"fossil-differential-{index}",
                attempt_id="attempt-fixed",
            )
        common = {
            "idempotency_key": "fossil-differential",
            "subject_id": "subject-fossil-differential",
            "artifact_type": " study_fossil ",
            "source_ids": ["attempt-fixed"],
        }
        try:
            direct = services[0].export_fossil(**common)
            application = project_create_fossil_export_to_mcp(
                ApplicationService(services[1]).create_fossil_export(
                    CreateFossilExportRequest(**common)
                )
            )
            mcp = MCPServer(services[2]).call_tool("export_fossil", common)

            self.assertEqual(application, direct)
            self.assertEqual(mcp, direct)
            self.assertEqual(direct["artifact_type"], " study_fossil ")
            self.assertEqual(direct["source_ids"], ["attempt-fixed"])

            for service in services:
                row = service.db.connection.execute(
                    "SELECT export_id, subject_id, artifact_type, source_ids_json, storage_path "
                    "FROM fossil_exports WHERE idempotency_key = ?",
                    ("fossil-differential",),
                ).fetchone()
                self.assertIsNotNone(row)
                assert row is not None
                self.assertEqual(row["export_id"], direct["export_id"])
                self.assertEqual(row["subject_id"], "subject-fossil-differential")
                self.assertEqual(row["artifact_type"], " study_fossil ")
                self.assertEqual(json.loads(row["source_ids_json"]), ["attempt-fixed"])

                export_path = service.config.root / row["storage_path"]
                self.assertTrue(export_path.is_file())
                payload = json.loads(export_path.read_text(encoding="utf-8"))
                self.assertEqual(payload["export_id"], direct["export_id"])
                self.assertEqual(payload["subject_id"], "subject-fossil-differential")
                self.assertEqual(payload["artifact_type"], " study_fossil ")
                self.assertEqual(payload["source_ids"], ["attempt-fixed"])
        finally:
            for service in services:
                service.close()
            for root in roots:
                root.cleanup()

    def test_retry_reuses_export_and_changed_request_conflicts(self) -> None:
        server = MCPServer(self.service)
        base = {
            "idempotency_key": "fossil-retry",
            "subject_id": "subject-fossil",
            "artifact_type": "study_fossil",
            "source_ids": [self.attempt_id],
        }
        first = server.call_tool("export_fossil", base)
        retry = server.call_tool("export_fossil", base)
        conflict = server.call_tool(
            "export_fossil",
            {**base, "artifact_type": "study_fossil_changed"},
        )

        self.assertTrue(first["created"])
        self.assertFalse(retry["created"])
        self.assertEqual(first["export_id"], retry["export_id"])
        self.assertEqual(conflict["error"]["category"], "conflict")
        self.assertEqual(
            self.service.db.connection.execute(
                "SELECT COUNT(*) FROM fossil_exports WHERE idempotency_key = ?",
                ("fossil-retry",),
            ).fetchone()[0],
            1,
        )
        row = self.service.db.connection.execute(
            "SELECT storage_path FROM fossil_exports WHERE idempotency_key = ?",
            ("fossil-retry",),
        ).fetchone()
        self.assertTrue((self.service.config.root / row["storage_path"]).is_file())

    def test_subject_and_source_failures_leave_no_export_artifact(self) -> None:
        server = MCPServer(self.service)
        missing_subject = server.call_tool(
            "export_fossil",
            {
                "idempotency_key": "fossil-missing-subject",
                "subject_id": "missing-subject",
                "artifact_type": "study_fossil",
                "source_ids": [self.attempt_id],
            },
        )
        self.assertEqual(missing_subject["error"]["category"], "not_found")

        missing_source = server.call_tool(
            "export_fossil",
            {
                "idempotency_key": "fossil-missing-source",
                "subject_id": "subject-fossil",
                "artifact_type": "study_fossil",
                "source_ids": ["missing-attempt"],
            },
        )
        self.assertEqual(missing_source["error"]["category"], "integrity_error")

        _, other_attempt = self.seed_attempt(
            self.service,
            subject_id="subject-fossil-other",
            suffix="fossil-other",
        )
        wrong_subject = server.call_tool(
            "export_fossil",
            {
                "idempotency_key": "fossil-wrong-subject-source",
                "subject_id": "subject-fossil",
                "artifact_type": "study_fossil",
                "source_ids": [other_attempt],
            },
        )
        self.assertEqual(wrong_subject["error"]["category"], "integrity_error")

        whitespace_alias = server.call_tool(
            "export_fossil",
            {
                "idempotency_key": "fossil-source-whitespace",
                "subject_id": "subject-fossil",
                "artifact_type": "study_fossil",
                "source_ids": [f" {self.attempt_id} "],
            },
        )
        self.assertEqual(whitespace_alias["error"]["category"], "integrity_error")
        self.assertEqual(
            self.service.db.connection.execute("SELECT COUNT(*) FROM fossil_exports").fetchone()[0],
            0,
        )
        export_dir = self.service.config.exports_root / "fossil"
        self.assertFalse(export_dir.exists() and any(export_dir.iterdir()))

    def test_malformed_runtime_result_and_extra_mcp_fields_fail_closed(self) -> None:
        malformed = MCPServer(MalformedFossilExportService()).call_tool(  # type: ignore[arg-type]
            "export_fossil",
            {
                "idempotency_key": "fossil-malformed",
                "subject_id": "subject-broken",
                "artifact_type": "study_fossil",
                "source_ids": ["attempt-broken"],
            },
        )
        self.assertEqual(malformed["error"]["category"], "internal_error")
        self.assertEqual(
            malformed["error"]["details"]["exception"],
            "ApplicationBoundaryError",
        )

        base = {
            "idempotency_key": "fossil-unexpected",
            "subject_id": "subject-fossil",
            "artifact_type": "study_fossil",
            "source_ids": [self.attempt_id],
        }
        for extra in (
            {"application_contract_version": "0.1.0"},
            {"invented": True},
        ):
            with self.subTest(extra=extra):
                result = MCPServer(self.service).call_tool(
                    "export_fossil",
                    {**base, **extra},
                )
                self.assertEqual(result["error"]["category"], "validation_error")


if __name__ == "__main__":
    unittest.main()
