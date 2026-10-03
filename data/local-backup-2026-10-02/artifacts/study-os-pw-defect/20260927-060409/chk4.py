from pathlib import Path
p = Path(r"D:\claude\Study-os\artifacts\study-os-pw-defect\20260927-060409\ux-defect-pass.cjs")
lines = p.read_text(encoding="utf-8").splitlines()
for i in range(580, 620):
    print(f"{i+1}: {lines[i]}")
