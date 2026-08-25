from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.check_dependency_lock import (
    DependencyLockFailure,
    check_dependency_lock,
    parse_lock,
)


class DependencyLockTests(unittest.TestCase):
    def test_current_dependency_lock_covers_direct_dependencies(self) -> None:
        check_dependency_lock()

    def test_lock_rejects_non_exact_versions(self) -> None:
        with self.assertRaises(DependencyLockFailure):
            parse_lock("ruff>=0.16,<1\n")

    def test_lock_rejects_duplicate_normalized_names(self) -> None:
        with self.assertRaises(DependencyLockFailure):
            parse_lock("typing_extensions==4.16.0\ntyping-extensions==4.16.0\n")

    def test_missing_direct_dependency_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            requirements = root / "requirements-dev.txt"
            lock = root / "requirements-dev.lock"
            pyproject = root / "pyproject.toml"
            requirements.write_text("ruff>=0.16,<1\n", encoding="utf-8")
            lock.write_text("coverage==7.15.4\n", encoding="utf-8")
            pyproject.write_text(
                "[project]\nname='example'\nversion='0.0.0'\ndependencies=[]\n",
                encoding="utf-8",
            )
            with self.assertRaises(DependencyLockFailure):
                check_dependency_lock(requirements, lock, pyproject)


if __name__ == "__main__":
    unittest.main()
