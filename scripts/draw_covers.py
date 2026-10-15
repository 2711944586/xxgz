# -*- coding: utf-8 -*-
"""Remake cover, back and watermark at A4 400 DPI with vector-quality TTF."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "monograph" / "figures"
FONT_DIR = Path(r"C:\Windows\Fonts")

DPI = 400
W = int(round(210 / 25.4 * DPI))  # 3307
H = int(round(297 / 25.4 * DPI))  # 4677
NAVY = (22, 48, 86)
NAVY2 = (28, 64, 112)
BLUE = (46, 110, 168)
STEEL = (70, 96, 128)
INK = (28, 36, 48)
MUTED = (96, 108, 122)
WHITE = (255, 255, 255)
PANEL = (248, 252, 255)


def mm(x: float) -> int:
    return int(round(x / 25.4 * DPI))


def load_font(name: str, size_pt: float, index: int = 0) -> ImageFont.FreeTypeFont:
    path = FONT_DIR / name
    px = max(8, int(round(size_pt * DPI / 72.0)))
    try:
        return ImageFont.truetype(str(path), px, index=index)
    except OSError:
        return ImageFont.truetype(str(FONT_DIR / "simhei.ttf"), px)


def font_song(size_pt: float) -> ImageFont.FreeTypeFont:
    return load_font("STZHONGS.TTF", size_pt)


def font_hei(size_pt: float) -> ImageFont.FreeTypeFont:
    return load_font("simhei.ttf", size_pt)


def font_msyh(size_pt: float, bold: bool = False) -> ImageFont.FreeTypeFont:
    return load_font("msyhbd.ttc" if bold else "msyh.ttc", size_pt, index=0)


def font_kai(size_pt: float) -> ImageFont.FreeTypeFont:
    return load_font("STKAITI.TTF", size_pt)


def sky_bg() -> Image.Image:
    yy = np.linspace(0.0, 1.0, H)[:, None]
    top = np.array([252.0, 254.0, 255.0])
    mid = np.array([236.0, 245.0, 252.0])
    bot = np.array([220.0, 234.0, 246.0])
    t = yy[:, 0]
    col = np.empty((H, 3), dtype=np.float64)
    m = t < 0.42
    u = np.clip(t / 0.42, 0.0, 1.0)
    v = np.clip((t - 0.42) / 0.58, 0.0, 1.0)
    col[m] = (1.0 - u[m])[:, None] * top + u[m][:, None] * mid
    col[~m] = (1.0 - v[~m])[:, None] * mid + v[~m][:, None] * bot
    arr = np.broadcast_to(col[:, None, :].astype(np.uint8), (H, W, 3)).copy()
    return Image.fromarray(arr, mode="RGB")


def paste_crop(dst: Image.Image, src_path: Path, box: tuple[int, int, int, int], dest_xy: tuple[int, int], dest_size: tuple[int, int]) -> None:
    src = Image.open(src_path).convert("RGB")
    crop = src.crop(box)
    crop = crop.resize(dest_size, Image.Resampling.LANCZOS)
    crop = crop.filter(ImageFilter.UnsharpMask(radius=1.5, percent=150, threshold=2))
    crop = ImageEnhance.Contrast(crop).enhance(1.06)
    crop = ImageEnhance.Color(crop).enhance(1.05)
    # Feather the top and left so the crop meets the sky.
    mask = Image.new("L", dest_size, 255)
    md = ImageDraw.Draw(mask)
    fade = max(8, dest_size[0] // 28)
    for i in range(fade):
        a = int(255 * (i / fade))
        md.rectangle([0, i, dest_size[0], i], fill=min(255, a + 40) if i < fade // 3 else 255)
        md.line([(i, 0), (i, dest_size[1])], fill=int(180 + 75 * (i / fade)))
    dst.paste(crop, dest_xy, mask)


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def draw_center(draw: ImageDraw.ImageDraw, text: str, y: int, font: ImageFont.FreeTypeFont, fill, stroke: int = 0, stroke_fill=None) -> None:
    tw, _ = text_size(draw, text, font)
    kw = {"stroke_width": stroke, "stroke_fill": stroke_fill} if stroke else {}
    draw.text(((W - tw) // 2, y), text, font=font, fill=fill, **kw)


def draw_mountain(draw: ImageDraw.ImageDraw, x: int, y: int, s: int) -> None:
    c1, c2, c3 = (36, 92, 150), (24, 70, 122), (18, 54, 98)
    draw.polygon([(x, y + s), (x + int(0.38 * s), y + int(0.18 * s)), (x + int(0.72 * s), y + s)], fill=c3)
    draw.polygon([(x + int(0.22 * s), y + s), (x + int(0.55 * s), y), (x + int(0.92 * s), y + s)], fill=c1)
    draw.polygon([(x + int(0.58 * s), y + s), (x + int(0.86 * s), y + int(0.28 * s)), (x + int(1.18 * s), y + s)], fill=c2)


def hline(draw: ImageDraw.ImageDraw, y: int, x0: int, x1: int, fill=NAVY, width: int = 2) -> None:
    draw.line([(x0, y), (x1, y)], fill=fill, width=width)


def make_cover() -> Image.Image:
    img = sky_bg()
    paste_crop(
        img,
        FIG / "_src_cover.png",
        box=(268, 552, 1028, 1210),
        dest_xy=(mm(58), mm(118)),
        dest_size=(W - mm(58), mm(148)),
    )
    draw = ImageDraw.Draw(img)
    # cover leftover original side labels that sit on the tank
    draw.rectangle([W - mm(42), mm(114), W, mm(222)], fill=(232, 243, 252))

    # top logo
    draw_mountain(draw, mm(16), mm(14), mm(16))
    draw.text((mm(38), mm(15)), "东北大学", font=font_song(18), fill=NAVY)
    draw.text((mm(38), mm(24.2)), "NORTHEASTERN UNIVERSITY", font=font_msyh(7.2), fill=STEEL)

    right = [
        ("科技赋能 生活", 8.2, NAVY),
        ("感知 连接 未来", 8.2, NAVY2),
        ("SENSING INTELLIGENCE", 6.4, MUTED),
        ("FOR A BETTER FUTURE", 6.4, MUTED),
    ]
    ry = mm(14)
    for text, size, color in right:
        font = font_hei(size) if size > 7 else font_msyh(size)
        tw, th = text_size(draw, text, font)
        draw.text((W - mm(16) - tw, ry), text, font=font, fill=color)
        ry += th + mm(1.1)

    # main title
    draw_center(draw, "信息感知课程报告", mm(42), font_song(34), NAVY)
    hline(draw, mm(58.5), mm(62), W - mm(62), fill=BLUE, width=max(2, mm(0.35)))
    draw_center(draw, "INFORMATION PERCEPTION COURSE REPORT", mm(60.5), font_msyh(8.4), STEEL)

    bar_x, bar_y = mm(18), mm(76)
    draw.rounded_rectangle([bar_x, bar_y, bar_x + mm(2.4), bar_y + mm(28)], radius=mm(0.6), fill=NAVY2)
    draw.text((mm(24), mm(75.5)), "基于信息感知的智能蒸烤一体机", font=font_hei(16.5), fill=NAVY)
    draw.text((mm(24), mm(85.5)), "ACTS-MCDT", font=font_msyh(14, bold=True), fill=NAVY2)
    draw.text(
        (mm(24), mm(96)),
        "多尺度界面物理、对偶信息控制与测量隔离的安全执行",
        font=font_kai(11.5),
        fill=STEEL,
    )

    # left keywords
    kw = [("AI  SENSING", mm(132)), ("STEAM  BAKING", mm(140)), ("CONTROL  SAFETY", mm(148))]
    for text, y in kw:
        draw.text((mm(16), y), text, font=font_msyh(8.0, bold=True), fill=BLUE)

    # left stack
    layers = [
        ("多尺度界面", (186, 214, 236)),
        ("蒸汽流场", (154, 194, 228)),
        ("热对流", (118, 168, 214)),
        ("信息感知", (78, 136, 196)),
        ("对偶控制", (42, 98, 168)),
    ]
    sx0, sy0 = mm(16), mm(168)
    lw, lh, gap = mm(42), mm(9.2), mm(2.2)
    for i, (label, fill) in enumerate(layers):
        y = sy0 + i * (lh + gap)
        inset = i * mm(1.6)
        draw.rounded_rectangle([sx0 + inset, y, sx0 + lw, y + lh], radius=mm(1.1), fill=fill)
        ink = WHITE if i >= 2 else NAVY
        font = font_hei(8.2)
        tw, th = text_size(draw, label, font)
        draw.text((sx0 + inset + (lw - inset - tw) // 2, y + (lh - th) // 2 - mm(0.4)), label, font=font, fill=ink)

    # mini traces
    cx0, cy0 = mm(16), mm(226)
    cw, ch = mm(46), mm(22)
    draw.rounded_rectangle([cx0, cy0, cx0 + cw, cy0 + ch], radius=mm(1.2), fill=WHITE, outline=BLUE, width=2)
    # three polylines
    traces = [
        [(0.05, 0.72), (0.22, 0.58), (0.40, 0.50), (0.62, 0.38), (0.82, 0.28), (0.95, 0.22)],
        [(0.05, 0.80), (0.25, 0.70), (0.48, 0.62), (0.70, 0.55), (0.95, 0.48)],
        [(0.05, 0.55), (0.30, 0.48), (0.55, 0.42), (0.78, 0.40), (0.95, 0.38)],
    ]
    colors = [(30, 90, 160), (40, 150, 150), (180, 90, 50)]
    for pts, col in zip(traces, colors):
        xy = [(cx0 + int(p[0] * cw), cy0 + int(p[1] * ch)) for p in pts]
        draw.line(xy, fill=col, width=max(2, mm(0.45)))
    legend = [("温度 ℃", (30, 90, 160)), ("湿度 %", (40, 150, 150)), ("压力 kPa", (180, 90, 50))]
    lx = cx0 + mm(1.2)
    ly = cy0 + ch + mm(1.4)
    for lab, col in legend:
        draw.rectangle([lx, ly + mm(1.1), lx + mm(4), ly + mm(3.2)], fill=col)
        draw.text((lx + mm(5.2), ly), lab, font=font_msyh(6.2), fill=INK)
        lx += mm(16)

    # right vertical labels
    vlabels = ["感知", "建模", "控制", "测量隔离", "安全执行"]
    vx = W - mm(14)
    vy = mm(124)
    vfont = font_hei(9.0)
    for lab in vlabels:
        tw, th = text_size(draw, lab, vfont)
        draw.rounded_rectangle(
            [vx - tw - mm(2.4), vy - mm(0.8), vx + mm(1.6), vy + th + mm(0.8)],
            radius=mm(1.0),
            fill=(244, 249, 253),
        )
        draw.text((vx - tw, vy), lab, font=vfont, fill=NAVY2)
        vy += th + mm(4.4)

    # bottom info card
    card = [mm(14), mm(248), mm(108), mm(281)]
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle(card, radius=mm(2.0), fill=(255, 255, 255, 245))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(card, radius=mm(2.0), outline=NAVY2, width=2)
    draw.rectangle([card[0], card[1] + mm(3), card[0] + mm(2.0), card[3] - mm(3)], fill=NAVY2)

    info = [
        ("课程名称", "信息感知"),
        ("报告题目", "智能蒸烤一体机"),
        ("学    号", "20241334"),
        ("姓    名", "庄颂"),
        ("班    级", "信息2402"),
        ("提交日期", "2026年11月"),
    ]
    iy = mm(251)
    kfont, vfont2 = font_hei(9.4), font_msyh(9.4)
    for k, v in info:
        draw.text((mm(20), iy), f"{k}：", font=kfont, fill=NAVY)
        draw.text((mm(48), iy), v, font=vfont2, fill=INK)
        iy += mm(4.7)

    draw_center(draw, "沈阳 · 东北大学", mm(284.5), font_song(12), NAVY)
    hline(draw, mm(283.6), mm(78), mm(96), fill=NAVY, width=2)
    hline(draw, mm(283.6), W - mm(96), W - mm(78), fill=NAVY, width=2)
    draw_center(draw, "NORTHEASTERN UNIVERSITY  ·  SHENYANG", mm(291.2), font_msyh(7.0), STEEL)
    return img


def make_back() -> Image.Image:
    img = sky_bg()
    paste_crop(
        img,
        FIG / "_src_back.png",
        box=(0, 780, 1055, 1368),
        dest_xy=(0, mm(152)),
        dest_size=(W, mm(112)),
    )
    draw = ImageDraw.Draw(img)
    draw_center(draw, "信息感知  智能生活", mm(108), font_song(32), NAVY)
    hline(draw, mm(126), mm(58), W - mm(58), fill=BLUE, width=max(2, mm(0.4)))
    draw_center(draw, "SENSING INFORMATION FOR A SMARTER LIFE", mm(130), font_msyh(9.0), STEEL)
    draw_center(draw, "东北大学", mm(276), font_song(16), NAVY)
    hline(draw, mm(274.8), mm(82), mm(98), fill=NAVY, width=2)
    hline(draw, mm(274.8), W - mm(98), W - mm(82), fill=NAVY, width=2)
    draw_center(draw, "NORTHEASTERN UNIVERSITY", mm(286), font_msyh(8.0), STEEL)
    return img


def make_bg(cover: Image.Image) -> Image.Image:
    base = cover.copy()
    base = ImageEnhance.Color(base).enhance(0.55)
    base = ImageEnhance.Contrast(base).enhance(0.72)
    base = ImageEnhance.Brightness(base).enhance(1.18)
    base = base.filter(ImageFilter.GaussianBlur(radius=1.2))
    return base


def save_png(img: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "PNG", optimize=True, dpi=(DPI, DPI))
    print("wrote", path, img.size)


def main() -> None:
    cover = make_cover()
    back = make_back()
    bg = make_bg(cover)
    save_png(cover, FIG / "cover.png")
    save_png(back, FIG / "back.png")
    save_png(bg, FIG / "bg.png")


if __name__ == "__main__":
    main()
