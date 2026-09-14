from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "tools" / "check_model_tutoring_acceptance.py"
CORPUS_PATH = ROOT / "datasets" / "dsa-conversation-replay.v0.1.json"
RAW_TRANSCRIPT_PATH = ROOT / "artifacts" / "dual-luna-dsa-transcript.jsonl"
TRACE_SCHEMA_PATH = ROOT / "contracts" / "model-tutoring-trace.v0.1.schema.json"

spec = importlib.util.spec_from_file_location("model_tutoring_acceptance", CHECKER_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("unable to load model tutoring acceptance checker")
acceptance = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = acceptance
spec.loader.exec_module(acceptance)


class ModelTutoringAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.corpus = acceptance.load_json(CORPUS_PATH)
        cls.scenario = acceptance.find_scenario(cls.corpus, "contains-duplicate-set")

    def _passing_transcript(self) -> list[dict]:
        rows: list[dict] = []
        for index, turn in enumerate(self.scenario["turns"]):
            expected = turn["expected"]
            anchor = expected["must_include_any"][0]
            teacher = f"```text\n{anchor}\n```\nTiny check: what do you think?"
            rows.append(
                {
                    "schema_version": "study-os.dual-luna-exchange.v0.1",
                    "scenario_id": self.scenario["id"],
                    "title": self.scenario["title"],
                    "problem": self.scenario["problem"],
                    "turn_index": index,
                    "learner_signal": turn["learner_signal"],
                    "learner_message": f"learner turn {index}",
                    "teacher_message": teacher,
                }
            )
        return rows

    def _passing_trace(self) -> list[dict]:
        rows: list[dict] = []
        for index, turn in enumerate(self.scenario["turns"]):
            stage = turn["stage"]
            rows.append(
                {
                    "schema_version": acceptance.TRACE_SCHEMA_VERSION,
                    "scenario_id": self.scenario["id"],
                    "turn_index": index,
                    "path_kind": "model_generated",
                    "target_concept": acceptance.STAGE_TO_CONCEPT[stage],
                    "diagnosis_family": "uncertain_mixed",
                    "operation": "probe",
                    "assistance_level": "A1",
                    "advance": False,
                    "allowed_variables": sorted(acceptance.STAGE_REQUIRED_VARIABLES[stage]),
                    "forbidden_variables": list(self.scenario["forbidden_aliases"]),
                    "visual_required": bool(turn["expected"]["visual_required"]),
                    "prompt_version": "pilot-test-v1",
                    "model_identifier": "test-model",
                }
            )
        return rows

    def test_trace_schema_is_valid(self) -> None:
        schema = json.loads(TRACE_SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)

    def test_synthetic_calibrated_model_path_is_accepted(self) -> None:
        report = acceptance.evaluate(
            transcript_rows=self._passing_transcript(),
            scenario=self.scenario,
            trace_rows=self._passing_trace(),
            require_trace=True,
        )
        self.assertTrue(report["accepted"], report["failures"])

    def test_existing_needs_compilation_transcript_is_rejected(self) -> None:
        rows = acceptance.load_jsonl(RAW_TRANSCRIPT_PATH)
        report = acceptance.evaluate(
            transcript_rows=rows,
            scenario=self.scenario,
            trace_rows=None,
            require_trace=False,
        )
        self.assertFalse(report["accepted"])
        codes = {failure["code"] for failure in report["failures"]}
        self.assertIn("PRODUCT_INTERNAL_STATE_LEAK", codes)

    def test_final_acceptance_requires_model_trace(self) -> None:
        report = acceptance.evaluate(
            transcript_rows=self._passing_transcript(),
            scenario=self.scenario,
            trace_rows=None,
            require_trace=True,
        )
        self.assertFalse(report["accepted"])
        self.assertIn("TRACE_REQUIRED", {item["code"] for item in report["failures"]})

    def test_wrong_or_clarification_turn_cannot_advance(self) -> None:
        trace = self._passing_trace()
        trace[0]["advance"] = True
        report = acceptance.evaluate(
            transcript_rows=self._passing_transcript(),
            scenario=self.scenario,
            trace_rows=trace,
            require_trace=True,
        )
        self.assertFalse(report["accepted"])
        self.assertIn("UNSUPPORTED_ADVANCE", {item["code"] for item in report["failures"]})

    def test_future_concept_and_forbidden_alias_are_rejected(self) -> None:
        transcript = self._passing_transcript()
        transcript[0]["teacher_message"] = "```text\nnums duplicate seen set\n```\nWhat do you think?"
        report = acceptance.evaluate(
            transcript_rows=transcript,
            scenario=self.scenario,
            trace_rows=self._passing_trace(),
            require_trace=True,
        )
        codes = {item["code"] for item in report["failures"]}
        self.assertIn("FUTURE_OR_FORBIDDEN_CONCEPT", codes)
        self.assertIn("FORBIDDEN_VARIABLE_ALIAS", codes)


if __name__ == "__main__":
    unittest.main()
