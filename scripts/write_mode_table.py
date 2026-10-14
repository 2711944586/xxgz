"""Mode comparison from the exported catalog. Writes a TeX table."""

import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
frames = json.loads((root / "demo" / "public" / "catalog.json").read_text(encoding="utf-8"))
groups = {}
for row in frames:
    groups.setdefault(row["key"], []).append(row)

lines = [
    r"\begin{longtable}{llrrrrrr}",
    r"\toprule",
    r"策略 & 档 & 停止时刻 & 进度 & 方差 & A & B & C \\",
    r"\midrule",
    r"\endhead",
]
for key in sorted(groups):
    rows = groups[key]
    if not key.endswith("_30"):
        continue
    policy, cook, _ = key.split("_")
    last = rows[-1]
    lines.append(
        f"{policy} & {cook} & {last['time']:.0f} & {last['alpha']:.3f} & {last['varR']:.3f} & "
        f"{max(r['pathA'] for r in rows):.0f} & {max(r['pathB'] for r in rows):.0f} & "
        f"{max(r['pathC'] for r in rows):.0f} \\\\"
    )
lines += [r"\bottomrule", r"\end{longtable}"]
(root / "monograph" / "mode_table.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(len(groups))
