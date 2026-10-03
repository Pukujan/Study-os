from pathlib import Path
import subprocess
for name in ["20260927-055921", "20260927-060210", "20260927-060409"]:
    p = Path(rf"D:\claude\Study-os\artifacts\study-os-pw-defect\{name}\ux-defect-pass.cjs")
    if not p.exists():
        print(name, "missing"); continue
    r = subprocess.run(["node", "--check", str(p)], capture_output=True, text=True)
    print(name, "size", p.stat().st_size, "check", r.returncode, (r.stderr or "")[:120].replace("\n"," "))
    print("  has tryOpen", "tryOpenCompanion" in p.read_text(encoding="utf-8"))
    print("  has companion.mic", "companion.mic" in p.read_text(encoding="utf-8"))
