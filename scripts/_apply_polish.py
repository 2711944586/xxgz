# -*- coding: utf-8 -*-
"""Apply validated sentence-level polish proposals to the monograph chapters.

Each proposal is checked before it is applied: the `old` text must occur
exactly once in its file. Anything that fails the check is printed and skipped,
never guessed at.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "monograph"


def hanzi(s: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", s))


def main(path: str, dry: bool) -> None:
    items = json.loads(Path(path).read_text(encoding="utf-8"))
    cache: dict[str, str] = {}
    applied = 0
    skipped = []
    for it in items:
        name = it["file"]
        p = BOOK / name
        text = cache.get(name) or p.read_text(encoding="utf-8")
        old, new = it["old"], it["new"]
        n = text.count(old)
        if n != 1:
            skipped.append((name, it.get("line_hint"), n, old[:40]))
            continue
        cache[name] = text.replace(old, new, 1)
        applied += 1
        print(f"OK   {name}:{it.get('line_hint')}  {hanzi(old)}->{hanzi(new)} 汉字")
    if dry:
        print(f"\n[dry] would apply {applied}, skip {len(skipped)}")
        return
    for name, text in cache.items():
        (BOOK / name).write_text(text, encoding="utf-8")
    print(f"\napplied {applied}, skipped {len(skipped)}")
    for s in skipped:
        print("SKIP", s)


if __name__ == "__main__":
    main(sys.argv[1], dry="--dry" in sys.argv)
