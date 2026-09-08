"""Deterministic prerequisite-sensitive remediation routing.

This controller consumes canonical learner state plus a structured diagnosis
proposal.  It may block progression and route to a missing prerequisite or a
same-target representation intervention.  The diagnosis model itself cannot
advance course state or select mastery outcomes.
"""

from __future__ import annotations

from typing import Sequence

from .contracts import ASSISTANCE_LEVELS, DecisionProposal, LearnerSnapshot, SelectedAction
from .diagnosis import DiagnosisProposal

PREREQUISITE_REMEDIATION_VERSION = "0.1.0"
PREREQUISITE_PASS_STATUSES = frozenset({"pass_unaided", "pass_transfer", "pass_delayed"})
VISUAL_TRACE_FAMILIES = frozenset({"decision_tree", "state_flow", "sequence_trace"})


def _non_empty(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _ordered_unique(values: Sequence[str], field_name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an array of strings")
    result = tuple(values)
    if any(not isinstance(value, str) or not value.strip() for value in result):
        raise ValueError(f"{field_name} must contain non-empty strings")
    if len(result) != len(set(result)):
        raise ValueError(f"{field_name} must be unique")
    return result


def _bounded_assistance(ceiling: str, desired: str = "A2") -> str:
    if ceiling not in ASSISTANCE_LEVELS:
        raise ValueError(f"unsupported assistance ceiling: {ceiling}")
    desired_number = int(desired[1:])
    ceiling_number = int(ceiling[1:])
    return f"A{min(desired_number, ceiling_number)}"


def _missing_prerequisites(snapshot: LearnerSnapshot, ordered: tuple[str, ...]) -> tuple[str, ...]:
    missing: list[str] = []
    for competency_id in ordered:
        state = snapshot.capabilities.get(competency_id)
        if state is None or state.status not in PREREQUISITE_PASS_STATUSES:
            missing.append(competency_id)
    return tuple(missing)


def _authorized_operations(diagnosis: DiagnosisProposal, *, prerequisite_route: bool) -> list[str]:
    families = diagnosis.families()
    operations: list[str] = []
    if prerequisite_route or "decomposition_too_coarse" in families:
        operations.append("smaller_step")
    if "representation_interference" in families:
        operations.append("change_representation")
    if set(diagnosis.representation_signals.requested_families) & VISUAL_TRACE_FAMILIES:
        operations.append("show_trace")
    return list(dict.fromkeys(operations))


def _representation_constraints(diagnosis: DiagnosisProposal) -> dict[str, object]:
    signals = diagnosis.representation_signals
    return {
        "requested_families": list(signals.requested_families),
        "avoid_families": list(signals.avoid_families),
        "code_visibility": signals.code_visibility,
        "interaction_granularity": signals.interaction_granularity,
    }


def propose_prerequisite_sensitive_remediation(
    snapshot: LearnerSnapshot,
    diagnosis: DiagnosisProposal,
    *,
    parent_candidate_id: str,
    parent_competency_id: str,
    ordered_prerequisite_ids: Sequence[str],
    assistance_ceiling: str = "A2",
) -> DecisionProposal:
    """Return a bounded remediation route without changing course progression.

    A missing-prerequisite diagnosis can route only to an unsatisfied canonical
    prerequisite of the active parent competency.  Ambiguous or mismatched
    diagnosis fails closed and requests a diagnostic probe rather than guessing.
    Representation interference without a missing prerequisite remains on the
    same target.
    """

    if snapshot.phase != "instruction":
        raise ValueError("prerequisite remediation requires snapshot.phase='instruction'")
    _non_empty(parent_candidate_id, "parent_candidate_id")
    _non_empty(parent_competency_id, "parent_competency_id")
    prerequisites = _ordered_unique(ordered_prerequisite_ids, "ordered_prerequisite_ids")
    assistance_target = _bounded_assistance(assistance_ceiling)
    missing = _missing_prerequisites(snapshot, prerequisites)
    families = diagnosis.families()

    prerequisite_candidates = tuple(
        f"{parent_candidate_id}::prerequisite::{competency_id}" for competency_id in missing
    )
    candidate_ids = (parent_candidate_id, *prerequisite_candidates)
    selected: SelectedAction | None = None
    rationale: str
    expected: dict[str, object] = {
        "parent_candidate_id": parent_candidate_id,
        "parent_competency_id": parent_competency_id,
        "missing_prerequisite_ids": list(missing),
        "progression_blocked": True,
        "canonical_parent_attempt_recording": "forbidden_until_parent_behavioral_probe",
        "diagnosis_schema_version": diagnosis.schema_version,
        "diagnosis_prompt_version": diagnosis.prompt_version,
        "representation_constraints": _representation_constraints(diagnosis),
    }

    target_prerequisite: str | None = None
    if "missing_prerequisite" in families:
        suspected_order = diagnosis.suspected_competency_ids("missing_prerequisite")
        suspected = set(suspected_order)
        canonical = set(prerequisites)
        noncanonical_suspected = tuple(
            competency_id for competency_id in suspected_order if competency_id not in canonical
        )
        expected["suspected_prerequisite_ids"] = list(suspected_order)
        expected["noncanonical_suspected_prerequisite_ids"] = list(noncanonical_suspected)

        for competency_id in missing:
            if competency_id in suspected:
                target_prerequisite = competency_id
                break
        if target_prerequisite is None and not suspected_order and len(missing) == 1:
            target_prerequisite = missing[0]

        if target_prerequisite is not None:
            operations = _authorized_operations(diagnosis, prerequisite_route=True)
            if not operations:
                operations = ["smaller_step"]
            selected = SelectedAction(
                candidate_id=f"{parent_candidate_id}::prerequisite::{target_prerequisite}",
                action_type="remediate_prerequisite",
                assistance_target=assistance_target,
                learning_operation="smaller_step",
            )
            rationale = (
                "Structured diagnosis identifies an unsatisfied canonical prerequisite; "
                "block the parent target and gather behavioral micro-evidence on that prerequisite."
            )
            expected.update(
                {
                    "target_competency_id": target_prerequisite,
                    "authorized_operations": operations,
                    "required_next_evidence": "behavioral_micro_probe",
                    "parent_reentry": "controller_authorized_after_prerequisite_assessment",
                    "diagnostic_probe_required": False,
                }
            )
        else:
            rationale = (
                "Missing-prerequisite diagnosis is ambiguous, noncanonical, already satisfied, "
                "or does not match an unsatisfied canonical prerequisite; fail closed and gather "
                "a diagnostic probe before selecting a remediation target."
            )
            expected.update(
                {
                    "target_competency_id": None,
                    "authorized_operations": [],
                    "required_next_evidence": "diagnostic_probe",
                    "diagnostic_probe_required": True,
                }
            )
    elif families & {"representation_interference", "decomposition_too_coarse"}:
        operations = _authorized_operations(diagnosis, prerequisite_route=False)
        primary_operation = (
            "change_representation" if "change_representation" in operations else "smaller_step"
        )
        selected = SelectedAction(
            candidate_id=parent_candidate_id,
            action_type="remediate_same_target",
            assistance_target=assistance_target,
            learning_operation=primary_operation,
        )
        rationale = (
            "No missing prerequisite is established; keep the canonical target fixed while changing only the "
            "authorized representation/decomposition dimension."
        )
        expected.update(
            {
                "target_competency_id": parent_competency_id,
                "authorized_operations": operations,
                "required_next_evidence": "behavioral_reprobe_same_target",
                "diagnostic_probe_required": False,
            }
        )
    else:
        rationale = (
            "Diagnosis does not justify prerequisite traversal or representation remediation; "
            "fail closed and request additional behavioral evidence."
        )
        expected.update(
            {
                "target_competency_id": None,
                "authorized_operations": [],
                "required_next_evidence": "diagnostic_probe",
                "diagnostic_probe_required": True,
            }
        )

    return DecisionProposal(
        component_name="prerequisite_sensitive_remediation_router",
        implementation="study_os.adaptive.prerequisite_remediation.propose_prerequisite_sensitive_remediation",
        component_version=PREREQUISITE_REMEDIATION_VERSION,
        mode="shadow",
        phase=snapshot.phase,
        candidates=candidate_ids,
        selected=selected,
        rationale=rationale,
        expected_evidence=expected,
    )
