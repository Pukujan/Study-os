"""Link shadow controller proposals to actual behavioral outcomes.

Shadow selectors are only useful if Study OS can later reconstruct what they
recommended and what actually happened.  This module builds a derived learning
event that cites both the original proposal event and the canonical behavioral
assessment.  It performs no persistence itself.
"""

from __future__ import annotations

from typing import Any

from .contracts import ASSISTANCE_LEVELS, DecisionProposal

SHADOW_OUTCOME_PAYLOAD_VERSION = "p2-shadow-outcome-0.1.0"


def _non_empty(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def shadow_outcome_learning_event(
    proposal: DecisionProposal,
    *,
    proposal_event_id: str,
    assessment_id: str,
    actual_candidate_id: str,
    capability: str,
    result: str,
    assistance_level: str,
) -> dict[str, Any]:
    """Build `record_learning_event` arguments for a shadow-policy outcome."""

    if proposal.mode != "shadow":
        raise ValueError("shadow outcome requires a shadow proposal")
    for field_name, value in (
        ("proposal_event_id", proposal_event_id),
        ("assessment_id", assessment_id),
        ("actual_candidate_id", actual_candidate_id),
        ("capability", capability),
        ("result", result),
    ):
        _non_empty(value, field_name)
    if assistance_level not in ASSISTANCE_LEVELS:
        raise ValueError(f"unsupported assistance level: {assistance_level}")

    proposed_candidate_id = proposal.selected.candidate_id if proposal.selected else None
    return {
        "evidence_class": "derived",
        "event_type": "controller_shadow_outcome",
        "payload_version": SHADOW_OUTCOME_PAYLOAD_VERSION,
        "source_ids": [proposal_event_id, assessment_id],
        "payload": {
            "proposal_component": {
                "name": proposal.component_name,
                "implementation": proposal.implementation,
                "version": proposal.component_version,
            },
            "proposal_event_id": proposal_event_id,
            "proposed_candidate_id": proposed_candidate_id,
            "actual_candidate_id": actual_candidate_id,
            "proposal_followed": proposed_candidate_id == actual_candidate_id,
            "assessment_id": assessment_id,
            "capability": capability,
            "result": result,
            "assistance_level": assistance_level,
        },
    }
