from pathlib import Path
import json
art = Path(r"D:\claude\Study-os\artifacts\study-os-pw-defect\20260927-060651")
summary = json.loads((art / "summary.json").read_text(encoding="utf-8"))
for d in summary["defects"]:
    if d["id"] == "A13-chat-ack":
        d["repro"] = (
            "Guest open https://study.design-bakery.com -> Try Big O -> open companion via pet "
            "(aria-label Open study assistant; may need force click — pet float animates) -> "
            "Send chat 'What should I notice on this step?' -> wait 20s. "
            "Expected: tutor/system bubble ack. Observed: no tutor/system bubble within 20s "
            "(screenshot fail-A13-chat-silent.png). Note: same check passed in prior run "
            "20260927-060210; console also shows intermittent 401 resource failures."
        )
        d["detail"] = (
            "No chat ack within 20000ms after companion send. "
            "Intermittent vs prior pass at 20260927-060210. Soft-fail continued suite."
        )
(art / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

# rewrite report.md Defects section detail from summary
md = (art / "report.md").read_text(encoding="utf-8")
# Replace P1 A13 block
import re
md2 = re.sub(
    r"### A13-chat-ack\n- Detail:.*?\n- Repro:.*?\n",
    "### A13-chat-ack\n- Detail: " + summary["defects"][0]["detail"] + "\n- Repro: " + summary["defects"][0]["repro"] + "\n",
    md,
    count=1,
    flags=re.S,
)
(art / "report.md").write_text(md2, encoding="utf-8")
print("updated")
print((art / "report.md").read_text(encoding="utf-8")[:1200])
