from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.check_engineering_baseline import (
    _imported_modules,
    check_pure_logic_boundaries,
    check_version_consistency,
)


class EngineeringBaselineTests(unittest.TestCase):
    def test_current_versions_and_approved_tool_count_are_consistent(self) -> None:
        check_version_consistency()

    def test_current_adaptive_and_curriculum_code_respects_boundary(self) -> None:
        check_pure_logic_boundaries()

    def test_import_parser_detects_absolute_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.py"
            path.write_text(
                "import study_os.db.connection\nfrom study_os.services import runtime\n",
                encoding="utf-8",
            )
            self.assertEqual(
                _imported_modules(path),
                {"study_os.db.connection", "study_os.services"},
            )


if __name__ == "__main__":
    unittest.main()
