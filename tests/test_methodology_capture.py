"""Tests for the public-safe methodology capture."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "datasets" / "learner-methodology" / "2026-08-29-study-os-methodology-capture.json"
EXPORT_PATH = ROOT / "fossil" / "exports" / "research" / "2026-08-29-study-os-methodology.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class MethodologyCaptureTests(unittest.TestCase):
    def test_dataset_and_export_match_their_schemas(self) -> None:
        dataset_schema = load_json(ROOT / "schemas" / "learner-methodology-capture.schema.json")
        export_schema = load_json(ROOT / "schemas" / "fossil-research-export.schema.json")
        Draft202012Validator.check_schema(dataset_schema)
        Draft202012Validator.check_schema(export_schema)
        Draft202012Validator(dataset_schema, format_checker=FormatChecker()).validate(load_json(DATASET_PATH))
        Draft202012Validator(export_schema, format_checker=FormatChecker()).validate(load_json(EXPORT_PATH))

    def test_export_hash_and_counts_match_dataset(self) -> None:
        dataset = load_json(DATASET_PATH)
        export = load_json(EXPORT_PATH)
        digest = hashlib.sha256(DATASET_PATH.read_bytes()).hexdigest()
        self.assertEqual(export["dataset_sha256"], digest)
        self.assertEqual(
            export["record_counts"],
            {
                "self_reported": len(dataset["self_reported"]),
                "observed": len(dataset["observed"]),
                "derived": len(dataset["derived"]),
                "instrumentation_proposals": len(dataset["instrumentation_proposals"]),
            },
        )

    def test_evidence_classes_are_explicit_and_separate(self) -> None:
        dataset = load_json(DATASET_PATH)
        self.assertTrue(all(item["evidence_class"] == "self_reported" for item in dataset["self_reported"]))
        self.assertTrue(all(item["evidence_class"] == "observed" for item in dataset["observed"]))
        self.assertTrue(all(item["evidence_class"] == "derived" for item in dataset["derived"]))
        self.assertTrue(all(item["evidence_class"] == "derived" for item in dataset["instrumentation_proposals"]))

    def test_public_derivative_has_no_full_transcript_or_raw_capture(self) -> None:
        dataset = load_json(DATASET_PATH)
        export = load_json(EXPORT_PATH)
        self.assertEqual(dataset["evidence_status"], "reconstructed")
        self.assertEqual(dataset["authority"], "non_authoritative")
        self.assertEqual(export["public_safety"]["full_transcript_committed"], False)
        self.assertEqual(export["public_safety"]["raw_capture_committed"], False)
        self.assertNotIn("messages", dataset)
        self.assertNotIn("transcript", dataset)
        self.assertNotIn("raw", dataset)


if __name__ == "__main__":
    unittest.main()
