"""Inventory every line-chart figure and classify by visual quality signals."""
import re
from pathlib import Path

tex = "\n".join(p.read_text(encoding="utf-8")
                for p in Path("monograph").glob("ch*.tex"))
used = sorted(set(re.findall(
    r"\\(?:colimg|spanimg|includegraphics)(?:\[[^\]]*\])?\{([^}]+)\}", tex)))

# heuristic: line-chart candidates by name
LINE = [f for f in used if f.startswith(("F_curves", "T_", "R_", "C_", "S_profiles",
                                         "S_", "P_", "G_", "X_"))]
print(f"全部引用图 {len(used)}，其中折线/曲线类 {len(LINE)}\n")
for f in LINE:
    p = Path("results/figures/paper") / f
    kb = p.stat().st_size / 1024 if p.exists() else 0
    print(f"  {f:24s} {kb:6.1f} KB")
