"""Page-by-page audit: figure size, caption length, whitespace, orphan floats."""
import re
from pathlib import Path

import fitz

doc = fitz.open("monograph/ACTS-MCDT.pdf")
print(f"pages: {len(doc)}\n")

rows = []
for i, page in enumerate(doc):
    imgs = page.get_images(full=True)
    txt = page.get_text().strip()
    blocks = [b for b in page.get_text("blocks") if b[4].strip()]
    maxy = max((b[3] for b in blocks), default=0)
    fill = maxy / page.rect.height if blocks else 0

    # image area fraction
    area = 0.0
    for im in page.get_image_info():
        r = fitz.Rect(im["bbox"])
        area += r.width * r.height
    frac = area / (page.rect.width * page.rect.height)

    rows.append((i + 1, len(imgs), frac, fill, len(txt)))

print("=== 页内图面积占比 > 55% 的页（图过大）===")
for pg, n, frac, fill, chars in rows:
    if frac > 0.55:
        print(f"  p{pg}: imgs={n} area={frac*100:.0f}% fill={fill*100:.0f}%")

print("\n=== 页内文字极少且有大图（图多字少）===")
for pg, n, frac, fill, chars in rows:
    if frac > 0.35 and chars < 700 and pg > 5:
        print(f"  p{pg}: imgs={n} area={frac*100:.0f}% chars={chars}")

print("\n=== 底部留白 > 30% 的页（排版空隙）===")
for pg, n, frac, fill, chars in rows:
    if fill < 0.70 and pg > 5 and frac < 0.05:
        print(f"  p{pg}: fill={fill*100:.0f}% chars={chars}")

# caption length distribution
tex = "\n".join(p.read_text(encoding="utf-8") for p in Path("monograph").glob("ch*.tex"))
caps = re.findall(r"\\caption\{(.+?)\}\s*\n", tex, flags=re.S)
lens = [len(re.findall(r"[\u4e00-\u9fff]", c)) for c in caps]
if lens:
    print(f"\n=== 图注长度: {len(lens)} 条, 均 {sum(lens)/len(lens):.0f} 字, "
          f"最长 {max(lens)}, 最短 {min(lens)} ===")
    long_caps = [(l, c[:70]) for l, c in zip(lens, caps) if l > 90]
    print(f"  过长(>90字): {len(long_caps)}")
    for l, c in long_caps[:5]:
        print(f"    {l}字: {c}")
