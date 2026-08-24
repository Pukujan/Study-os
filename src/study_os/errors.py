"""Stable machine-readable errors from the Study OS semantic boundary."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


RETRYABLE_CATEGORIES = {"unavailable"}
ERROR_CATEGORIES = {
    "validation_error",
    "not_found",
    "conflict",
    "integrity_error",
    "unsupported_version",
    "unavailable",
    "internal_error",
}


@dataclass
class StudyOSError(Exception):
    category: str
    message: str
    retryable: bool | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.category not in ERROR_CATEGORIES:
            self.category = "internal_error"
        if self.retryable is None:
            self.retryable = self.category in RETRYABLE_CATEGORIES
        super().__init__(self.message)

    def as_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "category": self.category,
                "message": self.message,
                "retryable": bool(self.retryable),
                "details": self.details,
            }
        }


def validation(message: str, **details: Any) -> StudyOSError:
    return StudyOSError("validation_error", message, False, details)


def not_found(message: str, **details: Any) -> StudyOSError:
    return StudyOSError("not_found", message, False, details)


def conflict(message: str, **details: Any) -> StudyOSError:
    return StudyOSError("conflict", message, False, details)


def integrity(message: str, **details: Any) -> StudyOSError:
    return StudyOSError("integrity_error", message, False, details)


def unsupported(message: str, **details: Any) -> StudyOSError:
    return StudyOSError("unsupported_version", message, False, details)


def unavailable(message: str, **details: Any) -> StudyOSError:
    return StudyOSError("unavailable", message, True, details)
