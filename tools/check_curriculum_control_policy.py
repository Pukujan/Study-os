from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "contracts" / "curriculum-control-policy.v0.1.json"

EXPECTED_TRACKS = {"ALG", "SWE", "MATH", "DATA", "ML", "DL", "AIE", "SYS", "DIAG"}
EXPECTED_DSA_BANDS = [f"DSA{index}" for index in range(7)]
EXPECTED_LEGACY_ALIASES = [f"T{index}" for index in range(7)]
EXPECTED_INDEPENDENT_BANDS = {"DSA2", "DSA4", "DSA5", "DSA6"}
REQUIRED_ANTI_PROMOTION_CASES = {
    "one_item_success",
    "supported_only_for_independent_band",
    "self_report_only",
    "average_hides_implementation_gap",
    "average_hides_transfer_gap",
    "teaching_item_reused_as_unseen_evidence",
    "ai_assisted_construction_recorded_as_unaided_manual",
    "immediate_success_inferred_as_transfer_or_delayed",
}
REQUIRED_DAILY_DEPENDENCIES = {
    "capability_evidence_refs",
    "current_and_last_successful_assistance",
    "active_goals_and_current_phase",
    "recent_exposure_summary",
    "explicit_next_fade_target",
    "next_high_information_action",
}


class CurriculumControlPolicyFailure(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CurriculumControlPolicyFailure(message)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CurriculumControlPolicyFailure(f"{path} must contain a JSON object")
    return value


def _string_list(value: object, label: str) -> list[str]:
    _require(isinstance(value, list), f"{label} must be a list")
    result = list(value)
    _require(all(isinstance(item, str) and item for item in result), f"{label} must contain non-empty strings")
    return result


def validate_policy(policy: dict[str, Any]) -> None:
    _require(policy.get("policy_version") == "0.1.0", "policy_version must remain 0.1.0")
    _require(policy.get("status") == "design_and_advisory_only", "C0/C1 must remain design/advisory only")
    _require(policy.get("global_mastery_scalar") is False, "Study OS must not collapse learning into one mastery scalar")

    research_scope = policy.get("research_scope")
    _require(isinstance(research_scope, dict), "research_scope must be an object")
    _require(research_scope.get("gate") == "R0", "C0/C1 must not broaden the active research gate")
    _require(research_scope.get("domain") == "dsa", "active research domain must remain DSA")
    _require(research_scope.get("language") == "python", "active research language must remain Python")
    _require(
        research_scope.get("active_concept_family") == "sliding-window",
        "R0 active concept family must remain Sliding Window",
    )
    _require(
        research_scope.get("instantiated_supporting_curriculum_slices") == ["running-extrema"],
        "running-extrema must remain an explicitly supporting instantiated curriculum slice",
    )
    _require(
        research_scope.get("supporting_slices_do_not_expand_r0_claim") is True,
        "supporting curriculum slices must not silently expand the R0 research claim",
    )
    _require(research_scope.get("active_tracks") == ["ALG"], "only ALG may be active under the current research scope")
    _require(research_scope.get("additional_tracks_are_architecture_only") is True, "additional tracks must remain architecture-only")

    dimensions = policy.get("dimensions")
    _require(isinstance(dimensions, dict), "dimensions must be an object")
    _require(dimensions.get("track") == "competency_family", "track semantics drifted")
    _require(dimensions.get("proficiency_tier") == "repeated_cross_item_and_session_capability_gate", "proficiency semantics drifted")
    _require(dimensions.get("daily_study_goal") == "derived_revisable_evidence_collection_plan", "daily-goal semantics drifted")

    tracks = policy.get("tracks")
    _require(isinstance(tracks, list), "tracks must be a list")
    track_ids: list[str] = []
    for raw_track in tracks:
        _require(isinstance(raw_track, dict), "every track must be an object")
        track_id = raw_track.get("id")
        _require(isinstance(track_id, str) and track_id, "every track must have an id")
        _require(not re.fullmatch(r"T\d+", track_id), f"track id {track_id} collides with the legacy proficiency namespace")
        _require(track_id not in track_ids, f"duplicate track id {track_id}")
        track_ids.append(track_id)
        expected_status = "active_research_slice" if track_id == "ALG" else "planned_architecture"
        _require(raw_track.get("status") == expected_status, f"{track_id}: track activation status drifted")
        _require(_string_list(raw_track.get("scope"), f"{track_id} scope"), f"{track_id}: scope must not be empty")
    _require(set(track_ids) == EXPECTED_TRACKS, "track taxonomy must contain the exact reviewed C0 track set")

    proficiency = policy.get("dsa_proficiency")
    _require(isinstance(proficiency, dict), "dsa_proficiency must be an object")
    _require(proficiency.get("namespace") == "DSA", "DSA proficiency namespace must remain explicit")
    _require(proficiency.get("legacy_namespace") == "T", "legacy Issue #3 tier namespace must remain documented")
    _require(proficiency.get("legacy_spec_issue") == 3, "DSA legacy tier provenance must point to Issue #3")
    _require(proficiency.get("legacy_aliases_are_documentation_compatibility_only") is True, "legacy aliases must not become canonical identifiers")
    bands = proficiency.get("bands")
    _require(isinstance(bands, list), "dsa_proficiency.bands must be a list")
    band_ids: list[str] = []
    aliases: list[str] = []
    for raw_band in bands:
        _require(isinstance(raw_band, dict), "every DSA proficiency band must be an object")
        band_id = raw_band.get("id")
        alias = raw_band.get("legacy_alias")
        _require(isinstance(band_id, str) and band_id, "every DSA band needs an id")
        _require(isinstance(alias, str) and alias, f"{band_id}: legacy alias is required")
        band_ids.append(band_id)
        aliases.append(alias)
        _require(isinstance(raw_band.get("summary"), str) and raw_band["summary"], f"{band_id}: summary is required")
    _require(band_ids == EXPECTED_DSA_BANDS, "DSA proficiency bands must remain DSA0 through DSA6 in order")
    _require(aliases == EXPECTED_LEGACY_ALIASES, "legacy DSA aliases must remain a one-to-one T0 through T6 mapping")

    promotion = policy.get("promotion_policy")
    _require(isinstance(promotion, dict), "promotion_policy must be an object")
    _require(
        promotion.get("status") == "initial_configurable_policy_not_validated_population_threshold",
        "promotion threshold must remain explicitly provisional",
    )
    minimum_items = promotion.get("minimum_distinct_unseen_items")
    _require(isinstance(minimum_items, int) and not isinstance(minimum_items, bool) and minimum_items >= 2, "promotion requires multiple unseen items")
    _require(promotion.get("more_than_one_session_when_practical") is True, "cross-session evidence requirement drifted")
    _require(promotion.get("threshold_is_configurable") is True, "promotion threshold must remain configurable")
    _require(set(_string_list(promotion.get("independent_bands"), "independent_bands")) == EXPECTED_INDEPENDENT_BANDS, "independent DSA band set drifted")
    for field in (
        "independent_band_requires_unaided_evidence",
        "independent_band_requires_transfer_evidence",
        "independent_band_requires_delayed_evidence",
        "critical_capability_gate_overrides_average",
        "self_report_is_never_sufficient",
        "teaching_exposure_cannot_count_as_unseen",
        "ai_assisted_construction_cannot_be_recorded_as_unaided_manual_implementation",
    ):
        _require(promotion.get(field) is True, f"promotion invariant {field} must remain enabled")
    anti_cases = set(_string_list(promotion.get("anti_promotion_cases"), "anti_promotion_cases"))
    _require(REQUIRED_ANTI_PROMOTION_CASES <= anti_cases, "promotion policy is missing required negative cases")

    daily = policy.get("daily_evidence_goal")
    _require(isinstance(daily, dict), "daily_evidence_goal must be an object")
    _require(daily.get("status") == "advisory_derived_design_only", "daily goal must remain design-only in C0/C1")
    _require(daily.get("evidence_class") == "derived", "daily goal must be derived, not observed learner evidence")
    _require(daily.get("canonical_mastery_authority") is False, "daily goal may not own mastery state")
    _require(daily.get("adaptive_authority") == "shadow", "daily goal authority must remain shadow")
    _require(daily.get("runtime_implementation") == "deferred_until_C3", "daily planner runtime must remain deferred until C3")
    _require(daily.get("public_mcp_change_required_for_C0_C1") is False, "C0/C1 may not require a new MCP tool")
    _require(daily.get("time_budget_is_planning_constraint_only") is True, "time budget must remain a planning constraint")
    _require(daily.get("item_count_is_not_progress_evidence") is True, "item counts may not become progress evidence")
    _require(daily.get("time_spent_is_not_mastery_evidence") is True, "time spent may not become mastery evidence")
    _require(daily.get("self_report_is_not_mastery_evidence") is True, "self-report may not become mastery evidence")
    _require(daily.get("manual_and_ai_assisted_evidence_must_remain_distinguishable") is True, "manual and AI-assisted evidence must remain distinguishable")
    dependencies = set(_string_list(daily.get("C2_snapshot_dependencies"), "C2_snapshot_dependencies"))
    _require(REQUIRED_DAILY_DEPENDENCIES <= dependencies, "daily-goal C2 snapshot dependencies are incomplete")
    selection_order = _string_list(daily.get("selection_order"), "selection_order")
    _require(selection_order[0] == "due_retention", "due retention must be serviced before ordinary new-work selection")
    _require(selection_order[-2:] == ["checkpoint", "schedule_next_probe"], "daily loop must close with checkpoint/probe scheduling")

    roadmap = policy.get("roadmap")
    _require(isinstance(roadmap, dict), "roadmap must be an object")
    _require(list(roadmap) == [f"C{index}" for index in range(6)], "curriculum-control roadmap must remain C0 through C5")
    _require(policy.get("C0_C1_runtime_behavior_change") is False, "C0/C1 may not change runtime learner semantics")
    _require(policy.get("C0_C1_http_frontend_change") is False, "C0/C1 may not introduce HTTP/frontend behavior")
    _require(policy.get("C0_C1_adaptive_authority_change") is False, "C0/C1 may not change adaptive authority")


def check_curriculum_control_policy(path: Path = DEFAULT_POLICY) -> None:
    validate_policy(_load_json(path))


def main() -> int:
    check_curriculum_control_policy()
    print("Study OS curriculum control policy checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
