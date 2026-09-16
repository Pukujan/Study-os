from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "calibration" / "manifest.json"
HUMAN_INDEX_PATH = ROOT / "docs" / "CALIBRATION_INDEX.md"
ROOT_POINTER_PATH = ROOT / "CALIBRATION_INDEX.md"
SLIDING_WINDOW_ID = "sliding-window.subject-001.2026-09-04"
SESSION_ROOT = ROOT / "sessions" / "2026-09-04" / "sliding-window-pedagogy-calibration"


class CalibrationRegistryTests(unittest.TestCase):
    def _registry(self) -> dict[str, object]:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

    def _sliding_window_dataset(self) -> dict[str, object]:
        registry = self._registry()
        self.assertEqual(registry.get("schema_version"), "study-os.calibration-index.v0.1")
        datasets = registry.get("datasets")
        self.assertIsInstance(datasets, list)
        assert isinstance(datasets, list)
        matching = [item for item in datasets if isinstance(item, dict) and item.get("calibration_id") == SLIDING_WINDOW_ID]
        self.assertEqual(len(matching), 1)
        return matching[0]

    def test_repository_discovery_entrypoints_exist(self) -> None:
        for path in (
            HUMAN_INDEX_PATH,
            ROOT_POINTER_PATH,
            REGISTRY_PATH,
            SESSION_ROOT / "README.md",
            ROOT / "domains" / "dsa" / "sliding-window" / "golden" / "README.md",
        ):
            self.assertTrue(path.is_file(), f"missing calibration discovery file: {path}")

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for text in (readme, agents):
            self.assertIn("docs/CALIBRATION_INDEX.md", text)
            self.assertIn("calibration/manifest.json", text)

    def test_registry_paths_resolve_and_ids_are_unique(self) -> None:
        registry = self._registry()
        datasets = registry.get("datasets")
        self.assertIsInstance(datasets, list)
        assert isinstance(datasets, list)

        ids = [item.get("calibration_id") for item in datasets if isinstance(item, dict)]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(isinstance(item, str) and item for item in ids))

        for dataset in datasets:
            self.assertIsInstance(dataset, dict)
            assert isinstance(dataset, dict)
            for key in ("session_root", "session_manifest", "human_index"):
                value = dataset.get(key)
                self.assertIsInstance(value, str)
                assert isinstance(value, str)
                self.assertTrue((ROOT / value).exists(), f"registry path does not resolve: {value}")

            raw = dataset.get("raw_evidence")
            self.assertIsInstance(raw, dict)
            assert isinstance(raw, dict)
            raw_index = raw.get("index")
            self.assertIsInstance(raw_index, str)
            assert isinstance(raw_index, str)
            self.assertTrue((ROOT / raw_index).is_file())
            parts = raw.get("parts")
            self.assertIsInstance(parts, list)
            assert isinstance(parts, list)
            self.assertTrue(parts)
            for path in parts:
                self.assertIsInstance(path, str)
                assert isinstance(path, str)
                self.assertTrue((ROOT / path).is_file(), f"raw calibration part missing: {path}")

            derived = dataset.get("derived")
            self.assertIsInstance(derived, list)
            assert isinstance(derived, list)
            for path in derived:
                self.assertIsInstance(path, str)
                assert isinstance(path, str)
                self.assertTrue((ROOT / path).is_file(), f"derived calibration artifact missing: {path}")

            goldens = dataset.get("goldens")
            self.assertIsInstance(goldens, dict)
            assert isinstance(goldens, dict)
            fixtures = goldens.get("fixtures")
            self.assertIsInstance(fixtures, list)
            assert isinstance(fixtures, list)
            for path in fixtures:
                self.assertIsInstance(path, str)
                assert isinstance(path, str)
                self.assertTrue((ROOT / path).is_file(), f"golden fixture missing: {path}")

    def test_sliding_window_registry_matches_session_manifest(self) -> None:
        dataset = self._sliding_window_dataset()
        self.assertEqual(dataset.get("runtime_authoritative"), False)
        self.assertEqual(dataset.get("pir_compilation_status"), "unfinished")

        goldens = dataset.get("goldens")
        self.assertIsInstance(goldens, dict)
        assert isinstance(goldens, dict)
        self.assertEqual(goldens.get("status"), "partial")

        raw = dataset.get("raw_evidence")
        self.assertIsInstance(raw, dict)
        assert isinstance(raw, dict)
        parts = raw.get("parts")
        self.assertIsInstance(parts, list)
        assert isinstance(parts, list)

        expected_parts = [
            f"sessions/2026-09-04/sliding-window-pedagogy-calibration/raw/chat-visible-transcript-part{number:02d}.md"
            for number in range(1, 9)
        ]
        self.assertEqual(parts, expected_parts)

        session_manifest = json.loads((SESSION_ROOT / "manifest.json").read_text(encoding="utf-8"))
        session_raw = session_manifest["artifacts"]["raw"]
        expected_session_raw = ["raw/chat-visible-transcript.md"] + [
            f"raw/chat-visible-transcript-part{number:02d}.md" for number in range(1, 9)
        ]
        self.assertEqual(session_raw, expected_session_raw)

        registered_relative = [str(Path(path).relative_to(SESSION_ROOT.relative_to(ROOT))) for path in parts]
        self.assertEqual(registered_relative, expected_session_raw[1:])

    def test_visible_transcript_index_covers_all_preserved_parts(self) -> None:
        index_text = (SESSION_ROOT / "raw" / "chat-visible-transcript.md").read_text(encoding="utf-8")
        self.assertIn("docs/CALIBRATION_INDEX.md", index_text)
        self.assertIn("calibration/manifest.json", index_text)
        for number in range(1, 9):
            self.assertIn(f"chat-visible-transcript-part{number:02d}.md", index_text)


if __name__ == "__main__":
    unittest.main()
