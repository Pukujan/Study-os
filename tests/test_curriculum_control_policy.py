from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from typing import Any

from tools.check_curriculum_control_policy import (
    CurriculumControlPolicyFailure,
    check_curriculum_control_policy,
    validate_policy,
)

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "contracts" / "curriculum-control-policy.v0.1.json"


def load_policy() -> dict[str, Any]:
    value = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("curriculum control policy must be a JSON object")
    return value


class CurriculumControlPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = load_policy()

    def assert_invalid(self, policy: dict[str, Any]) -> None:
        with self.assertRaises(CurriculumControlPolicyFailure):
            validate_policy(policy)

    def test_current_policy_is_consistent(self) -> None:
        check_curriculum_control_policy()

    def test_track_namespace_cannot_reuse_legacy_tier_ids(self) -> None:
        mutated = copy.deepcopy(self.policy)
        mutated["tracks"][0]["id"] = "T1"
        self.assert_invalid(mutated)

    def test_dsa_band_and_legacy_alias_mapping_is_exact(self) -> None:
        mutated = copy.deepcopy(self.policy)
        mutated["dsa_proficiency"]["bands"][2]["id"] = "DSA3"
        self.assert_invalid(mutated)

        mutated = copy.deepcopy(self.policy)
        mutated["dsa_proficiency"]["bands"][2]["legacy_alias"] = "T9"
        self.assert_invalid(mutated)

    def test_one_item_promotion_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.policy)
        mutated["promotion_policy"]["minimum_distinct_unseen_items"] = 1
        self.assert_invalid(mutated)

    def test_independent_band_cannot_drop_unaided_transfer_or_delayed_evidence(self) -> None:
        for field in (
            "independent_band_requires_unaided_evidence",
            "independent_band_requires_transfer_evidence",
            "independent_band_requires_delayed_evidence",
        ):
            mutated = copy.deepcopy(self.policy)
            mutated["promotion_policy"][field] = False
            self.assert_invalid(mutated)

    def test_average_or_self_report_cannot_override_critical_capability_gates(self) -> None:
        mutated = copy.deepcopy(self.policy)
        mutated["promotion_policy"]["critical_capability_gate_overrides_average"] = False
        self.assert_invalid(mutated)

        mutated = copy.deepcopy(self.policy)
        mutated["promotion_policy"]["self_report_is_never_sufficient"] = False
        self.assert_invalid(mutated)

    def test_ai_assisted_construction_cannot_be_relabelled_as_unaided_manual(self) -> None:
        mutated = copy.deepcopy(self.policy)
        mutated["promotion_policy"]["ai_assisted_construction_cannot_be_recorded_as_unaided_manual_implementation"] = False
        self.assert_invalid(mutated)

        mutated = copy.deepcopy(self.policy)
        mutated["daily_evidence_goal"]["manual_and_ai_assisted_evidence_must_remain_distinguishable"] = False
        self.assert_invalid(mutated)

    def test_daily_goal_cannot_become_observed_truth_or_live_authority_in_c0_c1(self) -> None:
        mutated = copy.deepcopy(self.policy)
        mutated["daily_evidence_goal"]["evidence_class"] = "observed"
        self.assert_invalid(mutated)

        mutated = copy.deepcopy(self.policy)
        mutated["daily_evidence_goal"]["canonical_mastery_authority"] = True
        self.assert_invalid(mutated)

        mutated = copy.deepcopy(self.policy)
        mutated["daily_evidence_goal"]["adaptive_authority"] = "live"
        self.assert_invalid(mutated)

    def test_c0_c1_cannot_enable_runtime_or_transport_changes(self) -> None:
        for field in (
            "C0_C1_runtime_behavior_change",
            "C0_C1_http_frontend_change",
            "C0_C1_adaptive_authority_change",
        ):
            mutated = copy.deepcopy(self.policy)
            mutated[field] = True
            self.assert_invalid(mutated)


if __name__ == "__main__":
    unittest.main()
