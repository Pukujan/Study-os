from pathlib import Path
p = Path(r"D:\claude\Study-os\artifacts\study-os-pw-defect\20260927-060210\ux-defect-pass.cjs")
text = p.read_text(encoding="utf-8")
# In fractions loop after visualOk2, add A14 + A12c when probe choices present
needle = '''          if (visualOk2.lineCount > 0) {
            addCheck("A12-numberline-readable", visualOk2.issues.length === 0,
              visualOk2.issues.length ? "Overlapping labels: " + visualOk2.issues.join(",") : "number-lines=" + visualOk2.lineCount + " ok", "P2");
            if (visualOk2.issues.length) await shot(page, "fail-A12-overlap");
            else await shot(page, "11-fractions-numberline");
            break;
          }'''
# The file may have slightly different formatting - search
idx = text.find("A12-numberline-readable")
print("idx", idx)
# find second occurrence in fractions section
idx2 = text.find('addCheck("A12-numberline-readable"', text.find("Secondary sample"))
print("idx2", idx2)
print(repr(text[idx2:idx2+450]))
