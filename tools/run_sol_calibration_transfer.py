#!/usr/bin/env python3
"""MT-E001: frozen Sliding Window calibration -> Sol -> fuzzed learner -> HTML review."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import random
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "MT-E001"
CALIBRATION = ROOT / "calibration/cases/sliding-window.subject-001.2026-09-04/transfer-calibration.v0.1.json"
OUTPUT_ROOT = ROOT / "artifacts/model-tutoring-experiments/MT-E001"
PROBLEM = "Given nums and target, return indices of two numbers whose sum is target."
TEACHER_MODEL = "gpt-5.6-sol"
STUDENT_MODEL = "gpt-5.6-luna"
MAX_EXCHANGES = 150
SEED = 20260915
TIMEOUT = 240

LEARNER_STATES = (
    ("correct", 30),
    ("partially_correct", 15),
    ("wrong", 15),
    ("slightly_misaligned", 15),
    ("uncertain", 10),
    ("ask_why", 5),
    ("ask_smaller_step", 5),
    ("representation_confusion", 5),
)

STATE_GUIDANCE = {
    "correct": "Correctly do only the specific thing just asked; do not jump ahead.",
    "partially_correct": "Get a meaningful sub-part right but miss one relevant piece.",
    "wrong": "Make one plausible beginner mistake about the current relation.",
    "slightly_misaligned": "Answer a nearby relation or confuse two closely related roles.",
    "uncertain": "Attempt the task with visible uncertainty or a tentative check.",
    "ask_why": "Ask one natural beginner why-question about the latest relation.",
    "ask_smaller_step": "Say the latest step is too large and ask for one smaller concrete step.",
    "representation_confusion": "Show plausible confusion about notation, diagram, index/value, or variable role.",
}

REVIEW_FLAGS = (
    ("teacher_weak", "teacher weak"),
    ("student_weak", "student weak / unrealistic"),
    ("missing_bridge", "missing bridge"),
    ("step_too_large", "step too large"),
    ("bad_representation", "bad representation"),
    ("diagram_weak", "diagram / chart weak"),
    ("repetition_stuck", "unnecessary repetition / stuck"),
    ("semantic_error", "semantic error"),
    ("premature_abstraction", "premature abstraction / code"),
    ("answer_leak", "answer leak"),
    ("progression_wrong", "progression / assessment wrong"),
    ("other", "other"),
)


@dataclass(frozen=True)
class TeacherTurn:
    status: str
    active_bridge: str
    message: str


class CodexSession:
    def __init__(self, *, label: str, model: str, bootstrap: str, cwd: Path, codex_bin: str, timeout: int) -> None:
        self.label = label
        self.model = model
        self.bootstrap = bootstrap
        self.cwd = cwd
        self.codex_bin = codex_bin
        self.timeout = timeout
        self.thread_id: str | None = None

    def _command(self, resume: str | None) -> list[str]:
        cmd = [self.codex_bin, "exec", "--json", "--color", "never", "--model", self.model]
        cmd.extend(["resume", resume, "-"] if resume else ["-"])
        return cmd

    @staticmethod
    def _parse(stdout: str) -> tuple[str | None, str]:
        thread_id = None
        messages: list[str] = []
        for line in stdout.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "thread.started":
                thread_id = event.get("thread_id") or thread_id
            if event.get("type") == "item.completed":
                item = event.get("item") or {}
                if item.get("type") == "agent_message" and str(item.get("text", "")).strip():
                    messages.append(str(item["text"]).strip())
        if not messages:
            raise RuntimeError("Codex returned no agent message")
        return thread_id, messages[-1]

    def ask(self, request: str, recovery_context: str = "") -> str:
        first_resume = self.thread_id
        last_error: Exception | None = None
        for attempt in range(2):
            resume = first_resume if attempt == 0 else None
            prompt = request
            if resume is None:
                parts = [self.bootstrap]
                if recovery_context:
                    parts.append("VISIBLE CONVERSATION SO FAR:\n" + recovery_context)
                parts.append("CURRENT REQUEST:\n" + request)
                prompt = "\n\n".join(parts)
            try:
                result = subprocess.run(
                    self._command(resume), input=prompt, text=True, encoding="utf-8",
                    capture_output=True, cwd=self.cwd, check=False, timeout=self.timeout,
                )
            except subprocess.TimeoutExpired as exc:
                last_error = RuntimeError(f"{self.label} timed out")
                self.thread_id = None
                continue
            if result.returncode != 0:
                last_error = RuntimeError((result.stderr or result.stdout or "Codex failed").strip())
                self.thread_id = None
                continue
            try:
                observed, message = self._parse(result.stdout or "")
            except RuntimeError as exc:
                last_error = exc
                self.thread_id = None
                continue
            self.thread_id = observed or resume
            if self.thread_id is None:
                last_error = RuntimeError(f"{self.label} did not report a thread id")
                continue
            return message
        raise last_error or RuntimeError(f"{self.label} failed")


def choose_state(rng: random.Random) -> str:
    names = [name for name, _ in LEARNER_STATES]
    weights = [weight for _, weight in LEARNER_STATES]
    return rng.choices(names, weights=weights, k=1)[0]


def parse_teacher(raw: str) -> TeacherTurn:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1]).strip() if len(lines) >= 3 else text
    decoder = json.JSONDecoder()
    payload = None
    for i, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[i:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            payload = value
            break
    if payload is None:
        raise ValueError("teacher response must contain JSON")
    status = payload.get("status")
    bridge = payload.get("active_bridge")
    message = payload.get("message")
    if status not in {"continue", "complete"}:
        raise ValueError("teacher status must be continue or complete")
    if not isinstance(bridge, str) or not bridge.strip():
        raise ValueError("active_bridge must be non-empty")
    if not isinstance(message, str) or not message.strip():
        raise ValueError("message must be non-empty")
    return TeacherTurn(status, bridge.strip(), message.rstrip())


def conversation(records: list[dict[str, Any]], pending_teacher: TeacherTurn | None = None) -> str:
    parts: list[str] = []
    for row in records:
        parts.append("TEACHER:\n" + row["teacher_message"])
        parts.append("LEARNER:\n" + row["learner_message"])
    if pending_teacher:
        parts.append("TEACHER:\n" + pending_teacher.message)
    return "\n\n".join(parts)


def teacher_bootstrap(calibration: str, problem: str) -> str:
    return f'''You are GPT-5.6 Sol, the measured teacher in Study OS experiment MT-E001.

TARGET PROBLEM
{problem}

FROZEN PEDAGOGICAL CALIBRATION MANUAL
Transfer its teaching granularity, interaction control, and representation behavior. Do not copy Sliding Window solution structure, vocabulary, constants, or stage order.

{calibration}

ISOLATION AND TEACHING CONTRACT
- Use only this manual, the target problem, and this run's visible conversation.
- Do not inspect files, repositories, tools, web sources, hidden rubrics, or historical Two Sum scripts.
- Derive Two Sum's learner-sized dependency path yourself.
- Keep turns concise and grounded; use aligned diagrams/state charts where useful.
- Ground objects/terms/symbols before using them in new relations.
- If the learner is wrong/partial/uncertain, repair the smallest failed relation, then use a changed retry and verify recovery when needed.
- Do not make the learner repair tutor mistakes.
- Do not reveal a complete solution before its component meanings and relations are earned.
- Turn count is never completion evidence.
- Complete only when the learner visibly demonstrates enough integrated understanding to explain/assemble a correct solution.

Return exactly one JSON object:
{{"status":"continue|complete","active_bridge":"short label","message":"learner-visible response"}}
'''


def student_bootstrap(problem: str) -> str:
    return f'''You are a synthetic beginner learner in Study OS experiment MT-E001.

TARGET PROBLEM
{problem}

- You do not know the teacher's calibration manual, hidden plan, rubric, or full solution.
- Learn from the visible conversation plus ordinary beginner Python knowledge.
- Do not inspect files, repositories, tools, or external sources.
- Do not intentionally sabotage the lesson or repair tutor mistakes for the tutor.
- Do not jump to the full hash-map solution before the visible teaching earns it.
- Stay coherent with knowledge already established.
- Keep replies natural and concise, normally 1-3 sentences.
- A per-turn response-quality state modifies how well you answer; it does not erase prior learning.
'''


def next_run_dir(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    used = [int(p.name[4:]) for p in root.iterdir() if p.is_dir() and p.name.startswith("run-") and p.name[4:].isdigit()]
    path = root / f"run-{max(used, default=0)+1:03d}"
    path.mkdir()
    return path


def write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    tmp.replace(path)


def render_html(meta: dict[str, Any], rows: list[dict[str, Any]], final_teacher: TeacherTurn | None) -> str:
    cards = []
    for row in rows:
        flags = "".join(f'<label><input type="checkbox" data-flag="{html.escape(k)}"> {html.escape(label)}</label>' for k, label in REVIEW_FLAGS)
        cards.append(f'''<section class="exchange" data-id="{row['exchange_id']}">
<h2>Exchange {row['exchange_id']}</h2>
<p><b>Bridge:</b> {html.escape(row['active_bridge'])} · <b>fuzz state:</b> {html.escape(row['learner_state'])}</p>
<h3>Teacher</h3><pre>{html.escape(row['teacher_message'])}</pre>
<h3>Learner</h3><pre>{html.escape(row['learner_message'])}</pre>
<details open><summary>Review</summary><div class="flags">{flags}</div><textarea data-comment rows="3" placeholder="What could be better?"></textarea></details>
</section>''')
    closure = ""
    if final_teacher:
        closure = f'''<section class="exchange"><h2>Final teacher closure</h2><p><b>{html.escape(final_teacher.status)}</b> · {html.escape(final_teacher.active_bridge)}</p><pre>{html.escape(final_teacher.message)}</pre></section>'''
    meta_json = json.dumps(meta, ensure_ascii=False)
    meta_pre = html.escape(json.dumps(meta, ensure_ascii=False, indent=2))
    flag_names = json.dumps([k for k, _ in REVIEW_FLAGS])
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(meta['run_id'])} review</title>
<style>body{{font-family:system-ui;max-width:1100px;margin:auto;padding:24px;background:#f6f6f7}}header,.exchange{{background:#fff;border:1px solid #ddd;border-radius:12px;padding:18px;margin-bottom:18px}}pre{{white-space:pre-wrap;font-family:ui-monospace,monospace;background:#fafafa;border:1px solid #ddd;border-radius:8px;padding:14px}}.flags{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px;margin:12px 0}}textarea{{width:100%;box-sizing:border-box}}button{{margin:4px;padding:8px 12px}}</style></head><body>
<header><h1>MT-E001 — Sol calibration transfer</h1><p><b>{html.escape(meta['status'])}</b> · {len(rows)} exchanges</p><p><b>Problem:</b> {html.escape(meta['problem'])}</p><button id="tsv">Export TSV</button><button id="json">Export JSON</button><button id="clear">Clear review</button><details><summary>Run metadata</summary><pre>{meta_pre}</pre></details></header>
{''.join(cards)}{closure}
<script>const META={meta_json};const FLAGS={flag_names};const KEY='study-os-review:'+META.run_id;
function collect(){{return [...document.querySelectorAll('.exchange[data-id]')].map(card=>{{let r={{exchange_id:card.dataset.id,reviewer_comment:card.querySelector('[data-comment]').value}};FLAGS.forEach(f=>r[f]=card.querySelector(`[data-flag="${{f}}"]`).checked);return r;}})}}
function save(){{localStorage.setItem(KEY,JSON.stringify(collect()))}}function restore(){{let x=localStorage.getItem(KEY);if(!x)return;let by=Object.fromEntries(JSON.parse(x).map(r=>[String(r.exchange_id),r]));document.querySelectorAll('.exchange[data-id]').forEach(c=>{{let r=by[c.dataset.id];if(!r)return;FLAGS.forEach(f=>c.querySelector(`[data-flag="${{f}}"]`).checked=!!r[f]);c.querySelector('[data-comment]').value=r.reviewer_comment||'';}})}}
function dl(name,text,type){{let b=new Blob([text],{{type}}),u=URL.createObjectURL(b),a=document.createElement('a');a.href=u;a.download=name;a.click();URL.revokeObjectURL(u)}}document.addEventListener('change',save);document.addEventListener('input',save);
document.getElementById('json').onclick=()=>dl(META.run_id+'-review.json',JSON.stringify({{metadata:META,annotations:collect()}},null,2),'application/json');document.getElementById('tsv').onclick=()=>{{let cols=['exchange_id',...FLAGS,'reviewer_comment'],esc=v=>String(v??'').replace(/\t/g,' ').replace(/\r?\n/g,' '),lines=[cols.join('\t'),...collect().map(r=>cols.map(c=>esc(r[c])).join('\t'))];dl(META.run_id+'-review.tsv',lines.join('\n')+'\n','text/tab-separated-values')}};document.getElementById('clear').onclick=()=>{{if(confirm('Clear local review state?')){{localStorage.removeItem(KEY);location.reload()}}}};restore();</script></body></html>'''


def main() -> int:
    p = argparse.ArgumentParser(description="Run MT-E001 Sol calibration transfer")
    p.add_argument("--calibration", type=Path, default=CALIBRATION)
    p.add_argument("--problem", default=PROBLEM)
    p.add_argument("--teacher-model", default=TEACHER_MODEL)
    p.add_argument("--student-model", default=STUDENT_MODEL)
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--max-exchanges", type=int, default=MAX_EXCHANGES)
    p.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    p.add_argument("--codex-bin", default="codex")
    p.add_argument("--timeout-seconds", type=int, default=TIMEOUT)
    args = p.parse_args()
    if args.max_exchanges < 1:
        raise SystemExit("--max-exchanges must be >= 1")

    calibration_bytes = args.calibration.read_bytes()
    calibration_text = calibration_bytes.decode("utf-8")
    payload = json.loads(calibration_text)
    if payload.get("artifact_type") != "transfer_calibration":
        raise SystemExit("calibration artifact_type must be transfer_calibration")

    run_dir = next_run_dir(args.output_root)
    run_id = run_dir.name
    calibration_sha = hashlib.sha256(calibration_bytes).hexdigest()
    (run_dir / "calibration-input.json").write_bytes(calibration_bytes)

    meta: dict[str, Any] = {
        "schema_version": "study-os.mt-e001-run.v0.1", "experiment_id": EXPERIMENT_ID,
        "run_id": run_id, "status": "running", "problem": args.problem,
        "teacher_model": args.teacher_model, "student_model": args.student_model,
        "seed": args.seed, "max_exchanges": args.max_exchanges,
        "calibration_file_sha256": calibration_sha,
        "isolation": {"teacher_repo_access": False, "student_repo_access": False,
                      "raw_sliding_window_transcript_supplied": False,
                      "historical_two_sum_regression_script_supplied": False,
                      "actor_working_directory": "temporary empty directory outside repository"},
    }
    manifest = run_dir / "run-manifest.json"
    manifest.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    rng = random.Random(args.seed)
    rows: list[dict[str, Any]] = []
    final_teacher: TeacherTurn | None = None
    reason = "anti_loop_ceiling_exhausted"

    with tempfile.TemporaryDirectory(prefix="study-os-mt-e001-") as tmp:
        cwd = Path(tmp)
        teacher = CodexSession(label="Sol teacher", model=args.teacher_model, bootstrap=teacher_bootstrap(calibration_text, args.problem), cwd=cwd, codex_bin=args.codex_bin, timeout=args.timeout_seconds)
        student = CodexSession(label="synthetic learner", model=args.student_model, bootstrap=student_bootstrap(args.problem), cwd=cwd, codex_bin=args.codex_bin, timeout=args.timeout_seconds)

        teacher_turn = parse_teacher(teacher.ask("Begin at the smallest useful grounded starting point. Do not dump a full plan or solution."))
        for n in range(1, args.max_exchanges + 1):
            if teacher_turn.status == "complete":
                final_teacher, reason = teacher_turn, "teacher_declared_integrated_completion"
                break
            state = choose_state(rng)
            student_msg = student.ask(
                f"Teacher message:\n\n{teacher_turn.message}\n\nResponse-quality state: {state}\nGuidance: {STATE_GUIDANCE[state]}\n\nReply with exactly one learner-visible message.",
                recovery_context=conversation(rows, teacher_turn),
            ).strip()
            rows.append({"schema_version":"study-os.mt-e001-exchange.v0.1","exchange_id":n,"active_bridge":teacher_turn.active_bridge,"learner_state":state,"teacher_message":teacher_turn.message,"learner_message":student_msg})
            write_jsonl(rows, run_dir / "transcript.jsonl")
            teacher_turn = parse_teacher(teacher.ask(
                f"Learner reply:\n\n{student_msg}\n\nRespond to this evidence. Continue or complete under the calibration contract.",
                recovery_context=conversation(rows),
            ))
            if teacher_turn.status == "complete":
                final_teacher, reason = teacher_turn, "teacher_declared_integrated_completion"
                break
        else:
            final_teacher = teacher_turn

    status = "completed" if final_teacher and final_teacher.status == "complete" else "failed"
    meta.update({"status":status,"completion_reason":reason,"exchange_count":len(rows),"final_teacher_status":final_teacher.status if final_teacher else None})
    manifest.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    (run_dir / "review.html").write_text(render_html(meta, rows, final_teacher), encoding="utf-8")
    print(f"MT-E001 {status}: {run_dir}")
    print(f"Review: {run_dir / 'review.html'}")
    return 0 if status == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
