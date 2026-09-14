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
TRACE_SCHEMA_PATH = ROOT / "contracts" / "model-tutoring-trace.v0.2.schema.json"

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
        cls.stage_contracts = acceptance._stage_contracts(cls.scenario)

    def _concepts(self) -> list[str]:
        return [
            "duplicate_meaning", "duplicate_meaning", "duplicate_meaning",
            "box_meaning", "box_meaning", "box_meaning",
            "membership", "membership", "membership",
            "check_before_add", "check_before_add", "check_before_add",
            "loop_assembly", "loop_assembly", "loop_assembly",
        ]

    def _passing_transcript(self) -> list[dict]:
        rows: list[dict] = []
        concepts = self._concepts()
        for index, concept in enumerate(concepts):
            stage = acceptance.CONCEPT_TO_STAGE[concept]
            expected = self.stage_contracts[stage]
            anchors = expected["must_include_any"]
            visual = " ".join(str(item) for item in anchors)
            extra = "\nIf no duplicate is found after the scan: `return False`." if index == 14 else ""
            rows.append(
                {
                    "schema_version": "study-os.model-tutoring-exchange.v0.2",
                    "scenario_id": self.scenario["id"],
                    "title": self.scenario["title"],
                    "problem": self.scenario["problem"],
                    "turn_index": index,
                    "learner_signal": self.scenario["turns"][index]["learner_signal"],
                    "learner_message": f"learner evidence turn {index}",
                    "teacher_message": f"```text\n{visual}\n```\n{extra}\nTiny check: what next?",
                }
            )
        return rows

    def _passing_trace(self) -> list[dict]:
        concepts = self._concepts()
        rows: list[dict] = []
        advance_turns = {2, 5, 8, 11}
        for index, concept in enumerate(concepts):
            stage = acceptance.CONCEPT_TO_STAGE[concept]
            demonstrated = index in advance_turns
            rows.append(
                {
                    "schema_version": acceptance.TRACE_SCHEMA_VERSION,
                    "scenario_id": self.scenario["id"],
                    "turn_index": index,
                    "path_kind": "model_generated",
                    "target_concept": concept,
                    "diagnosis_family": "none" if demonstrated else "uncertain_mixed",
                    "operation": "probe",
                    "assistance_level": "A0" if demonstrated else "A1",
                    "learner_outcome": "demonstrated" if demonstrated else "not_yet",
                    "evidence_quote": f"learner evidence turn {index}" if demonstrated else "",
                    "advance": demonstrated,
                    "allowed_variables": sorted(acceptance.STAGE_REQUIRED_VARIABLES[stage]),
                    "forbidden_variables": list(self.scenario["forbidden_aliases"]),
                    "visual_required": True,
                    "prompt_version": "pilot-test-v2",
                    "model_identifier": "test-model",
                }
            )
        return rows

    def test_trace_schema_is_valid(self) -> None:
        schema = json.loads(TRACE_SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)

    def test_synthetic_evidence_driven_path_is_accepted(self) -> None:
        report = acceptance.evaluate(
            transcript_rows=self._passing_transcript(),
            scenario=self.scenario,
            trace_rows=self._passing_trace(),
            require_trace=True,
        )
        self.assertTrue(report["accepted"], report["failures"])

    def test_recovery_signal_cannot_force_advance_without_demonstrated_outcome(self) -> None:
        trace = self._passing_trace()
        trace[0]["advance"] = True
        trace[0]["learner_outcome"] = "not_yet"
        report = acceptance.evaluate(
            transcript_rows=self._passing_transcript(),
            scenario=self.scenario,
            trace_rows=trace,
            require_trace=True,
        )
        self.assertIn("UNSUPPORTED_ADVANCE", {item["code"] for item in report["failures"]})

    def test_demonstrated_outcome_requires_verbatim_evidence(self) -> None:
        trace = self._passing_trace()
        trace[2]["evidence_quote"] = "not in the learner message"
        report = acceptance.evaluate(
            transcript_rows=self._passing_transcript(),
            scenario=self.scenario,
            trace_rows=trace,
            require_trace=True,
        )
        self.assertIn("EVIDENCE_NOT_IN_LEARNER_MESSAGE", {item["code"] for item in report["failures"]})

    def test_progression_must_follow_actual_advance_trace(self) -> None:
        trace = self._passing_trace()
        trace[3]["target_concept"] = "membership"
        report = acceptance.evaluate(
            transcript_rows=self._passing_transcript(),
            scenario=self.scenario,
            trace_rows=trace,
            require_trace=True,
        )
        self.assertIn("PROGRESSION_DRIFT", {item["code"] for item in report["failures"]})

    def test_final_loop_must_explicitly_establish_return_false(self) -> None:
        transcript = self._passing_transcript()
        transcript[-1]["teacher_message"] = "```text\nnums box num\n```\nTiny check: what next?"
        report = acceptance.evaluate(
            transcript_rows=transcript,
            scenario=self.scenario,
            trace_rows=self._passing_trace(),
            require_trace=True,
        )
        self.assertIn("LOOP_COMPLETION_MISSING", {item["code"] for item in report["failures"]})

    def test_existing_needs_compilation_transcript_is_rejected(self) -> None:
        rows = acceptance.load_jsonl(RAW_TRANSCRIPT_PATH)
        report = acceptance.evaluate(
            transcript_rows=rows,
            scenario=self.scenario,
            trace_rows=None,
            require_trace=False,
        )
        self.assertFalse(report["accepted"])
        self.assertIn("PRODUCT_INTERNAL_STATE_LEAK", {item["code"] for item in report["failures"]})

    def test_final_acceptance_requires_model_trace(self) -> None:
        report = acceptance.evaluate(
            transcript_rows=self._passing_transcript(),
            scenario=self.scenario,
            trace_rows=None,
            require_trace=True,
        )
        self.assertIn("TRACE_REQUIRED", {item["code"] for item in report["failures"]})


if __name__ == "__main__":
    unittest.main()
