"""Bounded, resumable qualification state for model-generated DSA plans.

This module deliberately contains orchestration state, not lesson content.  A
candidate is frozen by a content-addressed fingerprint; public evidence from a
different fingerprint can never be counted in the same qualification epoch.
The command-line runner is responsible for invoking Luna and the independent
acceptance checker, while these pure helpers make the safety rules testable
without a model call.
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


QUALIFICATION_SCHEMA_VERSION = "study-os.decomposition-reliability-qualification.v1"
STATUS_NOT_STARTED = "NOT_STARTED"
STATUS_RUNNING = "RUNNING"
STATUS_NOT_YET_QUALIFIED = "NOT_YET_QUALIFIED"
STATUS_PUBLIC_EPOCH_PASSED = "PUBLIC_EPOCH_PASSED"
STATUS_QUALIFIED = "DECOMPOSITION_RELIABILITY_QUALIFIED"


def canonical_json(value: object) -> str:
    """Return the stable JSON representation used for fingerprints/checkpoints."""

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _required_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _required_int(value: object, name: str, *, default: int | None = None) -> int:
    if value is None and default is not None:
        return default
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    return value


@dataclass(frozen=True, slots=True)
class CandidateFingerprint:
    """All mutable inputs that define one frozen candidate."""

    code_revision: str
    decomposition_prompt_version: str
    decomposition_prompt_hash: str
    diagnosis_prompt_version: str
    diagnosis_prompt_hash: str
    generation_prompt_version: str
    generation_prompt_hash: str
    teaching_plan_schema_version: str
    turn_trace_schema_version: str
    decomposer_skill_hash: str
    checklist_hash: str
    evaluation_policy_hash: str
    model_identifier: str

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            _required_text(getattr(self, name), name)

    def to_payload(self) -> dict[str, str]:
        return {name: str(getattr(self, name)) for name in self.__dataclass_fields__}

    @property
    def digest(self) -> str:
        return sha256_text(canonical_json(self.to_payload()))

    @property
    def candidate_id(self) -> str:
        return f"candidate-{self.digest[:16]}"

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "CandidateFingerprint":
        values = {name: payload.get(name) for name in cls.__dataclass_fields__}
        return cls(**values)  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True)
class QualificationBatch:
    index: int
    scenario_ids: tuple[str, ...]
    seed: int
    kind: str = "public"

    def __post_init__(self) -> None:
        if self.index < 0:
            raise ValueError("batch index must be non-negative")
        if not self.scenario_ids or len(set(self.scenario_ids)) != len(self.scenario_ids):
            raise ValueError("batch must contain unique scenario ids")
        if self.kind not in {"public", "hidden"}:
            raise ValueError("batch kind must be public or hidden")

    def to_payload(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "scenario_ids": list(self.scenario_ids),
            "seed": self.seed,
            "kind": self.kind,
        }


def plan_batches(
    scenario_ids: Iterable[str], *, batch_size: int = 4, seed: int = 0, kind: str = "public"
) -> tuple[QualificationBatch, ...]:
    """Create a deterministic shuffled partition with complete coverage."""

    if batch_size < 1:
        raise ValueError("batch_size must be >= 1")
    ids = [str(item).strip() for item in scenario_ids]
    if not ids or any(not item for item in ids):
        raise ValueError("scenario_ids must contain non-empty ids")
    if len(set(ids)) != len(ids):
        raise ValueError("scenario_ids must be unique")
    if kind not in {"public", "hidden"}:
        raise ValueError("kind must be public or hidden")
    shuffled = list(ids)
    random.Random(seed).shuffle(shuffled)
    return tuple(
        QualificationBatch(index=index, scenario_ids=tuple(shuffled[start : start + batch_size]), seed=seed, kind=kind)
        for index, start in enumerate(range(0, len(shuffled), batch_size))
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class QualificationLedger:
    """JSON-serializable state machine for one bounded qualification attempt."""

    goal: str
    batch_size: int
    seed: int
    public_scenario_ids: tuple[str, ...]
    hidden_scenario_ids: tuple[str, ...]
    candidate: CandidateFingerprint
    max_candidates: int = 10
    max_model_calls: int = 5000
    max_runtime_seconds: int | None = None
    epoch: int = 1
    status: str = STATUS_NOT_STARTED
    next_public_batch: int = 0
    next_hidden_batch: int = 0
    model_calls: int = 0
    started_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)
    public_batches: list[dict[str, Any]] = field(default_factory=list)
    hidden_batches: list[dict[str, Any]] = field(default_factory=list)
    candidate_history: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def new(
        cls,
        *,
        goal: str,
        public_scenario_ids: Sequence[str],
        hidden_scenario_ids: Sequence[str],
        candidate: CandidateFingerprint,
        batch_size: int = 4,
        seed: int = 0,
        max_candidates: int = 10,
        max_model_calls: int = 5000,
        max_runtime_seconds: int | None = None,
    ) -> "QualificationLedger":
        if max_candidates < 1 or max_model_calls < 1:
            raise ValueError("qualification bounds must be positive")
        public = tuple(str(item) for item in public_scenario_ids)
        hidden = tuple(str(item) for item in hidden_scenario_ids)
        if not public:
            raise ValueError("public corpus cannot be empty")
        if len(set(public)) != len(public) or len(set(hidden)) != len(hidden):
            raise ValueError("public and hidden scenario ids must be unique")
        if set(public) & set(hidden):
            raise ValueError("hidden scenarios must not overlap public scenarios")
        ledger = cls(
            goal=_required_text(goal, "goal"),
            batch_size=batch_size,
            seed=seed,
            public_scenario_ids=public,
            hidden_scenario_ids=hidden,
            candidate=candidate,
            max_candidates=max_candidates,
            max_model_calls=max_model_calls,
            max_runtime_seconds=max_runtime_seconds,
        )
        ledger._event("created", candidate_id=candidate.candidate_id)
        return ledger

    def _event(self, event: str, **details: Any) -> None:
        self.events.append({"at": _utc_now(), "event": event, **details})
        self.updated_at = self.events[-1]["at"]

    @property
    def candidate_count(self) -> int:
        return len(self.candidate_history) + 1

    @property
    def public_batches_plan(self) -> tuple[QualificationBatch, ...]:
        return plan_batches(self.public_scenario_ids, batch_size=self.batch_size, seed=self.seed)

    @property
    def hidden_batches_plan(self) -> tuple[QualificationBatch, ...]:
        return plan_batches(self.hidden_scenario_ids, batch_size=self.batch_size, seed=self.seed, kind="hidden") if self.hidden_scenario_ids else ()

    def budget_available(self, *, additional_model_calls: int = 0) -> bool:
        if self.candidate_count > self.max_candidates:
            return False
        return self.model_calls + additional_model_calls <= self.max_model_calls

    def start_new_candidate(self, candidate: CandidateFingerprint, *, reason: str) -> None:
        """Freeze a new candidate and restart the public epoch."""

        if self.candidate_count >= self.max_candidates:
            self.status = STATUS_NOT_YET_QUALIFIED
            self._event("candidate_bound_reached", reason=reason)
            return
        self.candidate_history.append(
            {
                "candidate_id": self.candidate.candidate_id,
                "fingerprint": self.candidate.to_payload(),
                "digest": self.candidate.digest,
                "epoch": self.epoch,
                "status": self.status,
            }
        )
        self.candidate = candidate
        self.epoch += 1
        self.next_public_batch = 0
        self.next_hidden_batch = 0
        self.public_batches.clear()
        self.hidden_batches.clear()
        self.status = STATUS_RUNNING
        self._event("new_candidate", reason=reason, candidate_id=candidate.candidate_id, epoch=self.epoch)

    def reconcile_candidate(self, current: CandidateFingerprint) -> bool:
        """Reset evidence when the frozen candidate fingerprint changed."""

        if current.digest == self.candidate.digest:
            return False
        self.start_new_candidate(current, reason="candidate_fingerprint_changed")
        return True

    def record_batch(
        self,
        batch: QualificationBatch,
        *,
        passed: bool,
        report: str | None = None,
        model_calls: int = 0,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        planned = self.public_batches_plan if batch.kind == "public" else self.hidden_batches_plan
        if batch.kind == "public":
            expected = self.next_public_batch
        else:
            expected = self.next_hidden_batch
        if batch.index != expected:
            raise ValueError(f"expected {batch.kind} batch {expected}, received {batch.index}")
        if expected >= len(planned) or tuple(batch.scenario_ids) != tuple(planned[expected].scenario_ids):
            raise ValueError(f"{batch.kind} batch contents do not match the frozen schedule")
        if model_calls < 0:
            raise ValueError("model_calls cannot be negative")
        self.model_calls += model_calls
        item = {
            "epoch": self.epoch,
            "candidate_id": self.candidate.candidate_id,
            "candidate_digest": self.candidate.digest,
            "batch": batch.to_payload(),
            "passed": bool(passed),
            "report": report,
            "model_calls": model_calls,
            "details": dict(details or {}),
        }
        target = self.public_batches if batch.kind == "public" else self.hidden_batches
        target.append(item)
        if not passed:
            self.status = STATUS_NOT_YET_QUALIFIED
            self._event("batch_failed", kind=batch.kind, batch_index=batch.index, report=report)
            return
        if batch.kind == "public":
            self.next_public_batch += 1
            self._event("public_batch_passed", batch_index=batch.index)
            if self.next_public_batch == len(self.public_batches_plan):
                self.status = STATUS_PUBLIC_EPOCH_PASSED
                self._event("public_epoch_passed", epoch=self.epoch)
        else:
            self.next_hidden_batch += 1
            self._event("hidden_batch_passed", batch_index=batch.index)
            if self.next_hidden_batch == len(self.hidden_batches_plan):
                self.status = STATUS_QUALIFIED
                self._event("qualified", epoch=self.epoch)

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": QUALIFICATION_SCHEMA_VERSION,
            "goal": self.goal,
            "batch_size": self.batch_size,
            "seed": self.seed,
            "public_scenario_ids": list(self.public_scenario_ids),
            "hidden_scenario_ids": list(self.hidden_scenario_ids),
            "candidate": {
                "candidate_id": self.candidate.candidate_id,
                "digest": self.candidate.digest,
                "fingerprint": self.candidate.to_payload(),
            },
            "bounds": {
                "max_candidates": self.max_candidates,
                "max_model_calls": self.max_model_calls,
                "max_runtime_seconds": self.max_runtime_seconds,
            },
            "candidate_count": self.candidate_count,
            "epoch": self.epoch,
            "status": self.status,
            "next_public_batch": self.next_public_batch,
            "next_hidden_batch": self.next_hidden_batch,
            "model_calls": self.model_calls,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "public_batches": list(self.public_batches),
            "hidden_batches": list(self.hidden_batches),
            "candidate_history": list(self.candidate_history),
            "events": list(self.events),
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "QualificationLedger":
        if payload.get("schema_version") != QUALIFICATION_SCHEMA_VERSION:
            raise ValueError("qualification ledger schema version mismatch")
        candidate_payload = payload.get("candidate")
        if not isinstance(candidate_payload, Mapping) or not isinstance(candidate_payload.get("fingerprint"), Mapping):
            raise ValueError("qualification ledger candidate fingerprint is missing")
        bounds = payload.get("bounds")
        if not isinstance(bounds, Mapping):
            raise ValueError("qualification ledger bounds are missing")
        ledger = cls(
            goal=_required_text(payload.get("goal"), "goal"),
            batch_size=_required_int(payload.get("batch_size"), "batch_size"),
            seed=_required_int(payload.get("seed"), "seed"),
            public_scenario_ids=tuple(str(item) for item in payload.get("public_scenario_ids", [])),
            hidden_scenario_ids=tuple(str(item) for item in payload.get("hidden_scenario_ids", [])),
            candidate=CandidateFingerprint.from_payload(candidate_payload["fingerprint"]),
            max_candidates=_required_int(bounds.get("max_candidates"), "max_candidates"),
            max_model_calls=_required_int(bounds.get("max_model_calls"), "max_model_calls"),
            max_runtime_seconds=(_required_int(bounds["max_runtime_seconds"], "max_runtime_seconds") if bounds.get("max_runtime_seconds") is not None else None),
            epoch=_required_int(payload.get("epoch"), "epoch", default=1),
            status=_required_text(payload.get("status"), "status"),
            next_public_batch=_required_int(payload.get("next_public_batch"), "next_public_batch", default=0),
            next_hidden_batch=_required_int(payload.get("next_hidden_batch"), "next_hidden_batch", default=0),
            model_calls=_required_int(payload.get("model_calls"), "model_calls", default=0),
            started_at=_required_text(payload.get("started_at"), "started_at"),
            updated_at=_required_text(payload.get("updated_at"), "updated_at"),
            public_batches=[dict(item) for item in payload.get("public_batches", [])],
            hidden_batches=[dict(item) for item in payload.get("hidden_batches", [])],
            candidate_history=[dict(item) for item in payload.get("candidate_history", [])],
            events=[dict(item) for item in payload.get("events", [])],
        )
        if candidate_payload.get("candidate_id") != ledger.candidate.candidate_id or candidate_payload.get("digest") != ledger.candidate.digest:
            raise ValueError("qualification ledger candidate identity is inconsistent")
        if ledger.candidate_count != int(payload.get("candidate_count", ledger.candidate_count)):
            raise ValueError("qualification ledger candidate count is inconsistent")
        return ledger


def write_ledger(path: Path, ledger: QualificationLedger) -> None:
    """Atomically checkpoint a ledger so interruption loses at most one write."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(ledger.to_payload(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_ledger(path: Path) -> QualificationLedger:
    if not path.exists():
        raise FileNotFoundError(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError("qualification ledger must be a JSON object")
    return QualificationLedger.from_payload(value)
