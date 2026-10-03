from pathlib import Path
p = Path(r"D:\claude\Study-os\artifacts\study-os-pw-defect\20260927-060409\ux-defect-pass.cjs")
lines = p.read_text(encoding="utf-8").splitlines()
for i in range(700, min(780, len(lines))):
    print(f"{i+1}: {lines[i]}")
print("total", len(lines))
