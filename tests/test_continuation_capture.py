"""Tests for the public-safe continuation capture."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "datasets" / "learner-methodology" / "2026-09-03-study-os-continuation-capture.json"
EXPORT_PATH = ROOT / "fossil" / "exports" / "research" / "2026-09-03-study-os-continuation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class ContinuationCaptureTests(unittest.TestCase):
    def test_dataset_and_export_match_their_schemas(self) -> None:
        dataset_schema = load_json(ROOT / "schemas" / "learner-methodology-capture.schema.json")
        export_schema = load_json(ROOT / "schemas" / "fossil-research-export.schema.json")
        Draft202012Validator(dataset_schema, format_checker=FormatChecker()).validate(load_json(DATASET_PATH))
        Draft202012Validator(export_schema, format_checker=FormatChecker()).validate(load_json(EXPORT_PATH))

    def test_export_points_to_the_exact_fossil_capture(self) -> None:
        dataset = load_json(DATASET_PATH)
        export = load_json(EXPORT_PATH)

        self.assertEqual(export["dataset_sha256"], hashlib.sha256(DATASET_PATH.read_bytes()).hexdigest())
        self.assertEqual(export["dataset_path"], "datasets/learner-methodology/2026-09-03-study-os-continuation-capture.json")
        self.assertEqual(dataset["source"]["fossil"]["pack_id"], "pack_study_os_personal_6a996a5d178483ea")
        self.assertEqual(dataset["source"]["fossil"]["conversation_id"], "conv_study_os_shared_6a996a5d178483ea")
        self.assertEqual(dataset["source"]["fossil"]["pull_request_url"], "https://github.com/Pukujan/fossil-core/pull/246")

    def test_public_derivative_keeps_evidence_classes_separate(self) -> None:
        dataset = load_json(DATASET_PATH)

        self.assertEqual(dataset["evidence_status"], "reconstructed")
        self.assertEqual(dataset["authority"], "non_authoritative")
        self.assertTrue(all(item["evidence_class"] == "self_reported" for item in dataset["self_reported"]))
        self.assertTrue(all(item["evidence_class"] == "observed" for item in dataset["observed"]))
        self.assertTrue(all(item["evidence_class"] == "derived" for item in dataset["derived"]))
        self.assertTrue(all(item["evidence_class"] == "derived" for item in dataset["instrumentation_proposals"]))
        self.assertNotIn("messages", dataset)
        self.assertNotIn("transcript", dataset)
        self.assertNotIn("raw", dataset)


if __name__ == "__main__":
    unittest.main()
