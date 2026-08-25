from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.check_engineering_baseline import (
    _find_dependency_cycle,
    _imported_modules,
    _resolved_imported_modules,
    check_pure_logic_boundaries,
    check_top_level_dependency_cycles,
    check_transport_boundaries,
    check_version_consistency,
)


class EngineeringBaselineTests(unittest.TestCase):
    def test_current_versions_and_approved_tool_count_are_consistent(self) -> None:
        check_version_consistency()

    def test_current_adaptive_and_curriculum_code_respects_boundary(self) -> None:
        check_pure_logic_boundaries()

    def test_current_mcp_code_respects_transport_boundary(self) -> None:
        check_transport_boundaries()

    def test_current_top_level_packages_have_no_dependency_cycle(self) -> None:
        check_top_level_dependency_cycles()

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

    def test_relative_import_parser_resolves_study_os_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            package = Path(tmpdir) / "study_os" / "mcp"
            package.mkdir(parents=True)
            path = package / "sample.py"
            path.write_text(
                "from ..db import connection\nfrom . import tools\n",
                encoding="utf-8",
            )
            self.assertEqual(
                _resolved_imported_modules(path),
                {"study_os.db", "study_os.mcp"},
            )

    def test_dependency_cycle_detector_finds_cycle(self) -> None:
        cycle = _find_dependency_cycle(
            {
                "mcp": {"services"},
                "services": {"db"},
                "db": {"mcp"},
            }
        )
        self.assertIsNotNone(cycle)
        assert cycle is not None
        self.assertEqual(cycle[0], cycle[-1])
        self.assertEqual(set(cycle[:-1]), {"mcp", "services", "db"})

    def test_dependency_cycle_detector_accepts_acyclic_graph(self) -> None:
        self.assertIsNone(
            _find_dependency_cycle(
                {
                    "mcp": {"services"},
                    "services": {"db", "evidence"},
                    "db": set(),
                    "evidence": set(),
                }
            )
        )


if __name__ == "__main__":
    unittest.main()
