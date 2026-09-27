"""SOS-0014 mascot sprite manifest integrity tests (unittest).

Checks web/public/mascot/manifest.json against
schemas/mascot-sprite-manifest.v1.schema.json:
  - manifest validates against the frozen schema;
  - every referenced sheet file exists;
  - recomputed sha256 of each sheet matches the manifest;
  - per-frame non-empty rule (alpha >= threshold opaque-pixel count) holds.

Pixel decoding requires Pillow. Pillow is intentionally NOT pinned in
requirements-dev.txt (the CI web job runs node; the python job runs the
repo unittest suite without imaging deps), so the pixel-gate test is
skipped with an explicit reason when Pillow is absent. The checksum +
manifest-consistency tests never need decoding and always run; the
authoritative pixel gate lives in tools/generate_mascot_frames.py,
which runs it at generation time.
"""

import hashlib
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MASCOT_DIR = REPO_ROOT / "web" / "public" / "mascot"
MANIFEST_PATH = MASCOT_DIR / "manifest.json"
SCHEMA_PATH = REPO_ROOT / "schemas" / "mascot-sprite-manifest.v1.schema.json"

try:
    from PIL import Image  # type: ignore[import-untyped]

    HAS_PIL = True
except ImportError:  # pragma: no cover - exercised only without Pillow
    HAS_PIL = False


def load_manifest():
    with MANIFEST_PATH.open("rb") as fh:
        return json.load(fh)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


@unittest.skipUnless(MANIFEST_PATH.exists(), "web/public/mascot/manifest.json not generated yet")
class MascotManifestTest(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = load_manifest()
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_manifest_matches_frozen_schema(self) -> None:
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema not installed")
        jsonschema.Draft202012Validator(self.schema).validate(self.manifest)

    def test_every_referenced_sheet_exists_and_hash_matches(self) -> None:
        for sheet in self.manifest["sheets"]:
            rel = sheet["file"].lstrip("/")
            path = REPO_ROOT / "web" / "public" / rel
            self.assertTrue(path.exists(), f"missing sheet file: {path}")
            self.assertEqual(
                sha256_file(path),
                sheet["sha256"],
                f"sha256 mismatch for {sheet['file']}",
            )

    def test_grid_metadata_consistent(self) -> None:
        for sheet in self.manifest["sheets"]:
            self.assertGreaterEqual(sheet["frames"], 1)
            self.assertLessEqual(sheet["frames"], sheet["rows"] * sheet["cols"])
            self.assertGreater(sheet["frame_w"], 0)
            self.assertGreater(sheet["frame_h"], 0)

    @unittest.skipUnless(HAS_PIL, "Pillow not installed; pixel gate runs in tools/generate_mascot_frames.py")
    def test_no_empty_frames_per_sheet(self) -> None:
        for sheet in self.manifest["sheets"]:
            path = REPO_ROOT / "web" / "public" / sheet["file"].lstrip("/")
            check = sheet["empty_frame_check"]
            threshold = check["alpha_threshold"]
            min_opaque = check["min_opaque_pixels"]
            with Image.open(path) as im:
                frames = sheet["frames"]
                cols = sheet["cols"]
                rows = sheet["rows"]
                fw, fh = sheet["frame_w"], sheet["frame_h"]
                rgba = im.convert("RGBA")
                for idx in range(frames):
                    col = idx % cols
                    row = (idx // cols) % rows
                    box = (col * fw, row * fh, (col + 1) * fw, (row + 1) * fh)
                    frame = rgba.crop(box)
                    alpha = frame.getchannel("A")
                    opaque = sum(1 for a in alpha.getdata() if a >= threshold)
                    self.assertGreaterEqual(
                        opaque,
                        min_opaque,
                        f"empty frame {idx} in {sheet['file']}: {opaque} < {min_opaque} opaque pixels",
                    )


if __name__ == "__main__":
    unittest.main()
