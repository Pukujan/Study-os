#!/usr/bin/env python3
"""Build src/study_os/web/content/hesi_a2_pack.v0.json from generated topic files.

Input: a directory of per-topic JSON files written by the draft generator (original items
from cb/glm-5.3, independent review by cb/deepseek-v4.1-flash, optional adjudication).
Everything is marked ``review_status: unreviewed`` until the owner reviews it. Items with
open review flags stay in the pack for review but are not served.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "src/study_os/web/content"


def _learner_neutral(text: str) -> str:
    """Remove phrasing the mastery detector treats as a claim about the learner (P-CTL-2)."""

    text = re.sub(r"\b[Oo]nce you know\b", "Once you recognize", text)
    text = re.sub(r"\byou(?:'ve|’ve| have) (?:now )?learned\b", "you have seen", text)
    return re.sub(r"\byou know\b", "you recognize", text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gen_dir", type=Path)
    parser.add_argument("--revision", default="hesi-a2-pack.v0.1")
    args = parser.parse_args()
    blueprint = json.loads((CONTENT / "hesi_blueprint.v0.json").read_text(encoding="utf-8"))
    titles = {t["topic_id"]: t["title"] for s in blueprint["sections"] for t in s["topics"]}
    topics: dict[str, dict] = {}
    for path in sorted(args.gen_dir.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        tid = raw["topic_id"]
        if tid not in titles:
            continue
        items = []
        for index, it in enumerate(raw["items"]):
            review = it.get("llm_review", {})
            flags = list(review.get("flags", []))
            adj = it.get("adjudication")
            if adj and adj.get("agrees_with_key") and "key_disagreement" in flags:
                flags.remove("key_disagreement")
            if len(it.get("options", [])) != 4 or not (0 <= int(it.get("correct_index", -1)) <= 3):
                flags.append("malformed")
            items.append({
                "item_id": f"{tid}-{index + 1:02d}",
                "role": "teach" if index < 6 else "check",
                "stem": it["stem"].strip(),
                "options": [o.strip() for o in it["options"]],
                "correct_index": int(it["correct_index"]),
                "rationale": it["rationale"].strip(),
                "distractor_rationales": it.get("distractor_rationales", []),
                "misconception_tags": [t for t in it.get("misconception_tags", []) if re.fullmatch(r"[a-z0-9_]{3,60}", t)],
                "source_id": it.get("source_id", "original"),
                "review_status": "unreviewed",
                "review_flags": sorted(set(flags)),
                "llm_review": {k: review.get(k) for k in ("model", "best_index", "factually_accurate", "single_best_answer", "distractor_quality", "issues")},
                **({"adjudication": adj} if adj else {}),
            })
        topics[tid] = {
            "title": titles[tid],
            "intro_markdown": _learner_neutral(raw["intro_markdown"].strip()),
            "key_points": raw.get("key_points", []),
            "generator_model": raw.get("generator_model"),
            "review_status": "unreviewed",
            "items": items,
        }
    pack = {
        "schema_version": "study-os.subject-pack.v0",
        "pack_revision": args.revision,
        "subject": "hesi",
        "review_status": "unreviewed",
        "provenance": "Original items and intros drafted with cb/glm-5.3 via InferHub (2026-09-24), independently reviewed by cb/deepseek-v4.1-flash; disagreements adjudicated by a second cb/glm-5.3 solve. No commercial prep content was used. Unreviewed by a human.",
        "sources": blueprint["sources"],
        "topics": topics,
    }
    out = CONTENT / "hesi_a2_pack.v0.json"
    out.write_text(json.dumps(pack, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    n = sum(len(t["items"]) for t in topics.values())
    served = sum(1 for t in topics.values() for i in t["items"] if not i["review_flags"])
    print(json.dumps({"topics": len(topics), "items": n, "servable": served}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
