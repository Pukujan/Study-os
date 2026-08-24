"""Content-addressed-ish private evidence files with verification helpers."""

from __future__ import annotations

import hashlib
import os
import shutil
import uuid
from pathlib import Path

from ..config import RuntimeConfig
from ..errors import integrity, validation


class EvidenceStore:
    def __init__(self, config: RuntimeConfig) -> None:
        self.config = config
        self.config.evidence_root.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.config.evidence_root, 0o700)
        except OSError:
            pass

    @staticmethod
    def sha256_bytes(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def sha256_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def capture(
        self,
        *,
        session_id: str,
        content: bytes | bytearray | memoryview | str | Path,
        media_type: str | None = None,
        capture_method: str = "local",
        source_metadata: dict | None = None,
        artifact_id: str | None = None,
    ) -> tuple[str, str, str]:
        if isinstance(content, (str, Path)):
            source = Path(content).expanduser()
            if not source.is_file():
                raise validation("Evidence source file does not exist", path=str(source))
            data = source.read_bytes()
        else:
            data = bytes(content)
        if not data:
            raise validation("Raw evidence must not be empty")
        artifact_id = artifact_id or str(uuid.uuid4())
        target_dir = self.config.evidence_root / session_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{artifact_id}.bin"
        if target.exists():
            raise integrity("Refusing to overwrite immutable evidence", artifact_id=artifact_id)
        temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
        temporary.write_bytes(data)
        try:
            os.chmod(temporary, 0o600)
        except OSError:
            pass
        os.replace(temporary, target)
        relative = target.relative_to(self.config.evidence_root).as_posix()
        return artifact_id, self.sha256_bytes(data), relative

    def resolve(self, relative_path: str) -> Path:
        root = self.config.evidence_root.resolve()
        target = (root / relative_path).resolve()
        if target != root and root not in target.parents:
            raise integrity("Evidence path escapes the configured evidence root")
        return target

    def verify(self, relative_path: str, expected_sha256: str) -> bool:
        target = self.resolve(relative_path)
        return target.is_file() and self.sha256_file(target) == expected_sha256

    def copy_to(self, destination: Path) -> None:
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(self.config.evidence_root, destination)
