"""CSP regression: decomposer review page must not rely on inline scripts (Refs #114)."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW_PUBLIC = ROOT / "web" / "public" / "review" / "decomposer"
REVIEW_DOCS = ROOT / "docs" / "research" / "decomposer-review"

# Match <script>...</script> that has a non-whitespace body (inline JS).
_INLINE_SCRIPT_BODY = re.compile(
    r"<script(?![^>]*\bsrc=)[^>]*>\s*\S",
    re.IGNORECASE,
)


class DecomposerReviewCspTests(unittest.TestCase):
    def test_public_index_has_no_inline_script_body(self) -> None:
        html = (REVIEW_PUBLIC / "index.html").read_text(encoding="utf-8")
        self.assertIsNone(
            _INLINE_SCRIPT_BODY.search(html),
            "inline <script> body breaks CSP script-src 'self'",
        )
        self.assertIn('src="/review/decomposer/app.js"', html)

    def test_public_app_js_exists_and_looks_like_review_app(self) -> None:
        app = REVIEW_PUBLIC / "app.js"
        self.assertTrue(app.is_file(), f"missing {app}")
        text = app.read_text(encoding="utf-8")
        self.assertIn("problemSelect", text)
        self.assertIn("/review/decomposer/data/index.json", text)
        self.assertGreater(len(text), 500)

    def test_docs_mirror_stays_in_sync(self) -> None:
        for name in ("index.html", "app.js"):
            pub = (REVIEW_PUBLIC / name).read_text(encoding="utf-8")
            docs = (REVIEW_DOCS / name).read_text(encoding="utf-8")
            self.assertEqual(pub, docs, f"{name} diverged between public and docs mirror")


if __name__ == "__main__":
    unittest.main()
