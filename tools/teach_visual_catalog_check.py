#!/usr/bin/env python3
"""Fail if any player lesson step lacks a step-visual-map entry (Refs #161)."""
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
LESSONS = ROOT / "src/study_os/web/player/lessons"
MAP = ROOT / "content/teach-visuals/step-visual-map.v1.json"
PROV = ROOT / "content/teach-visuals/provenance.v1.json"
def main() -> int:
    m = json.loads(MAP.read_text())
    keyed = {(e["lesson_id"], e["step_id"]): e for e in m["entries"]}
    missing = []
    queued = []
    for lesson in sorted(LESSONS.glob("*.json")):
        data = json.loads(lesson.read_text())
        lid = data.get("lesson_id") or lesson.stem.split(".")[0]
        for step in data.get("steps") or []:
            sid = step.get("step_id") or step.get("id")
            if not sid: continue
            e = keyed.get((lid, sid))
            if not e: missing.append(f"{lid}/{sid}")
            elif e.get("status") == "queued": queued.append(f"{lid}/{sid}")
    st = (json.loads(PROV.read_text()).get("stats") if PROV.exists() else {}) or {}
    print(f"mapped={len(keyed)} curated_assets={st.get('curated_assets')} research_files={st.get('research_files')}")
    if missing:
        print("MISSING:", *missing, sep="\n  ")
        return 2
    print("queued:", len(queued))
    print("OK: every lesson×step has a catalog row")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
