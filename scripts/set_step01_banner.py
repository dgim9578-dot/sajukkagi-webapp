"""홈 배너 이미지를 static/mood/step01_hero.png 로 설치 (--force 로 덮어쓰기)."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DST = ROOT / "static" / "mood" / "step01_hero.png"
DEFAULT_SOURCES = [
    ROOT / "images" / "step01_hero_v2.png",
    ROOT / "assets" / "step01_hero_v2.png",
    Path(r"C:\Users\Administrator\.cursor\projects\empty-window\assets\step01_hero_v2.png"),
    ROOT / "images" / "step01_hero.png",
    ROOT / "assets" / "step01_hero.png",
]


def install(src: Path, *, force: bool) -> int:
    if not src.is_file():
        print(f"not found: {src}", file=sys.stderr)
        return 1
    if src.stat().st_size < 5_000:
        print(f"file too small: {src}", file=sys.stderr)
        return 1
    DST.parent.mkdir(parents=True, exist_ok=True)
    if DST.is_file() and not force:
        if DST.stat().st_size >= 5_000 and DST.stat().st_mtime >= src.stat().st_mtime:
            print(f"skip (up to date): {DST}")
            return 0
    shutil.copyfile(src, DST)
    print(f"ok: {DST} <- {src} ({DST.stat().st_size} bytes)")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Install STEP1 home banner image")
    p.add_argument("source", nargs="?", help="Source image path (png/jpg/webp)")
    p.add_argument("--force", "-f", action="store_true", help="Always overwrite destination")
    args = p.parse_args()
    if args.source:
        return install(Path(args.source).expanduser().resolve(), force=True)
    for src in DEFAULT_SOURCES:
        if src.is_file():
            return install(src, force=args.force)
    print(
        "Usage: python scripts/set_step01_banner.py C:\\path\\to\\banner.png",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
