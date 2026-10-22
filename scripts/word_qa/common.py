"""Shared paths for local Word pagination checks."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCX = ROOT / "submit" / "20241334庄颂信息2402.docx"
OUTPUT_DIR = ROOT / "results" / "word_qa"


def write_json(name: str, data: object) -> Path:
    """Write a generated QA report under the ignored results directory."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / name
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return path
