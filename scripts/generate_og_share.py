"""카카오·SNS용 og-share.png (1200×630) — 홈 히어로 배너에서 생성.

``python scripts/generate_og_share.py``
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from saju.ui.og_share_sync import build_og_share_from_path, og_share_output_path, sync_og_share_from_hero
from saju.ui.home_hero_banner import preferred_banner_source, ensure_step01_hero_banner_file
from mood_assets import resolve_mood_image


def main() -> int:
    ensure_step01_hero_banner_file(force=True)
    out = sync_og_share_from_hero(force=True)
    if out is not None:
        print(f"OK: {out}")
        print(f"cache version: ", end="")
        from saju.ui.og_share_sync import og_share_cache_version

        print(og_share_cache_version())
        return 0

    src = preferred_banner_source() or resolve_mood_image("step01_hero")
    if src is None:
        print("히어로 배너 원본 없음 — images/step01_hero_v2.png 를 추가하세요.")
        return 1
    built = build_og_share_from_path(src, og_share_output_path())
    if built is None:
        print("pip install Pillow 후 다시 실행하세요.")
        return 1
    print(f"OK: {built}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
