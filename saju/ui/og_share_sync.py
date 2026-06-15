"""카카오·SNS 링크 미리보기용 og-share.png — 홈 히어로 배너에서 1200×630 생성."""

from __future__ import annotations

import hashlib
from pathlib import Path

_OG_W = 1200
_OG_H = 630


def og_share_output_path(project_root: Path | None = None) -> Path:
    root = project_root or Path(__file__).resolve().parents[2]
    return root / "static" / "og-share.png"


def og_share_cache_version(*, project_root: Path | None = None) -> str:
    """og:image URL 쿼리 — 카카오 캐시 무효화용."""
    root = project_root or Path(__file__).resolve().parents[2]
    parts: list[str] = []
    og = og_share_output_path(root)
    if og.is_file():
        try:
            parts.append(str(int(og.stat().st_mtime)))
            parts.append(str(og.stat().st_size))
        except OSError:
            pass
    try:
        from saju.ui.home_hero_banner import preferred_banner_source

        hero = preferred_banner_source()
        if hero is not None and hero.is_file():
            parts.append(str(int(hero.stat().st_mtime)))
            parts.append(str(hero.stat().st_size))
    except Exception:
        pass
    if not parts:
        return "hero-v2"
    return hashlib.md5("-".join(parts).encode("utf-8")).hexdigest()[:12]


def _crop_cover(img, *, width: int, height: int):
    from PIL import Image

    iw, ih = img.size
    target_ratio = width / height
    src_ratio = iw / ih if ih else target_ratio
    if src_ratio > target_ratio:
        new_w = max(1, int(ih * target_ratio))
        left = max(0, (iw - new_w) // 2)
        box = (left, 0, left + new_w, ih)
    else:
        new_h = max(1, int(iw / target_ratio))
        top = max(0, (ih - new_h) // 4)
        box = (0, top, iw, min(ih, top + new_h))
    cropped = img.crop(box)
    return cropped.resize((width, height), Image.Resampling.LANCZOS)


def build_og_share_from_path(src: Path, out: Path | None = None) -> Path | None:
    """히어로 원본 → og-share.png (1200×630 center crop)."""
    if not src.is_file() or src.stat().st_size < 5_000:
        return None
    try:
        from PIL import Image
    except ImportError:
        return None
    destination = out or og_share_output_path()
    try:
        with Image.open(src) as raw:
            img = _crop_cover(raw.convert("RGB"), width=_OG_W, height=_OG_H)
        destination.parent.mkdir(parents=True, exist_ok=True)
        img.save(destination, "PNG", optimize=True)
        return destination
    except OSError:
        return None


def sync_og_share_from_hero(*, force: bool = False) -> Path | None:
    """홈 히어로 배너와 동기화 — og-share.png 갱신."""
    from saju.ui.home_hero_banner import preferred_banner_source
    from mood_assets import resolve_mood_image

    src = preferred_banner_source()
    if src is None:
        src = resolve_mood_image("step01_hero")
    if src is None:
        return og_share_output_path() if og_share_output_path().is_file() else None

    out = og_share_output_path()
    if not force and out.is_file():
        try:
            if out.stat().st_mtime >= src.stat().st_mtime:
                return out
        except OSError:
            pass
    return build_og_share_from_path(src, out)
