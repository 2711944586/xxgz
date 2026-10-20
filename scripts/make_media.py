"""Encode the captured frame sequences into animated GIFs for PDF and Word.

GIF is the only animated format both a PDF (via the `animate` package) and a
Word document can play without a video player, so the sequences are encoded
twice: a large GIF for the report and a compact one for embedding.

    python scripts/make_media.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "results" / "figures" / "demo"
FRAMES = FIG / "_frames"

# name -> (width, frame duration ms, loop)
SPECS = {
    "anim_explode": (860, 85, 0),
}


def frames_of(name: str) -> list[Path]:
    return sorted((FRAMES / name).glob("*.png"))


def build_gif(name: str, width: int, duration: int) -> Path | None:
    """Assemble one GIF, downscaled for embedding and quantised to 128 colours."""
    files = frames_of(name)
    if not files:
        print(f"  {name}: no frames")
        return None

    images = []
    for path in files:
        img = Image.open(path).convert("RGB")
        ratio = width / img.width
        img = img.resize((width, round(img.height * ratio)), Image.LANCZOS)
        # a light dither keeps the thermal gradient smooth without huge files
        images.append(img.quantize(colors=128, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG))

    out = FIG / f"{name}.gif"
    images[0].save(
        out,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=0,
        optimize=True,
        disposal=1,
    )
    size_mb = out.stat().st_size / 1e6
    print(f"  {name}.gif  {width}px  {len(images)} frames  {size_mb:.2f} MB")
    return out


def build_mp4(name: str) -> None:
    """Also produce an MP4 when ffmpeg is present (better quality for slides)."""
    if not shutil.which("ffmpeg"):
        return
    files = frames_of(name)
    if not files:
        return
    out = FIG / f"{name}.mp4"
    pattern = str(FRAMES / name / "%03d.png")
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-framerate", "11", "-i", pattern,
            "-vf", "scale=760:-2:flags=lanczos",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(out),
        ],
        check=False,
    )
    if out.exists():
        print(f"  {name}.mp4  {out.stat().st_size / 1e6:.2f} MB")


# The animate package embeds every frame uncompressed as a PDF object, so a
# full-resolution sequence turns a 22-frame clip into 25 MB. Animations are
# therefore re-encoded once at print size, which is all a 160 mm text column
# can resolve anyway.
PRINT_WIDTH = 560


def build_print_sequence(name: str, width: int = PRINT_WIDTH) -> Path:
    """Write a downscaled JPEG sequence for the animate package.

    PNG frames made a 22-frame clip weigh 25 MB inside the PDF because animate
    stores each frame as its own object. JPEG at print resolution cuts that by
    roughly an order of magnitude with no visible loss at 560 px.
    """
    out_dir = FIG / name
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    files = frames_of(name)
    # animate wants six-digit numbering starting at 000000, and it reads PDF,
    # PNG or EPS frames (not JPEG), so each frame becomes a single-page PDF.
    for i, path in enumerate(files):
        img = Image.open(path).convert("RGB")
        ratio = width / img.width
        img = img.resize((width, round(img.height * ratio)), Image.LANCZOS)
        img.save(out_dir / f"f{i:06d}.pdf", "PDF", resolution=150.0)
    total = sum(f.stat().st_size for f in out_dir.glob("*.pdf")) / 1e6
    print(f"  {name}: {len(files)} frames, {width}px, {total:.2f} MB")
    return out_dir


def main() -> None:
    if not FRAMES.exists():
        raise SystemExit("run scripts/capture-demo.cjs first")
    print("encoding animations:")
    built = []
    for name, (width, duration, _loop) in SPECS.items():
        gif = build_gif(name, width, duration)
        if gif:
            built.append(gif)
            build_mp4(name)
            build_print_sequence(name)

    manifest_path = FIG / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["media"] = [
            {
                "name": gif.stem,
                "gif": str(gif.relative_to(ROOT)),
                "frames": len(frames_of(gif.stem)),
            }
            for gif in built
        ]
        manifest_path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"\n{len(built)} animations -> {FIG.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
