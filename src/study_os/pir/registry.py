from __future__ import annotations

import re

from .contracts import CanonicalTeachingAsset
from .controller import validate_asset
from .sliding_window import build_sliding_window_graph


SOURCE_PIR_COMMIT = "43599ff8ed75bd7ceeab980d078e3a2570c7725d"
CANONICAL_PROBLEM_ID = "sliding-window.max-sum-k.sep4.v1"
# v2 follows the two goldens under domains/dsa/sliding-window/golden/ step by step
# (SOS-0002). Runs pinned to v1 fail closed on the revision check.
CANONICAL_PIR_REVISION = "sep4.sliding-window.golden-box-index-enumerate-append.v2"
RENDERER_REVISION = "study-os.markdown-renderer.v1"


def sliding_window_asset() -> CanonicalTeachingAsset:
    entry_step_id, representations, assessments, steps, expansions = (
        build_sliding_window_graph()
    )
    asset = CanonicalTeachingAsset(
        schema_version="study-os.canonical-teaching-asset.v0",
        canonical_problem_id=CANONICAL_PROBLEM_ID,
        canonical_pir_revision=CANONICAL_PIR_REVISION,
        source_pir_repository="Pukujan/study-os-pedagogical-IR",
        source_pir_commit=SOURCE_PIR_COMMIT,
        controller_revision="study-os.pir-controller.v0",
        renderer_revision=RENDERER_REVISION,
        assessment_revision="study-os.pir-assessment.v0",
        entry_step_id=entry_step_id,
        aliases=(
            "given an array a and integer k find the maximum sum of any contiguous window of size k",
            "find the maximum sum of a contiguous subarray of size k",
            "maximum sum contiguous window size k",
            "sliding window maximum sum size k",
        ),
        representations=representations,
        assessments=assessments,
        steps=steps,
        expansions=expansions,
    )
    violations = validate_asset(asset)
    if violations:
        codes = ", ".join(item.code.value for item in violations)
        raise RuntimeError(f"built-in canonical PIR asset is invalid: {codes}")
    return asset


_ASSETS = {CANONICAL_PROBLEM_ID: sliding_window_asset()}


def get_asset(canonical_problem_id: str) -> CanonicalTeachingAsset | None:
    return _ASSETS.get(canonical_problem_id)


def _normalize_problem_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower()).rstrip(".?!")


def resolve_known_problem(problem_text: str, domain: str) -> CanonicalTeachingAsset | None:
    if not isinstance(problem_text, str) or not problem_text.strip():
        raise ValueError("problem_text must be a non-empty string")
    if not isinstance(domain, str) or not domain.strip():
        raise ValueError("domain must be a non-empty string")
    if domain.strip().lower() not in {"dsa", "data structures and algorithms"}:
        return None

    normalized = _normalize_problem_text(problem_text)
    asset = _ASSETS[CANONICAL_PROBLEM_ID]
    aliases = {_normalize_problem_text(alias) for alias in asset.aliases}
    return asset if normalized in aliases else None
