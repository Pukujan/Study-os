"""Adaptive Study OS components.

Donor/controller code lives behind typed, auditable adapters.  Nothing in
this package owns canonical learner persistence; StudyOSService remains the
semantic persistence boundary.
"""

from .contracts import (
    ASSISTANCE_LEVELS,
    CAPABILITY_STATUSES,
    DECISION_PROPOSAL_VERSION,
    LEARNER_SNAPSHOT_VERSION,
    SHADOW_EVENT_PAYLOAD_VERSION,
    CandidateExclusion,
    CandidateScore,
    CapabilityState,
    DecisionProposal,
    LearnerSnapshot,
    SelectedAction,
    shadow_learning_event,
)

__all__ = [
    "ASSISTANCE_LEVELS",
    "CAPABILITY_STATUSES",
    "DECISION_PROPOSAL_VERSION",
    "LEARNER_SNAPSHOT_VERSION",
    "SHADOW_EVENT_PAYLOAD_VERSION",
    "CandidateExclusion",
    "CandidateScore",
    "CapabilityState",
    "DecisionProposal",
    "LearnerSnapshot",
    "SelectedAction",
    "shadow_learning_event",
]
