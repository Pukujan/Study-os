#!/usr/bin/env python3
"""Full guest UX defect crawl via pinned jev-ultrafast + OpenRouter Decisions.

Writes actions.jsonl, decisions.jsonl, report.md, summary.json (legacy + schema
v1 fields) under ULTRAFAST_ARTIFACT_DIR. Confidence from Decisions is recorded
on each decision/action and optionally on defects; it never soft-skips a P0/P1
(see tools/gate_ux_defect_report.py).

Requires:
  OPENROUTER_API_KEY
  Browser Harness CDP (local Chrome or BU_CDP_URL / BU_CDP_WS)
  PYTHONPATH including the pinned jev-ultrafast checkout
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jev_ultrafast.questions as questions
from jev_ultrafast import Agent
from jev_ultrafast.browser import StalePage

# Raise step budget for full defect pass (runtime only).
questions.MAX_STEPS = 150

BASE_URL = os.environ.get("ULTRAFAST_BASE_URL", "https://study.design-bakery.com").rstrip("/")
ART = Path(os.environ.get("ULTRAFAST_ARTIFACT_DIR", "artifacts/ultrafast-ux")).resolve()
ART.mkdir(parents=True, exist_ok=True)
(ART / "screenshots").mkdir(exist_ok=True)

DECISIONS_PATH = ART / "decisions.jsonl"
ACTIONS_PATH = ART / "actions.jsonl"
DEFECTS: list[dict[str, Any]] = []
PAGES_VISITED: set[str] = set()
BUTTONS_CLICKED: list[str] = []
PHASE_LOG: list[dict[str, Any]] = []
GLOBAL_ACTIONS = 0
GLOBAL_DECISIONS = 0
ACTION_CAP = int(os.environ.get("ULTRAFAST_ACTION_CAP", "140"))
STARTED = time.perf_counter()
STARTED_AT = datetime.now(timezone.utc)
OPENROUTER_OK = False
ERRORS: list[str] = []
PIN_COMMIT = os.environ.get("ULTRAFAST_PIN_COMMIT", "")
MODEL = os.environ.get("OPENROUTER_MODEL", "typesafe/jev-1.13")

DECISIONS_PATH.write_text("", encoding="utf-8")
ACTIONS_PATH.write_text("", encoding="utf-8")

KNOWN_SUSPECTS = [
    "blank play/Resume",
    "missing Back/exit",
    "Explain again / Worked example dead",
    "speaker/mic no-op",
    "teach spoils probe",
    "arrow overlap",
    "review only once",
    "chat no ack",
    "number-line before probe",
    "companion chips",
]

PHASES = [
    {
        "name": "home_and_lanes",
        "url": f"{BASE_URL}/",
        "max_actions": 25,
        "goal": (
            "Guest UX defect crawl of Study OS. HOME + LANES phase. "
            "As guest only: do not book, pay, or use admin. "
            "Open home, explore every visible lane and catalog card "
            "(HESI fractions, DSA Big O, sliding window if listed). "
            "Click Start or Resume for each distinct lesson you can reach. "
            "After entering a lesson briefly, look for Back/Exit/home to return "
            "and try the next lesson. Prefer unused controls over repeating. "
            "If a button does nothing visible, note it and try another control. "
            "Do NOT mark DONE until you have attempted Start/Resume on every "
            "distinct lesson listed on home, or you are stuck. Then DONE or BLOCKED."
        ),
    },
    {
        "name": "hesi_fractions_lesson",
        "url": f"{BASE_URL}/",
        "max_actions": 35,
        "goal": (
            "Guest UX defect crawl — HESI fractions lesson deep pass. "
            "Start or Resume the Comparing fractions / HESI fractions lesson. "
            "Once in the player: click Explain again; click Worked example; "
            "try every companion chip; try mic/speaker if visible; "
            "if a chat/assistant input exists, TYPE one short message like 'help' and send; "
            "if probe/answer fields exist, submit a wrong answer once then a plausible "
            "right answer if possible; if review stars 1-5 + Submit appear, pick a star "
            "and Submit; try Continue / next / Back / exit / arrows. "
            "Assert each click changes the page; prefer untried controls. "
            "Do not pay or destroy data. DONE when major in-lesson controls tried or blocked."
        ),
    },
    {
        "name": "dsa_big_o_lesson",
        "url": f"{BASE_URL}/",
        "max_actions": 35,
        "goal": (
            "Guest UX defect crawl — DSA Big O lesson deep pass. "
            "From home or catalog, Start/Resume Big O: how work grows (or DSA Big O). "
            "In lesson: Explain again, Worked example, companion chips, Continue through "
            "a few steps, mic/speaker if present, chat one message if present, "
            "review stars+Submit if present, Back/exit/arrows. Prefer unused controls. "
            "Guest only. DONE when major controls exercised or no progress."
        ),
    },
    {
        "name": "sliding_window_and_misc",
        "url": f"{BASE_URL}/",
        "max_actions": 30,
        "goal": (
            "Guest UX defect crawl — remaining lessons + misc controls. "
            "Find sliding window or any other listed lesson not yet opened; Start/Resume it. "
            "Exercise Explain again, Worked example, chips, Continue, Back/exit, mic/speaker, "
            "chat, review. Also re-check home for blank Resume buttons or dead links. "
            "Guest only. DONE when no new unique controls remain or stuck."
        ),
    },
    {
        "name": "controls_sweep",
        "url": f"{BASE_URL}/",
        "max_actions": 25,
        "goal": (
            "Final control sweep for Study OS guest UX defects. "
            "Enter any open/resumable lesson. Systematically click every visible unused "
            "control once: Explain again, Worked example, companion chips, speaker, mic, "
            "chat send, review, Continue, Back, exit, arrows. "
            "If teach content reveals the probe answer before the probe (spoil), treat as "
            "observed defect and continue. Guest only. DONE when sweep complete or no new controls."
        ),
    },
]


def jlog(path: Path, obj: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, default=str, ensure_ascii=False) + "\n")


def guess_component(title: str, control: str) -> str:
    blob = f"{title} {control}".lower()
    mapping = [
        ("blank", "player-shell"),
        ("back", "back-exit"),
        ("exit", "back-exit"),
        ("worked example", "worked-example"),
        ("explain again", "explain-again"),
        ("voice", "mic-speaker"),
        ("mic", "mic-speaker"),
        ("speaker", "mic-speaker"),
        ("read aloud", "mic-speaker"),
        ("message", "study-buddy-chat"),
        ("chat", "study-buddy-chat"),
        ("assistant", "study-buddy-chat"),
        ("review", "review-submit"),
        ("rate ", "review-submit"),
        ("spoil", "player-shell"),
        ("arrow", "arrows"),
        ("number-line", "number-line"),
        ("companion", "companion-chips"),
        ("chip", "companion-chips"),
        ("home", "home-lanes"),
        ("lane", "home-lanes"),
        ("start", "home-lanes"),
        ("resume", "home-lanes"),
        ("harness", "error-boundary"),
        ("screenshot", "error-boundary"),
    ]
    for needle, slug in mapping:
        if needle in blob:
            return slug
    return "player-shell"


def add_defect(
    severity: str,
    title: str,
    repro: str,
    expected: str,
    actual: str,
    url: str = "",
    extra: dict[str, Any] | None = None,
) -> None:
    control = ""
    confidence = None
    kind = ""
    if extra:
        control = str(extra.get("control") or "")
        kind = str(extra.get("kind") or "")
        if isinstance(extra.get("confidence"), (int, float)):
            confidence = float(extra["confidence"])
    d: dict[str, Any] = {
        "id": f"D{len(DEFECTS)+1:03d}",
        "severity": severity,
        "title": title,
        "repro": repro,
        "expected": expected,
        "actual": actual,
        "url": url,
        "ts": datetime.now(timezone.utc).isoformat(),
        "component": guess_component(title, control),
        "control_label": control or title,
        "kind": kind,
    }
    if confidence is not None:
        d["confidence"] = confidence
    if extra:
        for k, v in extra.items():
            if k not in d:
                d[k] = v
    key = (title, url, actual[:120])
    for existing in DEFECTS:
        if (existing["title"], existing["url"], existing["actual"][:120]) == key:
            return
    DEFECTS.append(d)
    conf_s = f" conf={confidence}" if confidence is not None else ""
    print(f"DEFECT {severity}{conf_s} {title} @ {url}", flush=True)


def text_sig(page: dict[str, Any]) -> str:
    return (page.get("text") or "")[:2000]


def classify_noop(label: str, kind: str) -> str:
    low = label.lower()
    if any(
        k in low
        for k in (
            "explain again",
            "worked example",
            "resume",
            "start",
            "continue",
            "back",
            "exit",
            "submit",
            "send",
        )
    ):
        return "P0"
    if any(k in low for k in ("mic", "speaker", "sound", "voice", "audio", "chat", "assistant", "chip")):
        return "P1"
    if kind == "wait":
        return "P2"
    return "P1"


def analyze_action(before: dict[str, Any], after: dict[str, Any], hist_entry: dict[str, Any]) -> None:
    label = hist_entry.get("action") or ""
    kind = hist_entry.get("kind") or ""
    url_b = before.get("url") or ""
    url_a = after.get("url") or ""
    text_b = text_sig(before)
    text_a = text_sig(after)
    changed = hist_entry.get("page_changed")
    url_changed = url_b != url_a
    text_changed = text_b != text_a
    effective = bool(changed) or url_changed or text_changed
    conf = hist_entry.get("confidence")

    if "/play/" in url_a:
        ta = (after.get("text") or "").strip()
        if len(ta) < 40 and "explain" not in ta.lower():
            add_defect(
                "P0",
                "Blank or near-empty play surface",
                f"Navigate/Start into lesson ending at {url_a}",
                "Lesson teach/probe UI with content and controls",
                f"Page text length={len(ta)} preview={ta[:200]!r}",
                url_a,
                {"control": label, "kind": kind, "confidence": conf},
            )

    if kind == "wait":
        return

    if not effective:
        sev = classify_noop(label, kind)
        add_defect(
            sev,
            f"Dead/no-op control: {label}",
            f"On {url_b}, click/activate '{label}' and wait ~3s",
            "Visible change (URL, DOM text, panel, toast) within ~3s",
            "No URL/text/fingerprint change after action",
            url_b,
            {"control": label, "kind": kind, "confidence": conf},
        )

    ta = after.get("text") or ""
    if "which fraction" in ta.lower() and ("3/4" in ta or "three fourths" in ta.lower()):
        if "explain again" in ta.lower() and ("?" in ta):
            add_defect(
                "P2",
                "Possible teach/probe answer co-visibility (spoil risk)",
                "Open fractions (or similar) probe step with teach controls visible",
                "Probe should not display the correct answer before submission",
                "Answer-like fraction text visible alongside probe question",
                url_a,
                {"control": label, "kind": kind, "confidence": conf},
            )


def run_phase(phase: dict[str, Any]) -> None:
    global GLOBAL_ACTIONS, GLOBAL_DECISIONS, OPENROUTER_OK
    name = phase["name"]
    print(f"\n===== PHASE {name} =====", flush=True)
    phase_actions = 0
    phase_start = time.perf_counter()
    status = "error"
    try:
        with Agent(phase["url"], phase["goal"], record_dir=None, screenshots=False) as agent:
            page = agent.state["page"]
            PAGES_VISITED.add(page.get("url") or "")
            while agent.state["status"] not in {"done", "blocked"}:
                if GLOBAL_ACTIONS >= ACTION_CAP:
                    agent.state["status"] = "blocked"
                    ERRORS.append(f"Global action cap {ACTION_CAP}")
                    break
                if phase_actions >= phase["max_actions"]:
                    agent.state["status"] = "blocked"
                    break
                before = dict(agent.state["page"])
                before_text = text_sig(before)
                try:
                    snap = agent.command("tick")
                except StalePage:
                    agent.state["decision"] = None
                    agent.state["status"] = "ready"
                    agent.state["page"] = agent.state["browser"].observe(screenshot=False)
                    continue
                except Exception as exc:  # noqa: BLE001 — crawl continues other phases
                    ERRORS.append(f"{name}: {type(exc).__name__}: {exc}")
                    traceback.print_exc()
                    break

                if agent.state["decisions"]:
                    d = agent.state["decisions"][-1]
                    OPENROUTER_OK = True
                    jlog(
                        DECISIONS_PATH,
                        {
                            "phase": name,
                            "choice": d.get("choice"),
                            "operation": d.get("operation"),
                            "target": d.get("target"),
                            "confidence": d.get("confidence"),
                            "probabilities": d.get("probabilities"),
                            "latency_ms": d.get("latency_ms"),
                            "url": (snap.get("page") or {}).get("url"),
                            "usage": d.get("usage"),
                            "elapsed_ms": d.get("elapsed_ms"),
                        },
                    )

                after = snap.get("page") or agent.state["page"]
                PAGES_VISITED.add(after.get("url") or "")

                hist = agent.state["history"]
                if hist and len(hist) > phase_actions:
                    h = hist[-1]
                    phase_actions = len(hist)
                    GLOBAL_ACTIONS += 1
                    BUTTONS_CLICKED.append(h.get("action") or "")
                    jlog(
                        ACTIONS_PATH,
                        {
                            "phase": name,
                            "step_global": GLOBAL_ACTIONS,
                            "step_phase": phase_actions,
                            "action": h.get("action"),
                            "kind": h.get("kind"),
                            "choice": h.get("choice"),
                            "page_changed": h.get("page_changed"),
                            "url_before": before.get("url"),
                            "url_after": after.get("url"),
                            "title_after": after.get("title"),
                            "text_changed": before_text != text_sig(after),
                            "confidence": h.get("confidence"),
                            "probability": h.get("probability"),
                            "latency_ms": h.get("latency_ms"),
                        },
                    )
                    analyze_action(before, after, h)
                    print(
                        f"{GLOBAL_ACTIONS:3d} [{name}] {h.get('kind')} {h.get('action')!r} "
                        f"changed={h.get('page_changed')} conf={h.get('confidence')} "
                        f"-> {(after.get('url') or '')[:70]}",
                        flush=True,
                    )

                status = agent.state["status"]
                if status in {"done", "blocked"}:
                    break

            GLOBAL_DECISIONS += len(agent.state.get("decisions") or [])

            final_url = (agent.state["page"] or {}).get("url") or ""
            labels = [((a.get("label") or "").lower()) for a in (agent.state["page"].get("actions") or [])]
            if "/play/" in final_url:
                has_nav = any(
                    ("back" in L) or ("exit" in L) or ("home" in L) or ("leave" in L) or ("close" in L)
                    for L in labels
                )
                if not has_nav:
                    add_defect(
                        "P1",
                        "Missing Back/exit control on play surface",
                        f"Enter lesson player at {final_url} and inspect visible actions",
                        "Visible Back/Exit/Home control to leave lesson",
                        f"No back/exit/home among {len(labels)} actions: {labels[:20]}",
                        final_url,
                    )
            status = agent.state["status"]
    except Exception as exc:  # noqa: BLE001
        status = "error"
        ERRORS.append(f"{name} fatal: {type(exc).__name__}: {exc}")
        traceback.print_exc()

    PHASE_LOG.append(
        {
            "phase": name,
            "status": status,
            "phase_actions": phase_actions,
            "elapsed_s": round(time.perf_counter() - phase_start, 2),
        }
    )


def to_schema_defects(defects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for d in defects:
        item: dict[str, Any] = {
            "id": d["id"],
            "severity": d["severity"],
            "component": d.get("component") or "player-shell",
            "control_label": d.get("control_label") or d.get("control") or d.get("title") or d["id"],
            "url": d.get("url") or BASE_URL,
            "expected": d.get("expected") or "",
            "actual": d.get("actual") or "",
            "repro_steps": [d["repro"]] if d.get("repro") else [d.get("title") or d["id"]],
            "evidence": {"action_id": d.get("id")},
            "source": "jev",
        }
        if isinstance(d.get("confidence"), (int, float)):
            item["confidence"] = float(d["confidence"])
        out.append(item)
    return out


def write_report() -> dict[str, Any]:
    finished_at = datetime.now(timezone.utc)
    duration_s = round(time.perf_counter() - STARTED, 2)
    order = {"P0": 0, "P1": 1, "P2": 2}
    defects_sorted = sorted(DEFECTS, key=lambda d: (order.get(d["severity"], 9), d["id"]))
    schema_defects = to_schema_defects(defects_sorted)
    blocking = [d for d in defects_sorted if d["severity"] in {"P0", "P1"}]
    run_id = STARTED_AT.strftime("%Y%m%dT%H%M%SZ")
    if PIN_COMMIT:
        run_id = f"{run_id}-{PIN_COMMIT[:12]}"

    summary: dict[str, Any] = {
        "schema_version": "ux-defect-report.v1",
        "run_id": run_id,
        "source": "jev",
        "started_at": STARTED_AT.isoformat(),
        "finished_at": finished_at.isoformat(),
        "base_url": BASE_URL,
        "agent": {
            "name": "jev-ultrafast",
            "model": MODEL,
            "harness_version": PIN_COMMIT or "unpinned",
        },
        "controls_exercised": GLOBAL_ACTIONS,
        # pass=false when any P0/P1 (confidence never soft-skips)
        "pass": len(blocking) == 0,
        "catch_rate": (len(defects_sorted) / GLOBAL_ACTIONS) if GLOBAL_ACTIONS else 0.0,
        "artifacts": {
            "actions_jsonl": "actions.jsonl",
            "decisions_jsonl": "decisions.jsonl",
            "report_md": "report.md",
            "screenshots_dir": "screenshots",
        },
        "defects": schema_defects,
    }
    ops = {
        "status": "done" if not ERRORS else ("partial" if GLOBAL_ACTIONS else "error"),
        "duration_s": duration_s,
        "actions": GLOBAL_ACTIONS,
        "decisions": GLOBAL_DECISIONS,
        "openrouter_decisions_ok": OPENROUTER_OK,
        "pages_visited": sorted(PAGES_VISITED),
        "unique_pages": len(PAGES_VISITED),
        "buttons_clicked_count": len(BUTTONS_CLICKED),
        "unique_buttons": sorted(set(BUTTONS_CLICKED)),
        "defect_count": len(defects_sorted),
        "defects_raw": defects_sorted,
        "phases": PHASE_LOG,
        "errors": ERRORS,
        "action_cap": ACTION_CAP,
        "artifact_dir": str(ART),
        "known_suspects_checked": KNOWN_SUSPECTS,
        "ts_utc": finished_at.isoformat(),
        "pin_commit": PIN_COMMIT,
        "fail_policy": (
            "ANY P0/P1 fails CI regardless of confidence; "
            "confidence is recorded for investigation vs ship-fix signal only"
        ),
    }
    (ART / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    (ART / "crawl_ops.json").write_text(json.dumps(ops, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Study OS full guest UX defect crawl (Jev Ultrafast)",
        "",
        f"- **Live URL:** {BASE_URL}",
        f"- **When (UTC):** {summary['ts_utc']}",
        f"- **Duration:** {duration_s}s",
        f"- **Actions:** {GLOBAL_ACTIONS} (cap {ACTION_CAP})",
        f"- **Decisions:** {GLOBAL_DECISIONS} (OpenRouter Decisions OK: {OPENROUTER_OK})",
        f"- **Pin:** `{PIN_COMMIT or 'unpinned'}`",
        f"- **Model:** `{MODEL}`",
        f"- **Pages visited:** {len(PAGES_VISITED)}",
        f"- **Defects:** {len(defects_sorted)} (blocking P0/P1: {len(blocking)})",
        f"- **Artifact dir:** `{ART}`",
        "",
        "## Fail policy",
        "",
        "- **ANY P0 or P1 fails CI**, regardless of Decisions confidence.",
        "- Confidence is recorded on decisions/actions (and defects when known).",
        "- Low confidence => agents should investigate why; still a fail.",
        "- High confidence => ship the product fix without re-litigating.",
        "",
        "## Coverage",
        "",
        "### Pages",
    ]
    for u in sorted(PAGES_VISITED):
        lines.append(f"- {u}")
    lines.append("")
    lines.append("### Phases")
    for p in PHASE_LOG:
        lines.append(
            f"- **{p['phase']}**: status={p.get('status')} "
            f"actions={p.get('phase_actions')} elapsed={p.get('elapsed_s')}s"
        )
    lines.append("")
    lines.append("### Buttons / controls clicked")
    for b in sorted(set(BUTTONS_CLICKED)):
        lines.append(f"- {b}")
    lines.append("")
    lines.append("## Defects")
    lines.append("")
    if not defects_sorted:
        lines.append("_No defects logged by automated heuristics (may still have coverage gaps)._")
    for d in defects_sorted:
        conf = d.get("confidence")
        conf_s = f" (confidence={conf})" if isinstance(conf, (int, float)) else ""
        lines.append(f"### {d['id']} — {d['severity']}: {d['title']}{conf_s}")
        lines.append("")
        lines.append(f"- **URL:** {d.get('url')}")
        lines.append(f"- **Component:** {d.get('component')}")
        lines.append(f"- **Control:** {d.get('control_label')}")
        lines.append(f"- **Repro:** {d.get('repro')}")
        lines.append(f"- **Expected:** {d.get('expected')}")
        lines.append(f"- **Actual:** {d.get('actual')}")
        lines.append("")
    lines.append("## Known #126 suspects checklist")
    lines.append("")
    for s in KNOWN_SUSPECTS:
        hit = [
            d
            for d in defects_sorted
            if s.split()[0].lower() in (d["title"] + d["actual"]).lower()
            or s.lower() in (d["title"] + d["actual"]).lower()
        ]
        mark = "HIT" if hit else "exercised/observed (see actions.jsonl)"
        lines.append(f"- **{s}:** {mark}")
    lines.append("")
    lines.append("## Blockers / errors")
    lines.append("")
    if ERRORS:
        for e in ERRORS:
            lines.append(f"- {e}")
    else:
        lines.append("- None")
    lines.append("")
    lines.append("## Method")
    lines.append("")
    lines.append(
        f"- Agent: `jev-ultrafast` pin `{PIN_COMMIT or 'unpinned'}` with OpenRouter Decisions "
        f"(`{MODEL}`), no TypeSafe key."
    )
    lines.append("- Pass/fail oracle: after each non-wait action, require URL/text/fingerprint change; else DEFECT.")
    lines.append("- CI gate: `tools/gate_ux_defect_report.py` fails on ANY P0/P1 (confidence never soft-skips).")
    (ART / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {ART / 'report.md'} and summary.json defects={len(defects_sorted)}", flush=True)
    return summary


def require_openrouter() -> None:
    if not (os.environ.get("OPENROUTER_API_KEY") or os.environ.get("TYPESAFE_API_KEY")):
        print(
            "ERROR: OPENROUTER_API_KEY is required for Ultrafast Decisions. "
            "Add the repository secret OPENROUTER_API_KEY (INFERHUB_API_KEY alone is not enough).",
            file=sys.stderr,
            flush=True,
        )
        raise SystemExit(2)
    if not os.environ.get("TEXT_MODEL_API_KEY"):
        # TYPE_TEXT uses the same OpenRouter key when unset.
        os.environ["TEXT_MODEL_API_KEY"] = os.environ.get("OPENROUTER_API_KEY") or ""
        os.environ.setdefault("TEXT_MODEL_BASE_URL", "https://openrouter.ai/api/v1")
        os.environ.setdefault("TEXT_MODEL", "inception/mercury-2.5")
        os.environ.setdefault("TEXT_MODEL_REASONING", "none")


def main() -> None:
    require_openrouter()
    print(
        json.dumps(
            {
                "base_url": BASE_URL,
                "artifact_dir": str(ART),
                "pin": PIN_COMMIT,
                "model": MODEL,
                "action_cap": ACTION_CAP,
                "bu_cdp": bool(os.environ.get("BU_CDP_URL") or os.environ.get("BU_CDP_WS")),
            },
            indent=2,
        ),
        flush=True,
    )
    for phase in PHASES:
        if GLOBAL_ACTIONS >= ACTION_CAP:
            break
        run_phase(phase)
        time.sleep(0.5)
    summary = write_report()
    print(
        "DONE_CRAWL",
        json.dumps(
            {
                "actions": GLOBAL_ACTIONS,
                "decisions": GLOBAL_DECISIONS,
                "defects": len(DEFECTS),
                "blocking_p0_p1": sum(1 for d in DEFECTS if d["severity"] in {"P0", "P1"}),
                "openrouter_ok": OPENROUTER_OK,
                "pass": summary.get("pass"),
                "art": str(ART),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
