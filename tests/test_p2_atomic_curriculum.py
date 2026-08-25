import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os.adaptive.baseline import InstructionCandidate, propose_instruction_baseline  # noqa: E402
from study_os.adaptive.contracts import CapabilityState, LearnerSnapshot  # noqa: E402
from study_os.curriculum import CurriculumValidationError, load_curriculum_slice, validate_curriculum_pair  # noqa: E402


class AtomicCurriculumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.curriculum = load_curriculum_slice(ROOT, "domains/dsa/running-extrema")

    def test_all_versioned_curriculum_slices_validate(self):
        graph_paths = sorted((ROOT / "domains").glob("**/competencies.v*.json"))
        self.assertTrue(graph_paths)
        for graph_path in graph_paths:
            version = graph_path.name.removeprefix("competencies.v").removesuffix(".json")
            relative_dir = graph_path.parent.relative_to(ROOT).as_posix()
            with self.subTest(slice=relative_dir, version=version):
                load_curriculum_slice(ROOT, relative_dir, version=version)

    def test_real_slice_has_atomic_dag_and_multiple_task_modes(self):
        curriculum = self.curriculum
        self.assertEqual(curriculum.graph["graph_version"], "0.1.0")
        self.assertEqual(len(curriculum.competency_by_id), 8)
        self.assertGreaterEqual(len(curriculum.item_by_id), 10)
        modes = {item["task_mode"] for item in curriculum.item_by_id.values()}
        self.assertTrue(
            {"state_prediction", "code_trace", "verbal_explanation", "parsons_completion", "manual_code_blank", "debug_existing_code"}.issubset(modes)
        )
        self.assertIn("dsa.extrema.update_order", curriculum.competency_by_id)
        self.assertEqual(
            curriculum.competency_by_id["dsa.extrema.second_largest_implement"]["prerequisites"],
            ["dsa.extrema.update_order", "py.index_value.distinguish"],
        )

    def test_transfer_and_retention_public_fixtures_are_explicit_a0(self):
        special = [
            item
            for item in self.curriculum.item_by_id.values()
            if item["exposure_class"] in {"transfer_public_fixture", "retention_public_fixture"}
        ]
        self.assertGreaterEqual(len(special), 3)
        self.assertTrue(all(item["assistance_ceiling"] == "A0" for item in special))

    def test_unknown_prerequisite_is_rejected(self):
        graph = copy.deepcopy(self.curriculum.graph)
        bank = copy.deepcopy(self.curriculum.item_bank)
        graph["competencies"][0]["prerequisites"] = ["missing.competency"]
        with self.assertRaisesRegex(CurriculumValidationError, "unknown prerequisite"):
            validate_curriculum_pair(graph, bank)

    def test_cycle_is_rejected(self):
        graph = copy.deepcopy(self.curriculum.graph)
        bank = copy.deepcopy(self.curriculum.item_bank)
        graph["competencies"][0]["prerequisites"] = ["dsa.extrema.running_max"]
        with self.assertRaisesRegex(CurriculumValidationError, "cycle"):
            validate_curriculum_pair(graph, bank)

    def test_unknown_item_competency_is_rejected(self):
        graph = copy.deepcopy(self.curriculum.graph)
        bank = copy.deepcopy(self.curriculum.item_bank)
        bank["items"][0]["competency_ids"].append("missing.competency")
        with self.assertRaisesRegex(CurriculumValidationError, "unknown competencies"):
            validate_curriculum_pair(graph, bank)

    def test_real_items_can_feed_instruction_baseline_without_transcript_state(self):
        capabilities = {
            competency_id: CapabilityState(status="pass_unaided", evidence_ids=(f"ev-{index}",))
            for index, competency_id in enumerate(
                [
                    "dsa.compare.values",
                    "dsa.extrema.running_max",
                    "dsa.state.predict_transition",
                    "dsa.extrema.two_candidates",
                    "dsa.invariant.two_largest_order",
                    "py.index_value.distinguish",
                ],
                start=1,
            )
        }
        capabilities["dsa.extrema.update_order"] = CapabilityState(status="fail", evidence_ids=("ev-fail",))
        capabilities["dsa.extrema.second_largest_implement"] = CapabilityState(status="not_tested", evidence_ids=())
        snapshot = LearnerSnapshot(
            subject_id="subject-fixture",
            checkpoint_id="checkpoint-fixture",
            phase="instruction",
            current_focus="running extrema update ordering",
            capabilities=capabilities,
            recent_exposures=("re.update-order.001",),
            active_goal_ids=("goal.second-largest-independent",),
            interaction_constraints={"device": "any"},
        )
        candidates = []
        for item in self.curriculum.item_by_id.values():
            if item["exposure_class"] not in {"practice", "diagnostic"}:
                continue
            primary = self.curriculum.competency_by_id[item["primary_competency_id"]]
            candidates.append(
                InstructionCandidate(
                    candidate_id=item["id"],
                    competency_id=item["primary_competency_id"],
                    prerequisites=tuple(primary["prerequisites"]),
                    goal_relevance=1.0,
                    action_type=item["task_mode"],
                    assistance_target=item["assistance_ceiling"],
                    representation_id=item["representation_families"][0],
                    learning_operation=item["learning_operation"],
                )
            )
        proposal = propose_instruction_baseline(snapshot, candidates)
        self.assertIsNotNone(proposal.selected)
        self.assertEqual(proposal.selected.candidate_id, "re.update-order.002")
        excluded = {exclusion.candidate_id: exclusion.reason_code for exclusion in proposal.exclusions}
        self.assertEqual(excluded["re.implement.001"], "prerequisite_not_met")


if __name__ == "__main__":
    unittest.main()
