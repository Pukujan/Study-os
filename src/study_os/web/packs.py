"""Subject packs compiled into PIR teaching assets (#91, D018).

Each HESI topic compiles into a ``CanonicalTeachingAsset`` that follows the same golden
teaching pattern as the SOS-0002 sliding-window lesson: intro → probe → why (correct) or
fix with the answer marked and reassurance (incorrect) → retry on a *different* item →
one more check → exit ``assembled_mastery_unproven``. The same deterministic PIR controller
serves it, and ``study_os.pir.conformance.evaluate_asset`` checks it against a per-topic
oracle. Compiled assets are cached in process memory.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from typing import Any

from study_os.pir.conformance import (
    ConceptRepresentationRule,
    ConformanceReport,
    GoldenBridge,
    GoldenOracle,
    GoldenSource,
    evaluate_asset,
)
from study_os.pir.contracts import (
    AssessmentKind,
    AssessmentSpec,
    CanonicalTeachingAsset,
    ExpansionKind,
    ExpansionSpec,
    LearnerOutcome,
    RepresentationSpec,
    ResponseKind,
    RunStatus,
    StepKind,
    TeachingStep,
    TransitionSpec,
)
from study_os.pir.controller import validate_asset

PACK_FILE = "hesi_a2_pack.v0.json"
BLUEPRINT_FILE = "hesi_blueprint.v0.json"
PACK_CONTROLLER_REVISION = "study-os.pir-controller.v0"
PACK_RENDERER_REVISION = "study-os.pack-renderer.v1"
PACK_ASSESSMENT_REVISION = "study-os.pack-mcq-assessment.v1"
# Mirrors the sliding-window oracle's mastery rules (P-CTL-2).
MASTERY_PATTERNS = (
    r"\bmaster",
    r"\byou(?:'ve|’ve| have)? (?:now )?(?:learned|mastered|know)\b",
    r"\bfully understand",
    r"completed_validated",
    r"\bproficien",
)
# Subject vocabulary that contains a mastery-pattern substring but claims nothing about the learner.
MASTERY_ALLOWED_PHRASES = ("master gland", "Master gland", "Independent mastery remains unproven")
PACK_SOURCE_COMMIT = "0" * 40  # packs are repository-owned; no external PIR commit
MIN_TEACH_ITEMS = 3


@dataclass(frozen=True)
class PackItem:
    item_id: str
    topic_id: str
    role: str
    stem: str
    options: tuple[str, ...]
    correct_index: int
    rationale: str
    distractor_rationales: tuple[str, ...]
    misconception_tags: tuple[str, ...]
    source_id: str
    review_status: str
    review_flags: tuple[str, ...]

    @property
    def servable(self) -> bool:
        return not self.review_flags


def _content_root() -> Any:
    return files("study_os.web").joinpath("content")


@lru_cache(maxsize=1)
def load_blueprint() -> dict[str, Any]:
    return json.loads(_content_root().joinpath(BLUEPRINT_FILE).read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def pack_bytes() -> bytes:
    return _content_root().joinpath(PACK_FILE).read_bytes()


@lru_cache(maxsize=1)
def load_pack() -> dict[str, Any]:
    return json.loads(pack_bytes().decode("utf-8"))


def pack_sha256() -> str:
    return hashlib.sha256(pack_bytes()).hexdigest()


def pack_revision() -> str:
    return str(load_pack()["pack_revision"])


def _mastery_hit(text: str) -> bool:
    for phrase in MASTERY_ALLOWED_PHRASES:
        text = text.replace(phrase, "")
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in MASTERY_PATTERNS)


@lru_cache(maxsize=1)
def items_by_id() -> dict[str, PackItem]:
    out: dict[str, PackItem] = {}
    for topic_id, topic in load_pack()["topics"].items():
        for raw in topic["items"]:
            flags = list(raw.get("review_flags", []))
            text = " ".join([raw["stem"], raw["rationale"], *raw["options"]])
            if _mastery_hit(text):
                flags.append("mastery_language")
            item = PackItem(
                item_id=raw["item_id"],
                topic_id=topic_id,
                role=raw["role"],
                stem=raw["stem"],
                options=tuple(raw["options"]),
                correct_index=int(raw["correct_index"]),
                rationale=raw["rationale"],
                distractor_rationales=tuple(raw.get("distractor_rationales", [])),
                misconception_tags=tuple(raw.get("misconception_tags", [])),
                source_id=raw["source_id"],
                review_status=raw.get("review_status", "unreviewed"),
                review_flags=tuple(flags),
            )
            out[item.item_id] = item
    return out


def topic_items(topic_id: str, role: str | None = None, servable_only: bool = True) -> list[PackItem]:
    return [
        item
        for item in items_by_id().values()
        if item.topic_id == topic_id
        and (role is None or item.role == role)
        and (item.servable or not servable_only)
    ]


def topic_graph() -> list[dict[str, Any]]:
    """Sections with topics, prerequisites, and item availability for the home screen."""

    pack_topics = load_pack()["topics"]
    sections = []
    for section in load_blueprint()["sections"]:
        topics = []
        for topic in section["topics"]:
            tid = topic["topic_id"]
            teach = topic_items(tid, "teach")
            topics.append(
                {
                    "topic_id": tid,
                    "title": topic["title"],
                    "prerequisites": topic["prerequisites"],
                    "available": tid in pack_topics and len(teach) >= MIN_TEACH_ITEMS,
                    "items": len(topic_items(tid)),
                }
            )
        sections.append(
            {
                "section_id": section["section_id"],
                "exam_id": section["exam_id"],
                "title": section["title"],
                "topics": topics,
                "checkpoint_items": sum(len(topic_items(t["topic_id"], "check")) for t in topics),
            }
        )
    return sections


def _choices_md(item: PackItem) -> str:
    return "\n".join(f"{index + 1}. {option}" for index, option in enumerate(item.options))


def probe_markdown(item: PackItem) -> str:
    return f"{item.stem}\n\n{_choices_md(item)}"


def why_markdown(item: PackItem) -> str:
    n = item.correct_index + 1
    return (
        f"{probe_markdown(item)}\n\n"
        f"Yes: **{n}. {item.options[item.correct_index]}**\n\n**Why:** {item.rationale}"
    )


def fix_markdown(item: PackItem) -> str:
    n = item.correct_index + 1
    return (
        f"{probe_markdown(item)}\n\n"
        f"The right answer is **{n}. {item.options[item.correct_index]}**.\n\n"
        f"**Why:** {item.rationale}\n\nIt’s okay. Let’s try a different one."
    )


def intro_markdown(topic_id: str) -> str:
    topic = load_pack()["topics"][topic_id]
    title = topic.get("title", topic_id)
    points = "\n".join(f"- {point}" for point in topic.get("key_points", []))
    body = topic["intro_markdown"].replace("?", ".")
    return f"### {title}\n\n{body}\n\n**Key points**\n\n{points}".strip()


def _topic_title(topic_id: str) -> str:
    for section in load_blueprint()["sections"]:
        for topic in section["topics"]:
            if topic["topic_id"] == topic_id:
                return topic["title"]
    return topic_id


def asset_id_for_topic(topic_id: str) -> str:
    return f"hesi.{topic_id}.{pack_revision()}"


@lru_cache(maxsize=128)
def compile_topic(topic_id: str) -> CanonicalTeachingAsset:
    teach = topic_items(topic_id, "teach")
    if len(teach) < MIN_TEACH_ITEMS:
        raise KeyError(f"topic {topic_id} has fewer than {MIN_TEACH_ITEMS} servable items")
    t = topic_id
    rel = f"relation:{t}"
    representations: list[RepresentationSpec] = [
        RepresentationSpec(
            representation_id=f"r.{t}.intro",
            learner_visible_markdown=intro_markdown(t),
            visible_components=("key_points", rel),
        )
    ]
    assessments: list[AssessmentSpec] = []
    steps: list[TeachingStep] = [
        TeachingStep(
            step_id=f"{t}.intro",
            kind=StepKind.EXPLAIN,
            representation_id=f"r.{t}.intro",
            required_components=("key_points", rel),
            automatic_transition=TransitionSpec(next_step_id=f"{t}.e0.n2"),
        )
    ]
    expansions: list[ExpansionSpec] = []
    n = len(teach)
    for j, item in enumerate(teach):
        nxt = (j + 1) % n
        probe_rep = f"r.{t}.e{j}.probe"
        representations += [
            RepresentationSpec(
                representation_id=probe_rep,
                learner_visible_markdown=probe_markdown(item),
                visible_components=("question", "choices", rel),
            ),
            RepresentationSpec(
                representation_id=f"r.{t}.e{j}.why",
                learner_visible_markdown=why_markdown(item),
                visible_components=("question", "choices", "why_text", rel),
            ),
            RepresentationSpec(
                representation_id=f"r.{t}.e{j}.fix",
                learner_visible_markdown=fix_markdown(item),
                visible_components=("question", "choices", "why_text", "answer_marked", "reassurance", rel),
            ),
        ]
        assessment_id = f"a.{t}.{item.item_id}"
        assessments.append(
            AssessmentSpec(
                assessment_id=assessment_id,
                kind=AssessmentKind.INTEGER,
                expected_values=(item.correct_index + 1,),
            )
        )
        for need, correct_next in (("n2", TransitionSpec(next_step_id=f"{t}.e{nxt}.n1")),
                                   ("n1", TransitionSpec(exit_status=RunStatus.ASSEMBLED_MASTERY_UNPROVEN))):
            sid = f"{t}.e{j}.{need}"
            steps += [
                TeachingStep(
                    step_id=sid,
                    kind=StepKind.PROBE,
                    representation_id=probe_rep,
                    required_components=("question", "choices"),
                    forbidden_components=("answer_marked", "why_text"),
                    response_kind=ResponseKind.INTEGER,
                    assessment_id=assessment_id,
                    outcome_transitions=(
                        TransitionSpec(outcome=LearnerOutcome.CORRECT, next_step_id=f"{sid}.why"),
                        TransitionSpec(outcome=LearnerOutcome.INCORRECT, next_step_id=f"{sid}.fix"),
                    ),
                ),
                TeachingStep(
                    step_id=f"{sid}.why",
                    kind=StepKind.EXPLAIN,
                    representation_id=f"r.{t}.e{j}.why",
                    automatic_transition=correct_next,
                ),
                TeachingStep(
                    step_id=f"{sid}.fix",
                    kind=StepKind.CORRECT,
                    representation_id=f"r.{t}.e{j}.fix",
                    automatic_transition=TransitionSpec(next_step_id=f"{t}.e{nxt}.n2"),
                ),
            ]
            expansions.append(
                ExpansionSpec(step_id=sid, kind=ExpansionKind.REPEAT_REPRESENTATION, representation_id=f"r.{t}.intro")
            )
    asset = CanonicalTeachingAsset(
        schema_version="study-os.canonical-teaching-asset.v0",
        canonical_problem_id=asset_id_for_topic(t),
        canonical_pir_revision=f"{pack_revision()}:{pack_sha256()[:12]}:{t}",
        source_pir_repository="Pukujan/Study-os (subject pack)",
        source_pir_commit=PACK_SOURCE_COMMIT,
        controller_revision=PACK_CONTROLLER_REVISION,
        renderer_revision=PACK_RENDERER_REVISION,
        assessment_revision=PACK_ASSESSMENT_REVISION,
        entry_step_id=f"{t}.intro",
        aliases=(_topic_title(t),),
        representations=tuple(representations),
        steps=tuple(steps),
        assessments=tuple(assessments),
        expansions=tuple(expansions),
    )
    violations = validate_asset(asset)
    if violations:
        raise RuntimeError(f"compiled topic {t} invalid: {[v.code.value for v in violations]}")
    return asset


def topic_oracle(topic_id: str) -> GoldenOracle:
    return GoldenOracle(
        schema_version="study-os.pir-golden-oracle.v0",
        canonical_problem_id=asset_id_for_topic(topic_id),
        benchmarker_repository="Pukujan/study-os-benchmarker",
        benchmarker_commit="d438988fda12e9df902caabbcb6a639834452d5d",
        golden_sources=(
            GoldenSource(path=f"src/study_os/web/content/{PACK_FILE}", sha256=pack_sha256()),
        ),
        required_bridges=(GoldenBridge(concept_id=topic_id, golden_step=f"{topic_id} intro"),),
        max_new_concepts_per_step=1,
        feedback_required=("why_text",),
        fix_required=("answer_marked", "reassurance"),
        representation_rules=(
            ConceptRepresentationRule(
                concept_id=topic_id,
                probe_required=("question", "choices"),
                probe_forbidden=("answer_marked", "why_text"),
            ),
        ),
        mastery_patterns=MASTERY_PATTERNS,
        mastery_allowed_phrases=MASTERY_ALLOWED_PHRASES,
        allowed_exit_statuses=(RunStatus.ASSEMBLED_MASTERY_UNPROVEN,),
    )


def evaluate_topic(topic_id: str) -> ConformanceReport:
    return evaluate_asset(topic_oracle(topic_id), compile_topic(topic_id))


def item_for_assessment(assessment_id: str) -> PackItem | None:
    item_id = assessment_id.rsplit(".", 1)[-1]
    return items_by_id().get(item_id)
