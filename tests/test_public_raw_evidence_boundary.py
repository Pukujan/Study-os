from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "tools" / "validate_repo.py"


def load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("study_os_validate_repo", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load validate_repo.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PublicRawEvidenceBoundaryTests(unittest.TestCase):
    def test_existing_authorized_public_raw_corpora_pass(self) -> None:
        validator = load_validator()
        paths = [
            (
                "sessions/2026-09-03/mcp-recovery-transcript-gap/raw/public-export/"
                "chatgpt-6a8ca3b3-6434-83ea-a807-98080d8bcada/turns.jsonl"
            ),
            (
                "sessions/2026-09-04/sliding-window-pedagogy-calibration/raw/"
                "chat-visible-transcript-part08.md"
            ),
        ]

        with patch.object(validator, "tracked_files", return_value=paths):
            validator.check_public_data_boundary()

    def test_unrelated_raw_session_is_still_rejected(self) -> None:
        validator = load_validator()
        paths = ["sessions/2026-09-05/unapproved/raw/transcript.md"]

        with patch.object(validator, "tracked_files", return_value=paths):
            with self.assertRaisesRegex(validator.ValidationFailure, "Private/raw evidence"):
                validator.check_public_data_boundary()

    def test_prefix_near_miss_does_not_expand_authorization(self) -> None:
        validator = load_validator()
        paths = [
            (
                "sessions/2026-09-04/sliding-window-pedagogy-calibration-copy/raw/"
                "chat-visible-transcript.md"
            )
        ]

        with patch.object(validator, "tracked_files", return_value=paths):
            with self.assertRaises(validator.ValidationFailure):
                validator.check_public_data_boundary()


if __name__ == "__main__":
    unittest.main()
