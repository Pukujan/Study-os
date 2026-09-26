"""RED shape contract for the SOS-0018 live A2A golden roleplay gate.

Browser-free, network-free and database-free on purpose: a live A2A gate costs
money and needs Postgres plus ``INFERHUB_API_KEY``, so it must stay out of
always-on CI.  This module asserts the *shape* of that gate from Python instead,
mirroring ``tests/test_player_step_review_contract.py`` (A8) and
``tests/test_e2e_vision_gate_contract.py`` (A9a).

Expected state until an executor lands ``--gate`` in
``tools/run_player_agent_evals.py``: RED.  Do not weaken these assertions to
make CI green.  Receipts are asserted as *declared path constants*, never as
artifacts on disk, so a fabricated receipt cannot satisfy the gate.
"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "tools" / "run_player_agent_evals.py"
DOCS = {
    "research": ROOT / "docs" / "webapp" / "SOS-0018_LIVE_A2A_GOLDEN_GATE_RESEARCH.md",
    "pdd": ROOT / "docs" / "webapp" / "SOS-0018_LIVE_A2A_GOLDEN_GATE_PDD.md",
    "sdd": ROOT / "docs" / "webapp" / "SOS-0018_LIVE_A2A_GOLDEN_GATE_SDD.md",
    "tdd": ROOT / "docs" / "webapp" / "SOS-0018_LIVE_A2A_GOLDEN_GATE_TDD.md",
}

RECEIPT_VERSION = "study_os.e2e.live_a2a_gate_receipt/v0.1"
RECEIPT_PATH = "evals/out/live-a2a-gate-receipt.json"
REQUIRED_PERSONAS = (
    "golden",
    "wrong_then_right",
    "partial_then_right",
    "confused_then_right",
    "answer_seeker",
    "prompt_injector",
    "clarify_re_render",
)
REQUIRED_BLOCKING_CODES = (
    "MISSING_REQUIRED_BRIDGE",
    "BRIDGE_ORDER_VIOLATION",
    "FORBIDDEN_CONCEPT_DISCLOSED",
    "ANSWER_REVEAL_FORBIDDEN",
    "MASTERY_CLAIM",
    "RETRY_SAME_EXAMPLE",
    "NO_CONFIRM_AFTER_RETRY",
    "MISSING_REGENERATE_PRESENTATION",
    "INVALID_REGENERATE_PRESENTATION",
    "RENDER_NOT_APPLIED",
    "RENDER_MOVED_STEP",
    "REVIEW_PATH_VIOLATION",
    "INJECTION_ACCEPTED",
    "HOLDOUT_NOT_CAUGHT",
    "GATE_NOT_LIVE",
)
REQUIRED_METAMORPHIC = ("MR-replay", "MR-rephrase", "MR-reorder-retry", "MR-noop")
GATE_ENV_MARKERS = ("STUDY_OS_EVAL_LIVE", "INFERHUB_API_KEY", "TEST_DATABASE_URL")


def harness_source() -> str:
    return HARNESS.read_text(encoding="utf-8")


def doc_text(key: str) -> str:
    return DOCS[key].read_text(encoding="utf-8")


def is_tracked(relpath: str) -> bool:
    listing = subprocess.run(
        ["git", "ls-files", "--", relpath],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return bool(listing.stdout.strip())


class LiveA2AGoldenGateContractTests(unittest.TestCase):
    """The gate must be declared in harness code, not implied by a doc."""

    def test_docs_present(self) -> None:
        missing = [str(path) for path in DOCS.values() if not path.is_file()]
        self.assertEqual(missing, [], f"missing SOS-0018 docs: {missing}")

    def test_docs_declare_gate_command_and_env_contract(self) -> None:
        sdd = doc_text("sdd")
        self.assertIn("--gate", sdd)
        self.assertIn("--seeds", sdd)
        for marker in GATE_ENV_MARKERS:
            self.assertIn(marker, sdd, f"SDD must declare {marker}")
        self.assertIn("python tools/run_player_agent_evals.py --gate", sdd)

    def test_docs_declare_receipt_schema_and_synthetic_banner(self) -> None:
        sdd = doc_text("sdd")
        pdd = doc_text("pdd")
        self.assertIn(RECEIPT_VERSION, sdd)
        self.assertIn(RECEIPT_PATH, sdd)
        self.assertIn("synthetic_only", sdd)
        self.assertIn("not_a_live_gate", sdd)
        self.assertIn("learn.*", pdd)
        self.assertIn(RECEIPT_VERSION, pdd)

    def test_harness_declares_receipt_version_and_path_constants(self) -> None:
        source = harness_source()
        self.assertIn("LIVE_GATE_RECEIPT_VERSION", source)
        self.assertIn("LIVE_GATE_RECEIPT_PATH", source)
        self.assertIn(RECEIPT_VERSION, source)
        self.assertIn(RECEIPT_PATH, source)

    def test_receipt_path_is_not_a_learner_evidence_path(self) -> None:
        source = harness_source()
        self.assertIn("LIVE_GATE_RECEIPT_PATH", source)
        for part in Path(RECEIPT_PATH).parts:
            self.assertNotIn("learn", part.lower(), "receipt must not live in learner evidence")

    def test_no_receipt_artifact_is_committed(self) -> None:
        self.assertFalse(
            is_tracked(RECEIPT_PATH),
            "a committed receipt is fabricated evidence and must never satisfy the gate",
        )
        self.assertFalse((ROOT / RECEIPT_PATH).exists(), "receipt artifact must not be present in the repo")

    def test_harness_declares_gate_cli_and_env_markers(self) -> None:
        source = harness_source()
        self.assertIn('"--gate"', source)
        for name in ("GATE_LIVE_ENV", "GATE_KEY_ENV", "GATE_DB_ENV"):
            self.assertIn(name, source, f"harness must declare {name}")
        for marker in GATE_ENV_MARKERS:
            self.assertIn(marker, source)

    def test_harness_declares_required_persona_suite(self) -> None:
        source = harness_source()
        self.assertIn("GATE_PERSONAS", source)
        for persona in REQUIRED_PERSONAS:
            self.assertIn(persona, source, f"gate persona suite must include {persona}")

    def test_harness_declares_blocking_detector_codes(self) -> None:
        source = harness_source()
        self.assertIn("GATE_BLOCKING_CODES", source)
        missing = [code for code in REQUIRED_BLOCKING_CODES if code not in source]
        self.assertEqual(missing, [], f"blocking detector codes not declared: {missing}")

    def test_harness_declares_metamorphic_relations_and_holdouts(self) -> None:
        source = harness_source()
        self.assertIn("GATE_METAMORPHIC_IDS", source)
        self.assertIn("GATE_HOLDOUT_FIXTURES", source)
        missing = [rel for rel in REQUIRED_METAMORPHIC if rel not in source]
        self.assertEqual(missing, [], f"metamorphic relations not declared: {missing}")

    def test_harness_declares_not_a_live_gate_verdict(self) -> None:
        source = harness_source()
        self.assertIn("not_a_live_gate", source, "a stub run must never report a live pass")


if __name__ == "__main__":
    unittest.main()
