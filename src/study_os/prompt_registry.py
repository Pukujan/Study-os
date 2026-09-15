"""Immutable, content-addressed prompts used by model tutoring.

Prompt text is configuration with product-contract semantics.  A prompt version
therefore cannot be overwritten after it has been registered: callers receive a
new registry when they want to add a candidate version, while historical
definitions remain addressable by version and hash.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Iterable, Mapping


PROMPT_REGISTRY_SCHEMA_VERSION = "study-os.model-tutoring-prompt-registry.v0.1"


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


@dataclass(frozen=True, slots=True)
class PromptProvenance:
    """The immutable prompt/model/schema identity attached to generated output."""

    prompt_version: str
    prompt_hash: str
    model_identifier: str
    teaching_plan_schema_version: str
    turn_trace_schema_version: str
    run_id: str
    source_problem_id: str

    def __post_init__(self) -> None:
        for name in (
            "prompt_version",
            "prompt_hash",
            "model_identifier",
            "teaching_plan_schema_version",
            "turn_trace_schema_version",
            "run_id",
            "source_problem_id",
        ):
            _require_text(getattr(self, name), name)
        if len(self.prompt_hash) != 64 or any(
            character not in "0123456789abcdef" for character in self.prompt_hash.casefold()
        ):
            raise ValueError("prompt_hash must be a SHA-256 hexadecimal digest")

    def to_payload(self) -> dict[str, str]:
        return {
            "prompt_version": self.prompt_version,
            "prompt_hash": self.prompt_hash,
            "model_identifier": self.model_identifier,
            "teaching_plan_schema_version": self.teaching_plan_schema_version,
            "turn_trace_schema_version": self.turn_trace_schema_version,
            "run_id": self.run_id,
            "source_problem_id": self.source_problem_id,
        }


@dataclass(frozen=True, slots=True)
class PromptDefinition:
    """One immutable prompt definition and its content fingerprint."""

    version: str
    role: str
    content: str
    prompt_hash: str = field(init=False)

    def __post_init__(self) -> None:
        _require_text(self.version, "version")
        _require_text(self.role, "role")
        _require_text(self.content, "content")
        digest = hashlib.sha256(self.content.encode("utf-8")).hexdigest()
        object.__setattr__(self, "prompt_hash", digest)

    @property
    def content_hash(self) -> str:
        """Alias used by callers that describe the fingerprint as a content hash."""

        return self.prompt_hash

    def provenance(
        self,
        *,
        model_identifier: str,
        teaching_plan_schema_version: str,
        turn_trace_schema_version: str,
        run_id: str,
        source_problem_id: str,
    ) -> PromptProvenance:
        return PromptProvenance(
            prompt_version=self.version,
            prompt_hash=self.prompt_hash,
            model_identifier=model_identifier,
            teaching_plan_schema_version=teaching_plan_schema_version,
            turn_trace_schema_version=turn_trace_schema_version,
            run_id=run_id,
            source_problem_id=source_problem_id,
        )

    def to_payload(self) -> dict[str, str]:
        return {
            "version": self.version,
            "role": self.role,
            "content": self.content,
            "prompt_hash": self.prompt_hash,
        }


@dataclass(frozen=True, slots=True)
class PromptRegistry:
    """An append-only-in-practice registry represented by immutable values.

    ``register`` returns a new registry.  Reusing a version, even with identical
    content, is rejected so an evidence record can always resolve one historical
    definition without an in-place overwrite ambiguity.
    """

    _definitions: tuple[PromptDefinition, ...] = ()
    _by_version: Mapping[str, PromptDefinition] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        definitions = tuple(self._definitions)
        by_version: dict[str, PromptDefinition] = {}
        for definition in definitions:
            if not isinstance(definition, PromptDefinition):
                raise TypeError("prompt registry definitions must be PromptDefinition values")
            if definition.version in by_version:
                raise ValueError(f"prompt version already registered: {definition.version}")
            by_version[definition.version] = definition
        object.__setattr__(self, "_definitions", definitions)
        object.__setattr__(self, "_by_version", MappingProxyType(by_version))

    @classmethod
    def from_definitions(cls, definitions: Iterable[PromptDefinition]) -> "PromptRegistry":
        return cls(tuple(definitions))

    @property
    def definitions(self) -> tuple[PromptDefinition, ...]:
        return self._definitions

    def register(self, definition: PromptDefinition) -> "PromptRegistry":
        """Return a registry containing ``definition`` without mutating this one."""

        if definition.version in self._by_version:
            raise ValueError(f"prompt version already registered: {definition.version}")
        return PromptRegistry((*self._definitions, definition))

    def get(self, version: str) -> PromptDefinition:
        try:
            return self._by_version[version]
        except KeyError as exc:
            raise KeyError(f"unknown prompt version: {version}") from exc

    def for_role(self, role: str, *, version: str | None = None) -> PromptDefinition:
        if version is not None:
            definition = self.get(version)
            if definition.role != role:
                raise KeyError(
                    f"prompt version {version!r} is registered for role {definition.role!r}, "
                    f"not {role!r}"
                )
            return definition
        matches = tuple(item for item in self._definitions if item.role == role)
        if len(matches) != 1:
            raise KeyError(f"prompt role {role!r} does not resolve uniquely")
        return matches[0]

    def verify(self, *, version: str, prompt_hash: str) -> PromptDefinition:
        definition = self.get(version)
        if definition.prompt_hash != prompt_hash:
            raise ValueError(f"prompt hash does not match registered version: {version}")
        return definition


DECOMPOSITION_PROMPT_VERSION = "study-os.model-tutoring-decompose.v1"
DIAGNOSIS_PROMPT_VERSION = "study-os.model-tutoring-diagnose.v1"
GENERATION_PROMPT_VERSION = "study-os.model-tutoring-generate.v1"


DEFAULT_PROMPT_REGISTRY = PromptRegistry.from_definitions(
    (
        PromptDefinition(
            version=DECOMPOSITION_PROMPT_VERSION,
            role="decomposition",
            content=(
                "Decompose the supplied technical problem into a versioned TeachingPlan. "
                "Externalize concepts, prerequisite edges, variable roles and meanings, "
                "representation constraints, semantic invariants, completion evidence, "
                "misconception metadata, and assistance boundaries. Do not write a lesson, "
                "do not infer learner mastery, and do not include hidden evaluation answers."
            ),
        ),
        PromptDefinition(
            version=DIAGNOSIS_PROMPT_VERSION,
            role="diagnosis",
            content=(
                "Assess only the learner's actual message against the controller-supplied "
                "concept. Return a diagnosis hypothesis and learner outcome. A demonstrated "
                "outcome requires an exact verbatim evidence quote; uncertainty is not mastery."
            ),
        ),
        PromptDefinition(
            version=GENERATION_PROMPT_VERSION,
            role="generation",
            content=(
                "Generate one bounded learner-visible teaching turn from the deterministic "
                "generation contract. Preserve variable meanings, representation constraints, "
                "semantic invariants, assistance limits, and the current concept. Do not "
                "change progression, claim mastery, reveal internal routing, or jump ahead."
            ),
        ),
    )
)


__all__ = [
    "DEFAULT_PROMPT_REGISTRY",
    "DECOMPOSITION_PROMPT_VERSION",
    "DIAGNOSIS_PROMPT_VERSION",
    "GENERATION_PROMPT_VERSION",
    "PROMPT_REGISTRY_SCHEMA_VERSION",
    "PromptDefinition",
    "PromptProvenance",
    "PromptRegistry",
]
