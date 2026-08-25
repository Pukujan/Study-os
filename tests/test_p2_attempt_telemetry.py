import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os import RuntimeConfig, StudyOSService  # noqa: E402
from study_os.adaptive.telemetry import (  # noqa: E402
    AttemptTelemetry,
    ErrorTag,
    HintExposure,
)


class AttemptTelemetryContractTests(unittest.TestCase):
    def test_first_attempt_requires_no_parent_and_uses_canonical_assistance(self):
        telemetry = AttemptTelemetry(
            task_version="1.0.0",
            competency_ids=("algo.two_candidate_update_order",),
            attempt_number=1,
            interaction_mode="state_prediction",
            assistance_level_before_attempt="A0",
        )
        context = telemetry.to_context()
        self.assertEqual(context["context_version"], "0.1.0")
        self.assertIsNone(context["prior_attempt_id"])
        self.assertEqual(context["interaction_mode"], "state_prediction")

    def test_later_attempt_requires_parent(self):
        with self.assertRaisesRegex(ValueError, "requires prior_attempt_id"):
            AttemptTelemetry(
                task_version="1.0.0",
                competency_ids=("algo.two_candidate_update_order",),
                attempt_number=2,
                interaction_mode="state_prediction",
                assistance_level_before_attempt="A2",
            )

    def test_tools_used_must_be_declared(self):
        with self.assertRaisesRegex(ValueError, "subset"):
            AttemptTelemetry(
                task_version="1.0.0",
                competency_ids=("py.blank_implementation",),
                attempt_number=1,
                interaction_mode="manual_code_blank",
                assistance_level_before_attempt="A0",
                tools_allowed=(),
                tools_used=("python",),
            )

    def test_error_tags_preserve_observed_vs_derived_provenance(self):
        telemetry = AttemptTelemetry(
            task_version="1.0.0",
            competency_ids=("py.blank_implementation",),
            attempt_number=1,
            interaction_mode="manual_code_blank",
            assistance_level_before_attempt="A0",
            error_tags=(
                ErrorTag("return_control_flow_placement", "observed", detail="return nested inside loop"),
                ErrorTag("possible_js_syntax_interference", "derived", evidence_ids=("assessment-1",)),
            ),
        )
        tags = telemetry.to_context()["error_tags"]
        self.assertEqual(tags[0]["provenance"], "observed")
        self.assertEqual(tags[1]["provenance"], "derived")


class AttemptTelemetryPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = RuntimeConfig.from_env(self.temp_dir.name)
        self.service = StudyOSService(self.config)
        self.session = self.service.start_session(
            idempotency_key="telemetry-session",
            subject_id="subject-telemetry",
            project_id="dsa-python",
            domain_id="dsa",
        )

    def tearDown(self):
        try:
            self.service.close()
        finally:
            self.temp_dir.cleanup()

    def test_attempt_hint_attempt_chain_is_reconstructable_without_transcript(self):
        first_telemetry = AttemptTelemetry(
            task_version="1.0.0",
            competency_ids=("algo.two_candidate_update_order",),
            attempt_number=1,
            interaction_mode="state_prediction",
            assistance_level_before_attempt="A0",
            representation_ids_visible=("plain-text-v1",),
            feedback_exposure="none",
            self_report={"confidence": "low"},
        )
        first = self.service.record_attempt(
            idempotency_key="attempt-1",
            session_id=self.session["session_id"],
            subject_id="subject-telemetry",
            task_id="item-update-order-v1",
            response={"prediction": "update second before largest"},
            **first_telemetry.record_attempt_fields(),
        )

        hint = self.service.record_learning_event(
            idempotency_key="hint-1",
            session_id=self.session["session_id"],
            subject_id="subject-telemetry",
            evidence_class="observed",
            event_type="hint_presented",
            payload={
                "hint_id": "hint-update-order-1",
                "hint_type": "structural_subgoal",
                "assistance_level": "A3",
                "target_competency_id": "algo.two_candidate_update_order"
            },
        )

        second_telemetry = AttemptTelemetry(
            task_version="1.0.0",
            competency_ids=("algo.two_candidate_update_order",),
            attempt_number=2,
            prior_attempt_id=first["attempt_id"],
            interaction_mode="state_prediction",
            assistance_level_before_attempt="A3",
            representation_ids_visible=("state-table-v1",),
            hints_seen=(HintExposure("hint-update-order-1", "structural_subgoal", "A3"),),
            feedback_exposure="structural_hint",
            deterministic_result_refs=(hint["event_id"],),
        )
        second = self.service.record_attempt(
            idempotency_key="attempt-2",
            session_id=self.session["session_id"],
            subject_id="subject-telemetry",
            task_id="item-update-order-v1",
            response={"prediction": "promote old largest before replacing it"},
            **second_telemetry.record_attempt_fields(),
        )

        rows = self.service.repository.connection.execute(
            "SELECT attempt_id, assistance_level, context_json FROM attempts "
            "WHERE subject_id = ? ORDER BY created_at, rowid",
            ("subject-telemetry",),
        ).fetchall()
        self.assertEqual([row["attempt_id"] for row in rows], [first["attempt_id"], second["attempt_id"]])
        first_context = json.loads(rows[0]["context_json"])
        second_context = json.loads(rows[1]["context_json"])
        self.assertEqual(first_context["attempt_number"], 1)
        self.assertEqual(second_context["attempt_number"], 2)
        self.assertEqual(second_context["prior_attempt_id"], first["attempt_id"])
        self.assertEqual(second_context["hints_seen"][0]["hint_id"], "hint-update-order-1")
        self.assertEqual(first_context["representation_ids_visible"], ["plain-text-v1"])
        self.assertEqual(second_context["representation_ids_visible"], ["state-table-v1"])
        self.assertEqual(rows[1]["assistance_level"], "A3")


if __name__ == "__main__":
    unittest.main()
