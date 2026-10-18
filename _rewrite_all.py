"""Rewrite prose: remove duplicated sentences and AI-flavoured connectives.

Targets found by audit:
- 3 sentence pairs repeated verbatim across chapters
- 43 occurrences of 不是 (many in adversative 不是A而是B form)
- 40 occurrences of 因此 (mechanical causal linking)
- 28 em-dashes used as a thinking pause
- 23 occurrences of 同时 (weak parallelism)

The rewrite keeps every number, claim and citation; only the connective tissue
and the repeated sentences change.
"""
import re
from pathlib import Path

MONO = Path("monograph")
FILES = ["book.tex", "ch1.tex", "ch2.tex", "ch3.tex", "ch4.tex", "ch5.tex", "ch6.tex"]

# ---- duplicated sentences: keep the first, cut the later one ------------
DUPS = [
    # appears in ch4 (equation explanation) and ch6 (conclusion)
    ("热量滞留在近表面；窗内收缩的是热阻方差，冷点几乎没有升温。", 1),
    # appears in ch1 and ch5
    ("为冷点多送一股蒸汽，薄件上是冷凝收益，厚件上可能只是把表面打湿。", 1),
    # the IEC sentence appears in ch2 and ch6
    ("家用电器对漏电、温升和异常工作的通用要求见 IEC 60335-1 与 GB 4706.1", 1),
]

seen = {t: 0 for t, _ in DUPS}
for name in FILES:
    p = MONO / name
    s = p.read_text(encoding="utf-8")
    orig = s
    for target, keep in DUPS:
        if target in s:
            seen[target] += 1
            if seen[target] > keep:
                s = s.replace(target, "", 1)
                print(f"{name}: removed duplicate -> {target[:24]}...")
    if s != orig:
        p.write_text(s, encoding="utf-8", newline="\n")

# ---- connective substitutions ------------------------------------------
SUBS = [
    # em-dash used as a rhetorical pause -> colon or comma
    ("——这是", "。这是"),
    ("——它们", "。它们"),
    ("——机器改的是", "；机器改的是"),
    ("——蒸箱按重量", "。蒸箱按重量"),
    ("——闭合的是", "，闭合的是"),
    ("——机械定时、腔温闭环", "：机械定时、腔温闭环"),
    # mechanical causal openers
    ("因此机器要完成的链是", "机器要完成的链是"),
    ("因此两节点模型是一个", "两节点模型是一个"),
    ("因此第一节", "第一节"),
    ("因此表", "表"),
    ("因此本章", "本章"),
    # weak parallelism
    ("同时给出", "并给出"),
    ("同时进入", "一并进入"),
    ("同时读出", "一并读出"),
]

total = 0
for name in FILES:
    p = MONO / name
    s = p.read_text(encoding="utf-8")
    orig = s
    for a, b in SUBS:
        if a in s:
            n = s.count(a)
            s = s.replace(a, b)
            total += n
    if s != orig:
        p.write_text(s, encoding="utf-8", newline="\n")

print(f"\nconnective substitutions applied: {total}")
