from pathlib import Path
p = Path(r"D:\claude\Study-os\artifacts\study-os-pw-defect\20260927-060409\ux-defect-pass.cjs")
t = p.read_text(encoding="utf-8")
idx = t.find('note("A14-voice", "No companion/player mic/speaker controls in open panel");')
print(repr(t[idx:idx+400]))
# Also check node syntax
import subprocess
r = subprocess.run(["node", "--check", str(p)], capture_output=True, text=True)
print("check", r.returncode, r.stderr[:500])
