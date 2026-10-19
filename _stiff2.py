"""Find every stiff paragraph with enough context to rewrite it."""
import re
from pathlib import Path

FILES = ["ch1.tex", "ch2.tex", "ch3.tex", "ch4.tex", "ch5.tex", "ch6.tex"]
out = []
for f in FILES:
    s = (Path("monograph") / f).read_text(encoding="utf-8")
    for idx, p in enumerate(re.split(r"\n\s*\n", s)):
        p = p.strip()
        if p.startswith("\\") or len(re.findall(r"[\u4e00-\u9fff]", p)) < 90:
            continue
        ends = p.count("。") + p.count("；")
        if ends == 0:
            continue
        dens = p.count("，") / ends
        if dens < 1.0:
            out.append((dens, f, idx, p))

out.sort()
print(f"stiff paragraphs (comma/sentence < 1.0): {len(out)}\n")
for dens, f, idx, p in out:
    cn = len(re.findall(r"[\u4e00-\u9fff]", p))
    print(f"--- {f}#{idx} dens={dens:.2f} chars={cn}")
    print(p[:200].replace("\n", " "))
    print()
