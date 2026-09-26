"""RED E2E + cheap-vision gate contract for #126 (A9a); no product implementation here.

Asserts the *shape* of the Playwright + InferHub vision gate from Python so the
repository CI (which installs no browsers) fails loudly until A9-exec lands:

- ``web/playwright.config.ts`` with the 390x844 / 1440x900 viewport matrix;
- ``web/e2e/player-vision-gate.spec.ts`` targeting the ``player.review.*`` and
  ``player.step.regen-*`` data-testid anchors and the metamorphic relations;
- ``web/e2e/vision/{prompt,judge,receipt}.ts`` with the closed verdict code set,
  the pinned cheap-vision models, and the declared receipt marker path;
- ``web/e2e/fixtures/review-holdout.json`` for the blank-canvas false-positive control.

This test never requires a browser, a network call, or a committed receipt
artifact. A synthetic receipt on disk would be fabricated evidence.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB = REPO_ROOT / "web"
E2E = WEB / "e2e"

REQUIRED_GATE_PATHS: tuple[Path, ...] = (
    WEB / "playwright.config.ts",
    E2E / "player-vision-gate.spec.ts",
    E2E / "vision" / "prompt.ts",
    E2E / "vision" / "judge.ts",
    E2E / "vision" / "receipt.ts",
    E2E / "fixtures" / "review-holdout.json",
)

DOCS = REPO_ROOT / "docs" / "webapp"
REQUIRED_DOC_PATHS: tuple[Path, ...] = (
    DOCS / "SOS-0017_E2E_VISION_GATE_RESEARCH.md",
    DOCS / "SOS-0017_E2E_VISION_GATE_PDD.md",
    DOCS / "SOS-0017_E2E_VISION_GATE_SDD.md",
    DOCS / "SOS-0017_E2E_VISION_GATE_TDD.md",
)

SPEC_PATH = E2E / "player-vision-gate.spec.ts"
CONFIG_PATH = WEB / "playwright.config.ts"
PROMPT_PATH = E2E / "vision" / "prompt.ts"
JUDGE_PATH = E2E / "vision" / "judge.ts"
RECEIPT_PATH = E2E / "vision" / "receipt.ts"
HOLDOUT_PATH = E2E / "fixtures" / "review-holdout.json"
PACKAGE_JSON = WEB / "package.json"

REQUIRED_TESTIDS: tuple[str, ...] = (
    "player.review.panel",
    "player.review.score-",
    "player.review.why",
    "player.review.submit",
    "player.review.submitted",
    "player.step.regen-",
)

METAMORPHIC_IDS: tuple[str, ...] = ("M-regen", "M-viewport", "M-submit", "M-noop")

VISION_CODES: tuple[str, ...] = (
    "VISION_PASS",
    "VISION_FAIL_BLANK",
    "VISION_FAIL_PARTIAL",
    "VISION_FAIL_WRONG_TARGET",
    "VISION_FAIL_UNREADABLE",
    "VISION_UNCERTAIN",
    "VISION_MALFORMED",
    "VISION_PROVIDER_ERROR",
    "VISION_NOT_RUN",
    "VISION_HOLDOUT_BROKEN",
)

PRIMARY_VISION_MODEL = "ali/qwen3.8-flash"
FALLBACK_VISION_MODEL = "cb/deepseek-v4.1-flash"
RECEIPT_SCHEMA = "study_os.e2e.vision_gate_receipt/v0.1"
RECEIPT_MARKER_PATH = "web/e2e/.artifacts/vision-gate-receipt.json"

MOBILE_VIEWPORT = ("390", "844")
DESKTOP_VIEWPORT = ("1440", "900")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _missing(paths: tuple[Path, ...]) -> list[str]:
    return [str(path.relative_to(REPO_ROOT)) for path in paths if not path.is_file()]


class E2EVisionGateContractTests(unittest.TestCase):
    """Shape-only RED contract; expected to fail until A9-exec implements the gate."""

    def test_required_gate_paths_exist(self) -> None:
        missing = _missing(REQUIRED_GATE_PATHS)
        self.assertEqual(
            missing,
            [],
            "SOS-0017 gate files are missing (A9-exec product/test work): "
            f"{missing}. See docs/webapp/SOS-0017_E2E_VISION_GATE_SDD.md.",
        )

    def test_docs_present(self) -> None:
        self.assertEqual(_missing(REQUIRED_DOC_PATHS), [], "SOS-0017 design docs are missing.")

    def test_playwright_config_declares_viewport_matrix(self) -> None:
        self.assertTrue(CONFIG_PATH.is_file(), f"missing {CONFIG_PATH.name}")
        config = _read(CONFIG_PATH)
        for token in ("testDir", "projects", "webServer", '"./e2e"'):
            self.assertIn(token, config, f"playwright config must declare {token!r}")
        for width, height in (MOBILE_VIEWPORT, DESKTOP_VIEWPORT):
            self.assertIn(width, config, f"config must declare viewport width {width}")
            self.assertIn(height, config, f"config must declare viewport height {height}")

    def test_package_json_declares_playwright_and_e2e_script(self) -> None:
        self.assertTrue(PACKAGE_JSON.is_file(), "missing web/package.json")
        package = json.loads(_read(PACKAGE_JSON))
        self.assertIn(
            "@playwright/test",
            package.get("devDependencies", {}),
            "@playwright/test must be a devDependency of web/package.json",
        )
        self.assertIn("test:e2e", package.get("scripts", {}), "web/package.json needs a test:e2e script")

    def test_spec_targets_required_testids(self) -> None:
        self.assertTrue(SPEC_PATH.is_file(), f"missing {SPEC_PATH.name}")
        spec = _read(SPEC_PATH)
        absent = [testid for testid in REQUIRED_TESTIDS if testid not in spec]
        self.assertEqual(absent, [], f"spec must locate these data-testid anchors: {absent}")

    def test_spec_declares_metamorphic_relations(self) -> None:
        self.assertTrue(SPEC_PATH.is_file(), f"missing {SPEC_PATH.name}")
        spec = _read(SPEC_PATH)
        absent = [relation for relation in METAMORPHIC_IDS if relation not in spec]
        self.assertEqual(
            absent,
            [],
            f"spec must declare metamorphic relations {absent}; "
            "see docs/webapp/SOS-0017_E2E_VISION_GATE_TDD.md.",
        )

    def test_vision_prompt_declares_closed_code_set(self) -> None:
        self.assertTrue(PROMPT_PATH.is_file(), f"missing {PROMPT_PATH.name}")
        prompt = _read(PROMPT_PATH)
        absent = [code for code in VISION_CODES if code not in prompt]
        self.assertEqual(
            absent,
            [],
            f"prompt.ts must declare the closed verdict code set; missing {absent}",
        )

    def test_vision_judge_pins_cheap_models_and_records_model(self) -> None:
        self.assertTrue(JUDGE_PATH.is_file(), f"missing {JUDGE_PATH.name}")
        judge = _read(JUDGE_PATH)
        self.assertIn(PRIMARY_VISION_MODEL, judge, "judge must pin the primary cheap-vision model")
        self.assertIn(FALLBACK_VISION_MODEL, judge, "judge must pin the fallback cheap-vision model")
        self.assertIn("vision_model", judge, "judge must record which model produced a verdict")

    def test_holdout_is_wired_and_fails_closed(self) -> None:
        self.assertTrue(HOLDOUT_PATH.is_file(), f"missing {HOLDOUT_PATH.name}")
        holdout = json.loads(_read(HOLDOUT_PATH))
        cases = holdout.get("cases") if isinstance(holdout, dict) else holdout
        self.assertIsInstance(cases, list, "holdout fixture must declare a list of cases")
        self.assertTrue(cases, "blank-canvas holdout must declare at least one negative case")
        for case in cases:
            self.assertIn("expect", case, "each holdout case must declare an expected fail code")
            self.assertNotEqual(
                case.get("expect"),
                "VISION_PASS",
                "a holdout case can never expect VISION_PASS; that is the false positive this gate exists to catch",
            )
        gate_sources = _read(JUDGE_PATH) if JUDGE_PATH.is_file() else ""
        gate_sources += _read(SPEC_PATH) if SPEC_PATH.is_file() else ""
        gate_sources += _read(PROMPT_PATH) if PROMPT_PATH.is_file() else ""
        self.assertIn(
            "VISION_HOLDOUT_BROKEN",
            gate_sources,
            "gate must fail closed on a passing holdout (VISION_HOLDOUT_BROKEN)",
        )
        self.assertIn(
            "review-holdout",
            gate_sources,
            "the holdout fixture must be referenced by the judge or spec, not left inert",
        )

    def test_receipt_marker_path_and_schema_are_declared(self) -> None:
        self.assertTrue(RECEIPT_PATH.is_file(), f"missing {RECEIPT_PATH.name}")
        receipt = _read(RECEIPT_PATH)
        self.assertIn(RECEIPT_SCHEMA, receipt, "receipt.ts must declare the receipt schema id")
        self.assertIn(
            RECEIPT_MARKER_PATH,
            receipt,
            f"receipt.ts must declare the marker path {RECEIPT_MARKER_PATH}",
        )
        for field in ("verdict", "checkpoints", "holdout", "metamorphic"):
            self.assertIn(field, receipt, f"receipt must carry a {field!r} field")
        self.assertFalse(
            (REPO_ROOT / RECEIPT_MARKER_PATH).exists(),
            "a committed receipt artifact would be fabricated evidence; receipts are run outputs only",
        )


if __name__ == "__main__":
    unittest.main()
