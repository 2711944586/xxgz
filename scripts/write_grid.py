"""Median table of the full factor grid. Twelve seeds per cell."""

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
rows = json.loads((ROOT / "results" / "logs" / "study.json").read_text(encoding="utf-8"))
name = {"mince": "肉糜", "potato": "土豆", "dough": "面团",
        "steam": "蒸", "bake": "烤", "combi": "组合",
        "open": "开环", "pid": "腔温", "mpc": "无探针", "dual": "对偶"}
keys = []
seen = set()
for r in rows:
    k = (r["food"], r["length_mm"], r["t0"], r["m0"], r["cook"], r["policy"])
    if k not in seen:
        seen.add(k)
        keys.append(k)
lines = [
    r"\begin{longtable}{llrrllrr}",
    r"\toprule",
    r"食品 & 厚度 & 初温 & 含水 & 档 & 策略 & 偏差 & 加热 \\",
    r"\midrule",
    r"\endhead",
]
for food, length, t0, m0, cook, policy in keys:
    sub = [r for r in rows if r["food"] == food and r["length_mm"] == length and r["t0"] == t0 and r["m0"] == m0 and r["cook"] == cook and r["policy"] == policy]
    e = float(np.median([r["e_alpha"] for r in sub]))
    en = float(np.median([r["energy"] for r in sub]))
    lines.append(
        f"{name[food]} & {length} & {t0:.0f} & {m0:.2f} & {name[cook]} & {name[policy]} & {e:+.3f} & {en:.0f} \\\\"
    )
lines += [r"\bottomrule", r"\end{longtable}"]
(ROOT / "monograph" / "grid_table.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
q = [
    r"\begin{longtable}{llrrllrr}",
    r"\toprule",
    r"食品 & 厚度 & 初温 & 含水 & 档 & 策略 & 十分位 & 九十分位 \\",
    r"\midrule",
    r"\endhead",
]
for food, length, t0, m0, cook, policy in keys:
    sub = [r["e_alpha"] for r in rows if r["food"] == food and r["length_mm"] == length and r["t0"] == t0 and r["m0"] == m0 and r["cook"] == cook and r["policy"] == policy]
    q.append(
        f"{name[food]} & {length} & {t0:.0f} & {m0:.2f} & {name[cook]} & {name[policy]} & "
        f"{float(np.quantile(sub, 0.1)):+.3f} & {float(np.quantile(sub, 0.9)):+.3f} \\\\"
    )
q += [r"\bottomrule", r"\end{longtable}"]
(ROOT / "monograph" / "grid_quantile.tex").write_text("\n".join(q) + "\n", encoding="utf-8")
print(len(keys))
