"""Offline invariants for Study OS helper adoption (issue #78, task SOS-0001).

Study OS owns its project/continuity state; PCM and CGM are pinned helpers.
These checks run without network access. The full PCM validator needs a
checkout of the pinned PCM commit (see AGENTS.md); adding it to CI is planned.
"""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

PCM_COMMIT = "c18bfd6064d1249996bc00c45dbbc6721ec5dfd9"
CGM_COMMIT = "f85e88bc00362c53061d95ac7811bd9c6ada8e32"
PROTOCOL_VERSION = "0.1.0-draft"

# SHA-256 of PCM schemas/v1/* at PCM_COMMIT; the directory must stay an exact copy.
PCM_SCHEMA_SHA256 = {
    "checkpoint-operation.schema.json": "f724036485853ab5b48f45f1aa4fa8f14b2d72a3f49a0e82775c61af1cbcac40",
    "checkpoint.schema.json": "3bd75a9bf81a7cf4738ddb49e358e7a79b59cd07caa2be76684fd4cbc74bf755",
    "config.schema.json": "7e18cc2a2c4a17f39c2e0b6dd16e660618be41f8e0583af85255f24726b18a4c",
    "context-pack.schema.json": "74092c2ef616a8b641862dcc7e9af12661aa4e0bada81997eb61b7196271c88d",
    "current.schema.json": "17278a79da0ea4aa64195b510d732efde58b244491ffc6d075ad90f47905d317",
    "documents.schema.json": "147337ec8212f8f933eeaabce752c54074861de011eba4749ad00b2341d8dc76",
    "project.schema.json": "2184738ed21ac184e7a8c1ff4372fa01f077dab757c4cec509115abde5781da5",
    "recovery.schema.json": "927a72b4f275dac3def742f4a66166f1d26531ba219cc2e8e26d4e439fbd8017",
    "task.schema.json": "28ebe2afe19ff35812654403f4528b20c169a8b4366ac27eb58c53718c79edf1",
}

CGM_MODULES = {
    "brand-foundation",
    "content-context",
    "writing-direction",
    "visual-direction",
    "image-generation",
    "html-demo",
}

MARKER_RE = re.compile(r"<!--\s*continuity:(?P<kind>[a-z-]+)\s+(?P<payload>\{.*\})\s*-->")
PRIVATE_REPOSITORY_NAMES = ("private-study-log",)


def load_json(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def marker(relative: str, kind: str) -> dict[str, Any]:
    found = []
    for line in (ROOT / relative).read_text(encoding="utf-8").splitlines():
        match = MARKER_RE.fullmatch(line.strip())
        if match and match.group("kind") == kind:
            found.append(json.loads(match.group("payload")))
    if len(found) != 1:
        raise AssertionError(f"{relative}: expected exactly one continuity:{kind} marker, found {len(found)}")
    return found[0]


class PcmOverlayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_json(".continuity/config.json")

    def test_config_declares_study_os_canonical_paths(self) -> None:
        self.assertEqual(self.config["schema"], "project-continuity.config.v1")
        self.assertEqual(self.config["protocol_version"], PROTOCOL_VERSION)
        self.assertEqual(self.config["task_prefix"], "SOS")
        self.assertEqual(self.config["schema_dir"], "schemas/v1")
        self.assertTrue(self.config["trackers"]["github"])
        self.assertEqual(
            self.config["canonical"],
            {"project": "docs/PROJECT_CHARTER.md", "current": "docs/HANDOFF.md", "tasks": "tasks"},
        )

    def test_protocol_schemas_are_exact_pinned_copy(self) -> None:
        schema_dir = ROOT / "schemas" / "v1"
        # Hash the canonical LF form. The pinned helper schemas are LF, and CI
        # re-checks byte identity against a fresh PCM checkout with `diff -r`.
        # Hashing raw working-tree bytes would fail on a checkout with
        # core.autocrlf=true even when the committed blobs are unchanged.
        actual = {
            path.name: hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            for path in sorted(schema_dir.glob("*"))
        }
        self.assertEqual(actual, PCM_SCHEMA_SHA256)

    def test_canonical_markers_match_config(self) -> None:
        project = marker("docs/PROJECT_CHARTER.md", "project")
        self.assertEqual(project["id"], "study-os")
        self.assertEqual(project["protocol_version"], PROTOCOL_VERSION)
        current = marker("docs/HANDOFF.md", "current")
        self.assertEqual(current["protocol_version"], PROTOCOL_VERSION)
        self.assertEqual(current["active_task"] is None, current["active_task_file"] is None)

    def test_tasks_are_issue_backed_in_this_repository(self) -> None:
        tasks = sorted((ROOT / "tasks").glob("TASK-SOS-*.md"))
        self.assertTrue(tasks, "expected at least one SOS task projection")
        for path in tasks:
            meta = marker(path.relative_to(ROOT).as_posix(), "task")
            self.assertTrue(meta["id"].startswith("SOS-"))
            self.assertRegex(meta.get("issue_url", ""), r"^https://github\.com/Pukujan/Study-os/issues/\d+$")
        current = marker("docs/HANDOFF.md", "current")
        if current["active_task_file"] is not None:
            self.assertTrue((ROOT / current["active_task_file"]).is_file())


class HelperPinConsistencyTests(unittest.TestCase):
    def test_manifest_agents_and_adapter_agree_on_pins(self) -> None:
        manifest = yaml.safe_load((ROOT / "PROJECT_MANIFEST.yaml").read_text(encoding="utf-8"))
        helpers = manifest["helpers"]
        self.assertEqual(helpers["project_continuity_modules"]["commit"], PCM_COMMIT)
        self.assertEqual(helpers["project_continuity_modules"]["protocol_version"], PROTOCOL_VERSION)
        self.assertEqual(helpers["content_generation_modules"]["commit"], CGM_COMMIT)
        self.assertIs(helpers["private_repositories_copied_into_public_outputs"], False)

        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("## Helper modules and project ownership", agents)
        self.assertIn(PCM_COMMIT, agents)
        self.assertIn(CGM_COMMIT, agents)

        system = load_json(".content-system/system-version.json")
        self.assertEqual(system["helper_commit"], CGM_COMMIT)
        self.assertEqual(system["helper_version"], helpers["content_generation_modules"]["helper_version"])


class CgmAdapterTests(unittest.TestCase):
    def test_adapter_files_declare_expected_schemas(self) -> None:
        expected = {
            "system-version.json": "content-generation.adapter.v1",
            "project-brief.json": "content-generation.project-brief.v2",
            "brand-language.json": "content-generation.brand-language.v1",
            "visual-style.json": "content-generation.visual-style.v1",
            "asset-manifest.json": "content-generation.asset-manifest.v1",
            "review-rubric.json": "content-generation.review-rubric.v1",
        }
        for name, schema_version in expected.items():
            with self.subTest(name=name):
                self.assertEqual(load_json(f".content-system/{name}")["schema_version"], schema_version)
        system = load_json(".content-system/system-version.json")
        self.assertEqual(set(system["modules"]), CGM_MODULES)
        self.assertRegex(system["helper_commit"], r"^[0-9a-f]{40}$")

    def test_brief_claims_are_pinned_and_bounded(self) -> None:
        brief = load_json(".content-system/project-brief.json")
        self.assertTrue(brief["evidence"])
        for item in brief["evidence"]:
            with self.subTest(claim=item["claim"]):
                self.assertNotEqual(item["supports"], item["limits"])
                revision = item["source_revision"]
                if revision["kind"] == "repository_artifact":
                    self.assertEqual(revision["repository"], "Pukujan/Study-os")
                    self.assertRegex(revision["commit"], r"^[0-9a-f]{40}$")
                    self.assertIn(f"/blob/{revision['commit']}/{revision['path']}", revision["uri"])
                    self.assertTrue((ROOT / revision["path"]).is_file())


class PrivateBoundaryTests(unittest.TestCase):
    def test_helper_adoption_files_carry_no_private_repository_content(self) -> None:
        paths = [
            *(ROOT / ".content-system").glob("*.json"),
            *(ROOT / ".continuity").glob("*.json"),
            *(ROOT / "tasks").glob("*.md"),
        ]
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for name in PRIVATE_REPOSITORY_NAMES:
                with self.subTest(path=path.name, name=name):
                    self.assertNotIn(name, text)


if __name__ == "__main__":
    unittest.main()
