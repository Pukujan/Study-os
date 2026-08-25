"""Adaptive Study OS components.

Donor/controller code lives behind typed, auditable adapters. Nothing in this
package owns canonical learner persistence; StudyOSService remains the
semantic persistence boundary.
"""

from .baseline import BASELINE_COMPONENT_VERSION, InstructionCandidate, propose_instruction_baseline
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
from .diagnostic import (
    DIAGNOSTIC_COMPONENT_VERSION,
    DiagnosticCandidate,
    bernoulli_entropy,
    bkt_information_gain,
    propose_bkt_information_gain,
    propose_uncertainty_baseline,
)
from .telemetry import (
    ATTEMPT_CONTEXT_VERSION,
    FEEDBACK_EXPOSURES,
    INTERACTION_MODES,
    AttemptTelemetry,
    ErrorTag,
    HintExposure,
)

__all__ = [
    "ASSISTANCE_LEVELS",
    "ATTEMPT_CONTEXT_VERSION",
    "BASELINE_COMPONENT_VERSION",
    "CAPABILITY_STATUSES",
    "DECISION_PROPOSAL_VERSION",
    "DIAGNOSTIC_COMPONENT_VERSION",
    "FEEDBACK_EXPOSURES",
    "INTERACTION_MODES",
    "LEARNER_SNAPSHOT_VERSION",
    "SHADOW_EVENT_PAYLOAD_VERSION",
    "AttemptTelemetry",
    "CandidateExclusion",
    "CandidateScore",
    "CapabilityState",
    "DecisionProposal",
    "DiagnosticCandidate",
    "ErrorTag",
    "HintExposure",
    "InstructionCandidate",
    "LearnerSnapshot",
    "SelectedAction",
    "bernoulli_entropy",
    "bkt_information_gain",
    "propose_bkt_information_gain",
    "propose_instruction_baseline",
    "propose_uncertainty_baseline",
    "shadow_learning_event",
]
