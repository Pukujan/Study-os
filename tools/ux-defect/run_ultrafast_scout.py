# -*- coding: utf-8 -*-
"""Thin Study-os LOCAL guest Ultrafast scout (FE claim gate; not a CI job).

Writes ux-defect-report.v1 summary.json. P0/P1 fails regardless of confidence.
OpenRouter Decisions misconfig is env/config — not an Ultrafast flake.
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get("JEV_ULTRAFAST_ROOT", r"D:\claude\jev-ultrafast")).resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jev_ultrafast import Agent  # noqa: E402
import jev_ultrafast.questions as questions  # noqa: E402

BASE = (os.environ.get("BASE_URL") or os.environ.get("E2E_BASE_URL") or "https://study.design-bakery.com").rstrip("/")
ART = Path(os.environ.get("ART_DIR") or Path.cwd() / "artifacts" / "ux-defect-ultrafast" / "adhoc")
MAX_ACTIONS = int(os.environ.get("MAX_ACTIONS") or "40")
RUN_ID = os.environ.get("RUN_ID") or ART.name

ART.mkdir(parents=True, exist_ok=True)
(ART / "screenshots").mkdir(exist_ok=True)
DECISIONS = ART / "decisions.jsonl"
ACTIONS = ART / "actions.jsonl"
DECISIONS.write_text("", encoding="utf-8")
ACTIONS.write_text("", encoding="utf-8")

questions.MAX_STEPS = max(MAX_ACTIONS, 20)

STARTED = datetime.now(timezone.utc)
T0 = time.perf_counter()
DEFECTS: list[dict] = []
BUTTONS: list[str] = []
PAGES: set[str] = set()
SEEN_HIST = 0


def utc_iso(dt: datetime | None = None) -> str:
    d = dt or datetime.now(timezone.utc)
    return d.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def jlog(path: Path, obj: dict) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, default=str, ensure_ascii=False) + "\n")


def classify_noop(label: str) -> str:
    low = (label or "").lower()
    if any(
        k in low
        for k in (
            "explain again",
            "worked example",
            "resume",
            "start",
            "try",
            "continue",
            "back",
            "exit",
            "home",
            "submit",
            "send",
        )
    ):
        return "P0"
    if any(
        k in low
        for k in (
            "mic",
            "speaker",
            "sound",
            "voice",
            "audio",
            "read aloud",
            "chat",
            "message",
            "assistant",
            "chip",
        )
    ):
        return "P1"
    return "P1"


def component_for(title: str, control: str) -> tuple[str, str | None]:
    blob = f"{title} {control}".lower()
    if "worked example" in blob:
        return "worked-example", "A12"
    if any(k in blob for k in ("read aloud", "voice", "mic", "speaker")):
        return "mic-speaker", "A14"
    if any(k in blob for k in ("chat", "message", "send", "assistant")):
        return "study-buddy-chat", "A13"
    if any(k in blob for k in ("back", "exit", "home")):
        return "back-exit", "A20"
    if "explain again" in blob:
        return "explain-again", "A12"
    return "player-shell", None


def add_defect(severity: str, title: str, expected: str, actual: str, url: str, control: str, repro: list[str]) -> None:
    component, slice_id = component_for(title, control)
    d: dict = {
        "id": f"UX-JEV-{len(DEFECTS) + 1:03d}",
        "severity": severity,
        "component": component,
        "control_label": control or title,
        "url": url or BASE,
        "expected": expected,
        "actual": actual,
        "repro_steps": repro or [f"Open {BASE}", f"Activate {control or title}"],
        "evidence": {},
        "source": "jev",
    }
    if slice_id:
        d["related_issue_slice"] = slice_id
    DEFECTS.append(d)


GOAL = (
    "Guest UX defect scout of Study OS (fractions-first). Guest only: do not book, pay, or use admin. "
    f"Open {BASE}/ . Prefer Comparing fractions / HESI fractions (Try it or Try on that lesson). "
    "Once in /play: click Explain again; click Worked example and confirm the surface changes; "
    "open study assistant / Ask the tutor; try companion chips; fill Message and Send once; "
    "toggle Read aloud / Voice input if visible; then leave via Home / brand / Back / exit. "
    "Prefer unused controls. If a control does nothing visible in ~3s, note it and try another. "
    "DONE when major in-lesson controls tried or blocked."
)


def ingest_state(state: dict) -> None:
    global SEEN_HIST
    page = state.get("page") or {}
    url = page.get("url") if isinstance(page, dict) else None
    if isinstance(url, str) and url:
        PAGES.add(url)

    decisions = state.get("decisions") or []
    if decisions and isinstance(decisions[-1], dict):
        # Rewrite file from scratch would duplicate; append only new by counting lines cheaply.
        pass
    # Append latest decision if new
    if decisions:
        # Keep full stream: truncate+rewrite is simpler and small
        DECISIONS.write_text(
            "\n".join(json.dumps(d, default=str, ensure_ascii=False) for d in decisions if isinstance(d, dict)) + ("\n" if decisions else ""),
            encoding="utf-8",
        )

    history = state.get("history") or []
    if len(history) > SEEN_HIST:
        for entry in history[SEEN_HIST:]:
            if not isinstance(entry, dict):
                continue
            jlog(ACTIONS, entry)
            label = str(entry.get("action") or "")
            if label:
                BUTTONS.append(label)
            kind = str(entry.get("kind") or "")
            page_changed = entry.get("page_changed")
            entry_url = str(url or BASE)
            if page_changed is False and kind != "wait" and label and not any(
                k in label.lower() for k in ("wait", "scroll", "done", "blocked")
            ):
                add_defect(
                    classify_noop(label),
                    f"Dead/no-op control: {label}",
                    "Visible change (URL, DOM text, panel) within ~3s",
                    "No page_changed after action",
                    entry_url,
                    label,
                    [f"Open {entry_url}", f"Activate '{label}'", "Wait ~3s"],
                )
        SEEN_HIST = len(history)


def main() -> int:
    print(f"Ultrafast scout BASE={BASE} ART={ART} MAX_ACTIONS={MAX_ACTIONS} ROOT={ROOT}")
    ticks = 0
    try:
        with Agent(f"{BASE}/", GOAL, record_dir=str(ART / "record"), screenshots=False) as agent:
            for snap in agent.run():
                ticks += 1
                state = agent.state
                ingest_state(state)
                status = str(state.get("status") or "")
                if status in {"done", "blocked"}:
                    break
                if len(state.get("history") or []) >= MAX_ACTIONS:
                    break
                if ticks >= MAX_ACTIONS * 2:
                    break
                # snap unused except as generator pump
                _ = snap
    except Exception as exc:  # noqa: BLE001
        traceback.print_exc()
        add_defect(
            "P0",
            "Ultrafast scout crashed",
            "Scout completes without uncaught exception",
            f"{type(exc).__name__}: {exc}",
            BASE,
            "scout",
            [f"Run tools/ux-defect/Run-UltrafastScout.ps1 against {BASE}"],
        )

    finished = datetime.now(timezone.utc)
    controls = max(SEEN_HIST, len(BUTTONS), ticks)
    p0p1 = [d for d in DEFECTS if d["severity"] in ("P0", "P1")]
    summary = {
        "schema_version": "ux-defect-report.v1",
        "run_id": RUN_ID,
        "source": "jev",
        "started_at": utc_iso(STARTED),
        "finished_at": utc_iso(finished),
        "base_url": BASE,
        "agent": {
            "name": "jev-ultrafast",
            "model": "typesafe/jev-1.13",
            "harness_version": "study-os-scout-1",
        },
        "controls_exercised": controls,
        "pass": len(p0p1) == 0,
        "catch_rate": (len(DEFECTS) / controls) if controls else 0.0,
        "artifacts": {
            "actions_jsonl": "actions.jsonl",
            "decisions_jsonl": "decisions.jsonl",
            "report_md": "report.md",
            "screenshots_dir": "screenshots",
        },
        "defects": DEFECTS,
    }
    (ART / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (ART / "summary.detail.json").write_text(
        json.dumps(
            {
                "duration_s": round(time.perf_counter() - T0, 2),
                "pages_visited": sorted(PAGES),
                "buttons_clicked": BUTTONS,
                "ticks": ticks,
                "history_len": SEEN_HIST,
                "defect_count": len(DEFECTS),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    md = [
        "# Study OS Ultrafast UX defect scout",
        "",
        f"- Base URL: {BASE}",
        f"- Finished: {summary['finished_at']}",
        f"- Controls exercised: {summary['controls_exercised']}",
        f"- Defects: **{len(DEFECTS)}** (P0/P1 gate fails: {len(p0p1)})",
        f"- Pass: {summary['pass']}",
        "",
        "## Defects",
    ]
    if not DEFECTS:
        md.append("_None_")
    for d in DEFECTS:
        md.append(f"### {d['id']} [{d['severity']}] {d['control_label']}")
        md.append(f"- Expected: {d['expected']}")
        md.append(f"- Actual: {d['actual']}")
        md.append(f"- URL: {d['url']}")
        md.append("")
    (ART / "report.md").write_text("\n".join(md), encoding="utf-8")
    print(
        json.dumps(
            {
                "pass": summary["pass"],
                "defects": len(DEFECTS),
                "controls": summary["controls_exercised"],
                "art": str(ART),
            },
            indent=2,
        )
    )
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
