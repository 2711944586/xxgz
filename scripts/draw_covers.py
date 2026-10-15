# -*- coding: utf-8 -*-
"""Print-size the three original posters. Do not redraw or restyle them."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "monograph" / "figures"

DPI = 400
W = int(round(210 / 25.4 * DPI))  # 3307
H = int(round(297 / 25.4 * DPI))  # 4677

JOBS = (
    ("_src_cover.png", "cover.png"),
    ("_src_back.png", "back.png"),
    ("_src_bg.png", "bg.png"),
)


def print_size(src: Path, dest: Path) -> None:
    im = Image.open(src).convert("RGB")
    if im.size != (W, H):
        im = im.resize((W, H), Image.Resampling.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, "PNG", dpi=(DPI, DPI), compress_level=9, optimize=True)
    print(dest.name, im.size, dest.stat().st_size)


def main() -> None:
    for src_name, dest_name in JOBS:
        src = FIG / src_name
        if not src.exists():
            raise SystemExit(f"missing original {src}")
        print_size(src, FIG / dest_name)


if __name__ == "__main__":
    main()
