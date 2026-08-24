from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INGEST = ROOT / "tools" / "ingest_transcript.py"


class TranscriptIngestTests(unittest.TestCase):
    def test_ingest_preserves_bytes_hash_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            source = temp / "source.md"
            payload = b"# Learning session\n\nuser: I do not understand the window invariant.\n"
            source.write_bytes(payload)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(INGEST),
                    str(source),
                    "--repo-root",
                    str(temp),
                    "--subject",
                    "subject-001",
                    "--domain",
                    "dsa",
                    "--concept",
                    "sliding-window",
                    "--provider",
                    "chatgpt",
                    "--capture-method",
                    "copy",
                    "--started-at",
                    "2026-08-23T22:00:00-04:00",
                    "--session-id",
                    "test-session",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            result = json.loads(completed.stdout)
            session = temp / "sessions" / "2026-08-23" / "test-session"
            raw = session / "raw" / "transcript.original.md"
            manifest = json.loads((session / "manifest.json").read_text(encoding="utf-8"))

            self.assertEqual(raw.read_bytes(), payload)
            expected_hash = hashlib.sha256(payload).hexdigest()
            self.assertEqual(result["raw_sha256"], expected_hash)
            self.assertEqual(manifest["raw_artifacts"][0]["sha256"], expected_hash)
            self.assertEqual(manifest["subject_id"], "subject-001")
            self.assertEqual(manifest["domain"], "dsa")
            self.assertEqual(manifest["concepts"], ["sliding-window"])
            self.assertEqual(manifest["source"]["provider"], "chatgpt")

    def test_ingest_refuses_to_overwrite_raw_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            source = temp / "source.txt"
            source.write_text("first", encoding="utf-8")
            command = [
                sys.executable,
                str(INGEST),
                str(source),
                "--repo-root",
                str(temp),
                "--started-at",
                "2026-08-23T22:00:00-04:00",
                "--session-id",
                "immutable-session",
            ]

            subprocess.run(command, check=True, capture_output=True, text=True)
            second = subprocess.run(command, capture_output=True, text=True)

            self.assertNotEqual(second.returncode, 0)
            self.assertIn("Refusing to overwrite immutable evidence", second.stderr)


if __name__ == "__main__":
    unittest.main()
