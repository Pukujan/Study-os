"""Local-first Study OS runtime.

The package deliberately keeps the semantic service independent from the MCP
transport so the same invariants are exercised by local tests and by clients.
"""

RUNTIME_VERSION = "0.1.0"
CONTRACT_VERSION = "0.1.0"

from .config import RuntimeConfig
from .errors import StudyOSError
from .services.runtime import StudyOSService

__all__ = ["CONTRACT_VERSION", "RUNTIME_VERSION", "RuntimeConfig", "StudyOSError", "StudyOSService"]
