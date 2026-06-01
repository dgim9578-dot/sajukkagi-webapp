"""Install home banner image into static/mood/step01_hero.png."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DST = ROOT / "static" / "mood" / "step01_hero.png"
SRC_CANDIDATES = [
    ROOT / "images" / "step01_hero.png",
    ROOT / "assets" / "step01_hero.png",
    Path(r"C:\Users\Administrator\.cursor\projects\empty-window\assets\step01_hero.png"),
]


def main() -> int:
    DST.parent.mkdir(parents=True, exist_ok=True)
    if DST.is_file() and DST.stat().st_size > 10_000:
        print(f"already installed: {DST} ({DST.stat().st_size} bytes)")
        return 0
    for src in SRC_CANDIDATES:
        if not src.is_file():
            continue
        shutil.copyfile(src, DST)
        print(f"installed: {DST} <- {src} ({DST.stat().st_size} bytes)")
        return 0
    print("source image not found; place step01_hero.png under assets/ or static/mood/", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
