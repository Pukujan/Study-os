from pathlib import Path
import re, shutil

src = Path(r"D:\claude\Study-os\artifacts\study-os-pw-defect\20260927-055921\ux-defect-pass.cjs")
text = src.read_text(encoding="utf-8")

# Minimal: include companion.mic/speaker in voice locator + prefer panel scope
text = text.replace(
    "const voiceBtns = page.locator('[data-track=\"voice.mic\"], [data-track=\"voice.speak\"]');",
    "const voiceBtns = panel.locator('[data-track=\"companion.mic\"], [data-track=\"companion.speaker\"], [data-track=\"voice.mic\"], [data-track=\"voice.speak\"]');",
    1,
)
# companionVoice filter becomes redundant but ok; voiceCount still sums both

# Also change note when zero to be clearer
text = text.replace(
    'note("A14-voice", "No mic/speaker controls present on this surface");',
    'note("A14-voice", "No companion.mic/speaker or voice.* controls found in panel");',
    1,
)

out = Path(r"D:\claude\Study-os\artifacts\study-os-pw-defect\20260927-060409\ux-defect-pass.cjs")
out.write_text(text, encoding="utf-8")
# keep a clean master copy
Path(r"D:\claude\Study-os\artifacts\study-os-pw-defect\ux-defect-pass.cjs").write_text(text, encoding="utf-8")

import subprocess
r = subprocess.run(["node", "--check", str(out)], capture_output=True, text=True)
print("check", r.returncode, r.stderr)
print("braces", text.count("{")-text.count("}"))
print("has companion.mic", "companion.mic" in text)
