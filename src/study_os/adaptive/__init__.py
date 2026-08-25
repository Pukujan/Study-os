"""Adaptive Study OS components.

Donor/controller code lives behind typed, auditable adapters. Nothing in this
package owns canonical learner persistence; StudyOSService remains the
semantic persistence boundary.
"""

from .baseline import BASELINE_COMPONENT_VERSION, InstructionCandidate, propose_instruction_baseline
from .cat import (
    CAT_COMPONENT_VERSION,
    DEFAULT_TARGET_SUCCESS,
    CatItemCandidate,
    irt_fisher_information,
    irt_probability_correct,
    propose_maximum_fisher_information,
    propose_target_success_item,
)
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
from .fsrs_adapter import (
    FSRS_ADAPTER_VERSION,
    FSRS_PACKAGE_VERSION,
    FSRS_RATINGS,
    FsrsMaintenanceCandidate,
    propose_fsrs_maintenance,
    propose_fsrs_review_update,
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
    "CAT_COMPONENT_VERSION",
    "DECISION_PROPOSAL_VERSION",
    "DEFAULT_TARGET_SUCCESS",
    "DIAGNOSTIC_COMPONENT_VERSION",
    "FEEDBACK_EXPOSURES",
    "FSRS_ADAPTER_VERSION",
    "FSRS_PACKAGE_VERSION",
    "FSRS_RATINGS",
    "INTERACTION_MODES",
    "LEARNER_SNAPSHOT_VERSION",
    "SHADOW_EVENT_PAYLOAD_VERSION",
    "AttemptTelemetry",
    "CandidateExclusion",
    "CandidateScore",
    "CapabilityState",
    "CatItemCandidate",
    "DecisionProposal",
    "DiagnosticCandidate",
    "ErrorTag",
    "FsrsMaintenanceCandidate",
    "HintExposure",
    "InstructionCandidate",
    "LearnerSnapshot",
    "SelectedAction",
    "bernoulli_entropy",
    "bkt_information_gain",
    "irt_fisher_information",
    "irt_probability_correct",
    "propose_bkt_information_gain",
    "propose_fsrs_maintenance",
    "propose_fsrs_review_update",
    "propose_instruction_baseline",
    "propose_maximum_fisher_information",
    "propose_target_success_item",
    "propose_uncertainty_baseline",
    "shadow_learning_event",
]
