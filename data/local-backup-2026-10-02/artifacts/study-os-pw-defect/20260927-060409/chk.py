from pathlib import Path
p = Path(r"D:\claude\Study-os\artifacts\study-os-pw-defect\20260927-060409\ux-defect-pass.cjs")
t = p.read_text(encoding="utf-8")
print("braces", t.count("{")-t.count("}"))
# show around A14
idx = t.find("// A14 mic/speaker: companion")
print(t[idx:idx+1200])
print("---AFTER---")
print(t[idx+1200:idx+1600])
