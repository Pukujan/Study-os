"""Validate content/human-feedback pack (issue #164) — no parallel DB."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "content" / "human-feedback"
JSONL = PACK / "feedback.jsonl"
SCHEMA = PACK / "schema.v1.json"
REQUIRED_SEED_TAGS = {"too_complex", "crash", "prefer_graph", "no_bullets", "simpler_charts"}


class HumanFeedbackPackTests(unittest.TestCase):
    def test_schema_and_seed_exist(self) -> None:
        self.assertTrue(SCHEMA.is_file())
        self.assertTrue(JSONL.is_file())
        self.assertTrue((PACK / "README.md").is_file())

    def test_seed_entries_match_schema_shape_and_assets(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        required = set(schema["required"])
        allowed_tags = set(schema["properties"]["tags"]["items"]["enum"])
        allowed_stores = set(schema["properties"]["store"]["enum"])
        seen_tags: set[str] = set()
        ids: set[str] = set()

        lines = [ln for ln in JSONL.read_text(encoding="utf-8").splitlines() if ln.strip()]
        self.assertGreaterEqual(len(lines), 4, "seed must include tonight's critiques")

        for line in lines:
            row = json.loads(line)
            missing = required - set(row)
            self.assertFalse(missing, f"missing required keys: {missing}")
            self.assertNotIn(row["id"], ids)
            ids.add(row["id"])
            self.assertIn(row["store"], allowed_stores)
            self.assertNotEqual(
                row["store"],
                "sqlite",
                "must not invent a parallel DB store",
            )
            for tag in row["tags"]:
                self.assertIn(tag, allowed_tags)
                seen_tags.add(tag)
            shot = row.get("screenshot")
            if shot:
                path = ROOT / shot["path"]
                self.assertTrue(path.is_file(), f"missing asset {shot['path']}")
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(digest, shot["sha256"])

        self.assertTrue(
            REQUIRED_SEED_TAGS <= seen_tags,
            f"seed tags missing {REQUIRED_SEED_TAGS - seen_tags}",
        )

    def test_no_new_feedback_migration_in_this_pack(self) -> None:
        """Guardrail: #164 is git JSONL + docs; do not add ux.human_feedback SQL."""
        migrations = list((ROOT / "src" / "study_os" / "web" / "migrations").glob("*.sql"))
        for path in migrations:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("human_feedback", text.lower())
            self.assertNotIn("CREATE TABLE ux.feedback_v2", text)

    def test_append_helper_writes_jsonl(self) -> None:
        script = ROOT / "tools" / "append_human_feedback.py"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "content" / "human-feedback"
            pack.mkdir(parents=True)
            (pack / "feedback.jsonl").write_text("", encoding="utf-8")
            (pack / "assets").mkdir()
            png = tmp_path / "shot.png"
            png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--repo-root",
                    str(tmp_path),
                    "--text",
                    "unit-test critique: prefer simpler chart",
                    "--tag",
                    "simpler_charts",
                    "--screenshot",
                    str(png),
                    "--issue",
                    "164",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            rows = [
                json.loads(ln)
                for ln in (pack / "feedback.jsonl").read_text(encoding="utf-8").splitlines()
                if ln.strip()
            ]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["store"], "git.jsonl")
            self.assertEqual(rows[0]["author"], "Pukujan")
            self.assertTrue((tmp_path / rows[0]["screenshot"]["path"]).is_file())


if __name__ == "__main__":
    unittest.main()
