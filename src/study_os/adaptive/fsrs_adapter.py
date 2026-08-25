"""FSRS-backed retention scheduling behind the Study OS shadow boundary.

The maintained ``fsrs`` package owns the scheduling mathematics.  This
adapter only validates Study OS inputs, binds scheduling proposals to
canonical evidence, and translates donor state into auditable
``DecisionProposal`` payloads.  It does not write checkpoints or probes.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib.metadata import version
from typing import Any, Iterable, Mapping

from fsrs import Card, Rating, Scheduler

from .contracts import CandidateExclusion, CandidateScore, DecisionProposal, LearnerSnapshot, SelectedAction

FSRS_ADAPTER_VERSION = "0.1.0"
FSRS_PACKAGE_VERSION = version("fsrs")
FSRS_RATINGS = {
    "again": Rating.Again,
    "hard": Rating.Hard,
    "good": Rating.Good,
    "easy": Rating.Easy,
}


def _require_utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo != timezone.utc:
        raise ValueError(f"{field_name} must be a timezone-aware UTC datetime")
    return value


def _iso_utc(value: datetime) -> str:
    return _require_utc(value, "datetime").isoformat().replace("+00:00", "Z")


def _desired_retention(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("desired_retention must be numeric")
    result = float(value)
    if not math.isfinite(result) or not 0.0 < result < 1.0:
        raise ValueError("desired_retention must be finite and in (0,1)")
    return result


def _scheduler(desired_retention: float) -> Scheduler:
    # Fuzzing is deliberately disabled for auditable/replayable Study OS
    # shadow decisions.  We otherwise use the maintained FSRS defaults.
    return Scheduler(desired_retention=_desired_retention(desired_retention), enable_fuzzing=False)


def _stable_card_id(subject_id: str, concept_id: str) -> int:
    digest = hashlib.blake2b(
        f"study-os-fsrs:{subject_id}:{concept_id}".encode("utf-8"),
        digest_size=8,
    ).digest()
    return int.from_bytes(digest, "big") & ((1 << 63) - 1)


def _card_from_state(
    *,
    snapshot: LearnerSnapshot,
    concept_id: str,
    card_state: Mapping[str, Any] | None,
    initial_due: datetime,
) -> Card:
    if card_state is None:
        return Card(
            card_id=_stable_card_id(snapshot.subject_id, concept_id),
            due=_require_utc(initial_due, "initial_due"),
        )
    try:
        return Card.from_dict(dict(card_state))
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("card_state is not a valid FSRS card dictionary") from exc


@dataclass(frozen=True, slots=True)
class FsrsMaintenanceCandidate:
    """One already-reviewed concept eligible for retention consideration."""

    concept_id: str
    card_state: Mapping[str, Any]
    goal_relevance: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.concept_id, str) or not self.concept_id.strip():
            raise ValueError("concept_id must be a non-empty string")
        if not isinstance(self.card_state, Mapping):
            raise ValueError("card_state must be an object")
        if isinstance(self.goal_relevance, bool) or not isinstance(self.goal_relevance, (int, float)):
            raise ValueError("goal_relevance must be numeric")
        relevance = float(self.goal_relevance)
        if not math.isfinite(relevance) or not 0.0 <= relevance <= 1.0:
            raise ValueError("goal_relevance must be finite and in [0,1]")


def propose_fsrs_review_update(
    snapshot: LearnerSnapshot,
    *,
    concept_id: str,
    source_assessment_id: str,
    rating: str,
    review_datetime: datetime,
    card_state: Mapping[str, Any] | None = None,
    review_duration_ms: int | None = None,
    desired_retention: float = 0.9,
) -> DecisionProposal:
    """Apply one explicit FSRS rating and propose the next due state.

    ``rating`` is deliberately explicit; this adapter never converts a generic
    Study OS pass/fail result into FSRS semantics.  The source assessment must
    already be part of the canonical evidence supporting the snapshot.
    """

    if snapshot.phase != "maintenance":
        raise ValueError("FSRS review update requires snapshot.phase='maintenance'")
    if not isinstance(concept_id, str) or not concept_id.strip():
        raise ValueError("concept_id must be a non-empty string")
    if not isinstance(source_assessment_id, str) or not source_assessment_id.strip():
        raise ValueError("source_assessment_id must be a non-empty string")
    if source_assessment_id not in snapshot.evidence_ids():
        raise ValueError("source_assessment_id must resolve through LearnerSnapshot canonical evidence")
    rating_key = rating.strip().lower() if isinstance(rating, str) else ""
    if rating_key not in FSRS_RATINGS:
        raise ValueError("rating must be one of: again, hard, good, easy")
    reviewed_at = _require_utc(review_datetime, "review_datetime")
    if review_duration_ms is not None:
        if isinstance(review_duration_ms, bool) or not isinstance(review_duration_ms, int) or review_duration_ms < 0:
            raise ValueError("review_duration_ms must be an integer >= 0")

    scheduler = _scheduler(desired_retention)
    card = _card_from_state(
        snapshot=snapshot,
        concept_id=concept_id,
        card_state=card_state,
        initial_due=reviewed_at,
    )
    retrievability_before = scheduler.get_card_retrievability(card, current_datetime=reviewed_at)
    reviewed_card, review_log = scheduler.review_card(
        card=card,
        rating=FSRS_RATINGS[rating_key],
        review_datetime=reviewed_at,
        review_duration=review_duration_ms,
    )
    due_at = _iso_utc(reviewed_card.due)
    urgency_before = 1.0 - retrievability_before

    return DecisionProposal(
        component_name="py_fsrs_retention_scheduler",
        implementation="study_os.adaptive.fsrs_adapter.propose_fsrs_review_update",
        component_version=FSRS_ADAPTER_VERSION,
        mode="shadow",
        phase=snapshot.phase,
        candidates=(concept_id,),
        scores=(
            CandidateScore(
                candidate_id=concept_id,
                components={
                    "retrievability_before": retrievability_before,
                    "retention_urgency_before": urgency_before,
                },
                total=urgency_before,
            ),
        ),
        selected=SelectedAction(
            candidate_id=concept_id,
            action_type="schedule_retention_probe",
            assistance_target="A0",
            learning_operation="delayed_retrieval",
        ),
        rationale=(
            f"FSRS {FSRS_PACKAGE_VERSION} rated {concept_id}={rating_key}; "
            f"next due {due_at} with deterministic fuzzing disabled"
        ),
        expected_evidence={
            "competencies": [concept_id],
            "source_assessment_id": source_assessment_id,
            "fsrs": {
                "package_version": FSRS_PACKAGE_VERSION,
                "adapter_version": FSRS_ADAPTER_VERSION,
                "desired_retention": float(desired_retention),
                "enable_fuzzing": False,
                "rating": rating_key,
                "review_datetime": _iso_utc(reviewed_at),
                "review_duration_ms": review_duration_ms,
                "retrievability_before": retrievability_before,
                "due_at": due_at,
                "card": reviewed_card.to_dict(),
                "review_log": review_log.to_dict(),
            },
        },
    )


def propose_fsrs_maintenance(
    snapshot: LearnerSnapshot,
    candidates: Iterable[FsrsMaintenanceCandidate],
    *,
    current_datetime: datetime,
    desired_retention: float = 0.9,
) -> DecisionProposal:
    """Choose the most urgent *due* reviewed concept for retention probing."""

    if snapshot.phase != "maintenance":
        raise ValueError("FSRS maintenance selector requires snapshot.phase='maintenance'")
    now = _require_utc(current_datetime, "current_datetime")
    scheduler = _scheduler(desired_retention)
    candidate_tuple = tuple(candidates)
    ids = [candidate.concept_id for candidate in candidate_tuple]
    if len(ids) != len(set(ids)):
        raise ValueError("concept candidate IDs must be unique")

    exclusions: list[CandidateExclusion] = []
    scores: list[CandidateScore] = []
    eligible: list[tuple[FsrsMaintenanceCandidate, float, float]] = []

    for candidate in candidate_tuple:
        card = _card_from_state(
            snapshot=snapshot,
            concept_id=candidate.concept_id,
            card_state=candidate.card_state,
            initial_due=now,
        )
        if card.last_review is None or card.stability is None:
            exclusions.append(
                CandidateExclusion(candidate.concept_id, "fsrs_card_unreviewed")
            )
            continue
        if card.due > now:
            exclusions.append(
                CandidateExclusion(
                    candidate.concept_id,
                    "retention_not_due",
                    detail=_iso_utc(card.due),
                )
            )
            continue
        retrievability = scheduler.get_card_retrievability(card, current_datetime=now)
        urgency = 1.0 - retrievability
        score = urgency * float(candidate.goal_relevance)
        scores.append(
            CandidateScore(
                candidate_id=candidate.concept_id,
                components={
                    "retrievability": retrievability,
                    "retention_urgency": urgency,
                    "goal_relevance": float(candidate.goal_relevance),
                },
                total=score,
            )
        )
        eligible.append((candidate, score, retrievability))

    selected = None
    expected: dict[str, Any] = {
        "competencies": [],
        "selection_objective": "due_retention_urgency_x_goal_relevance",
        "fsrs_package_version": FSRS_PACKAGE_VERSION,
        "desired_retention": float(desired_retention),
    }
    if eligible:
        winner, score, retrievability = sorted(
            eligible,
            key=lambda item: (-item[1], item[0].concept_id),
        )[0]
        selected = SelectedAction(
            winner.concept_id,
            "retention_probe",
            assistance_target="A0",
            learning_operation="delayed_retrieval",
        )
        rationale = (
            f"selected due retention concept {winner.concept_id}: score={score:.6f}, "
            f"retrievability={retrievability:.6f}"
        )
        expected.update(
            {
                "competencies": [winner.concept_id],
                "retrievability": retrievability,
            }
        )
    else:
        rationale = "no reviewed FSRS retention candidate is currently due"

    return DecisionProposal(
        component_name="py_fsrs_maintenance_selector",
        implementation="study_os.adaptive.fsrs_adapter.propose_fsrs_maintenance",
        component_version=FSRS_ADAPTER_VERSION,
        mode="shadow",
        phase=snapshot.phase,
        candidates=tuple(ids),
        exclusions=tuple(exclusions),
        scores=tuple(scores),
        selected=selected,
        rationale=rationale,
        expected_evidence=expected,
    )
