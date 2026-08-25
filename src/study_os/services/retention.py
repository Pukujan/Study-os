"""Retention lifecycle helpers for the canonical Study OS service.

This module contains validation/projection helpers only.  It intentionally
does not open the database or mutate canonical state; `StudyOSService` remains
the persistence boundary.  The helpers let the eventual `record_assessment`
retention closure stay small and testable while P1 transport/schema exposure
is reconciled.
"""

from __future__ import annotations

from typing import Any, Mapping

from ..errors import conflict, integrity, not_found, validation


def validate_retention_probe_id(retention_probe_id: str | None) -> str | None:
    if retention_probe_id is None:
        return None
    if not isinstance(retention_probe_id, str) or not retention_probe_id.strip():
        raise validation("retention_probe_id must be a non-empty string when supplied")
    return retention_probe_id


def validate_scheduled_probe(
    probe: Mapping[str, Any] | None,
    *,
    retention_probe_id: str,
    subject_id: str,
) -> Mapping[str, Any]:
    if probe is None:
        raise not_found("Retention probe does not exist", retention_probe_id=retention_probe_id)
    if probe.get("subject_id") != subject_id:
        raise integrity(
            "Retention probe belongs to a different subject",
            retention_probe_id=retention_probe_id,
            expected_subject_id=subject_id,
        )
    if probe.get("status") != "scheduled":
        raise conflict(
            "Retention probe is not scheduled",
            retention_probe_id=retention_probe_id,
            status=probe.get("status"),
        )
    return probe


def retention_result_payload(
    *,
    assessment_id: str,
    capability: str,
    result: str,
    assistance_level: str,
    evidence_ids: list[str],
    completed_at: str,
) -> dict[str, Any]:
    for field_name, value in (
        ("assessment_id", assessment_id),
        ("capability", capability),
        ("result", result),
        ("assistance_level", assistance_level),
        ("completed_at", completed_at),
    ):
        if not isinstance(value, str) or not value.strip():
            raise validation(f"{field_name} must be a non-empty string")
    if not evidence_ids or any(not isinstance(value, str) or not value for value in evidence_ids):
        raise validation("evidence_ids must contain at least one non-empty string")
    return {
        "assessment_id": assessment_id,
        "capability": capability,
        "result": result,
        "assistance_level": assistance_level,
        "evidence_ids": list(evidence_ids),
        "completed_at": completed_at,
    }
