import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "study-os-mcp-tools.v0.1.json"
FIXTURE = ROOT / "tests" / "fixtures" / "reference_learning_trajectory.v0.1.json"


class RuntimeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.tools = {tool["name"]: tool for tool in cls.contract["tools"]}

    def test_contract_has_expected_version(self):
        self.assertEqual(self.contract["contract_version"], "0.1.0")

    def test_required_semantic_tools_exist(self):
        required = {
            "doctor",
            "status",
            "start_session",
            "record_learning_event",
            "record_attempt",
            "record_assessment",
            "record_representation_intervention",
            "record_representation_outcome",
            "checkpoint",
            "resume",
            "schedule_retention_probe",
            "get_next_probe",
            "export_fossil",
        }
        self.assertTrue(required.issubset(self.tools), required - set(self.tools))

    def test_tool_names_are_unique(self):
        names = [tool["name"] for tool in self.contract["tools"]]
        self.assertEqual(len(names), len(set(names)))

    def test_mutating_tools_require_idempotency_key(self):
        for tool in self.contract["tools"]:
            if tool["mutating"]:
                with self.subTest(tool=tool["name"]):
                    self.assertTrue(tool["idempotency_required"])
                    self.assertIn("idempotency_key", tool["required_input"])

    def test_no_generic_machine_mutation_tools(self):
        forbidden_fragments = {
            "sql",
            "shell",
            "terminal",
            "exec",
            "execute_code",
            "run_code",
            "write_file",
            "filesystem",
        }
        for name in self.tools:
            lowered = name.lower()
            with self.subTest(tool=name):
                self.assertFalse(any(fragment in lowered for fragment in forbidden_fragments))

        principles = self.contract["principles"]
        self.assertFalse(principles["generic_sql_allowed"])
        self.assertFalse(principles["generic_shell_allowed"])
        self.assertFalse(principles["generic_file_write_allowed"])
        self.assertFalse(principles["arbitrary_code_execution_allowed"])

    def test_runtime_does_not_depend_on_github_or_fossil(self):
        principles = self.contract["principles"]
        self.assertFalse(principles["github_runtime_dependency"])
        self.assertFalse(principles["fossil_runtime_dependency"])
        self.assertEqual(principles["canonical_runtime_store"], "local_study_os_service")

    def test_checkpoint_contract_requires_evidence_and_resume_state(self):
        checkpoint = self.tools["checkpoint"]
        required = set(checkpoint["required_input"])
        self.assertTrue({"evidence_ids", "capability_state", "assistance_state", "resume"}.issubset(required))

    def test_representation_outcome_requires_evidence(self):
        outcome = self.tools["record_representation_outcome"]
        self.assertIn("evidence_ids", outcome["required_input"])
        self.assertIn("evidence_score", outcome["required_input"])

    def test_reference_fixture_has_faded_success_before_score_three(self):
        sequence = self.fixture["sequence"]
        by_id = {item["id"]: item for item in sequence}
        outcome = by_id["outcome-001"]
        self.assertEqual(outcome["evidence_score"], 3)
        assessments = [by_id[eid] for eid in outcome["evidence_ids"]]
        self.assertTrue(any(item.get("assistance_level") == "representation_visible" for item in assessments))
        self.assertTrue(any(item.get("assistance_level") == "none" and item.get("result") == "pass" for item in assessments))

    def test_reference_checkpoint_does_not_promote_untested_implementation(self):
        checkpoint = next(item for item in self.fixture["sequence"] if item["kind"] == "checkpoint")
        self.assertEqual(checkpoint["capability_state"]["python_implementation"], "not_tested")
        self.assertEqual(checkpoint["capability_state"]["state_prediction"], "pass_unaided")

    def test_reference_checkpoint_only_references_existing_ids(self):
        sequence = self.fixture["sequence"]
        ids = {item["id"] for item in sequence}
        checkpoint = next(item for item in sequence if item["kind"] == "checkpoint")
        self.assertTrue(set(checkpoint["evidence_ids"]).issubset(ids))


if __name__ == "__main__":
    unittest.main()
