"""Restore the original STEP1 banner (step01_hero.png, not v2)."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(r"C:\Users\Administrator\.cursor\projects\empty-window\assets\step01_hero.png")
FALLBACKS = [
    ROOT / "images" / "step01_hero.png",
    ROOT / "assets" / "step01_hero.png",
]
DST_MOOD = ROOT / "static" / "mood" / "step01_hero.png"
DST_IMAGES = ROOT / "images" / "step01_hero.png"


def main() -> int:
    src = SRC if SRC.is_file() else next((p for p in FALLBACKS if p.is_file()), None)
    if src is None:
        print("Original step01_hero.png not found.", file=sys.stderr)
        return 1
    DST_IMAGES.parent.mkdir(parents=True, exist_ok=True)
    DST_MOOD.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, DST_IMAGES)
    shutil.copyfile(src, DST_MOOD)
    print(f"restored: {DST_MOOD} <- {src} ({DST_MOOD.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
