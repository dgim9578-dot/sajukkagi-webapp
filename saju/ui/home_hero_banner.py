"""STEP1 홈 상단 배너 이미지 (static/mood/step01_hero.*)."""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

from mood_assets import mood_image_data_uri, resolve_mood_image

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_IMAGES_DIR = _PROJECT_ROOT / "images"
_MOOD_DIR = _PROJECT_ROOT / "static" / "mood"
_BANNER_STEM = "step01_hero"
_MOOD_DST = _MOOD_DIR / f"{_BANNER_STEM}.png"
# 사진 배너 — images/step01_hero_v2.png 우선
_PREFERRED_SOURCES: tuple[Path, ...] = (
    _IMAGES_DIR / "step01_hero_v2.png",
    _PROJECT_ROOT / "assets" / "step01_hero_v2.png",
    Path(
        r"C:\Users\Administrator\.cursor\projects\empty-window\assets\step01_hero_v2.png"
    ),
    _IMAGES_DIR / "step01_hero.png",
    _PROJECT_ROOT / "assets" / "step01_hero.png",
    Path(r"C:\Users\Administrator\.cursor\projects\empty-window\assets\step01_hero.png"),
)
_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def _clear_mood_cache() -> None:
    mood_image_data_uri.cache_clear()
    resolve_mood_image.cache_clear()


def _write_banner_bytes(data: bytes, *, ext: str = ".png") -> Path:
    _MOOD_DIR.mkdir(parents=True, exist_ok=True)
    for old in _MOOD_DIR.glob(f"{_BANNER_STEM}.*"):
        if old.suffix.lower() in _IMAGE_EXTS and old != _MOOD_DST:
            try:
                old.unlink()
            except OSError:
                pass
    dst = _MOOD_DST if ext.lower() == ".png" else _MOOD_DIR / f"{_BANNER_STEM}{ext.lower()}"
    dst.write_bytes(data)
    _clear_mood_cache()
    return dst


def save_step01_hero_upload(file_bytes: bytes, filename: str = "") -> Path | None:
    """업로드·교체용 — bytes 를 static/mood 에 저장."""
    if not file_bytes or len(file_bytes) < 5_000:
        return None
    ext = Path(str(filename or "")).suffix.lower()
    if ext not in _IMAGE_EXTS:
        ext = ".png"
    return _write_banner_bytes(file_bytes, ext=ext)


def _pick_largest_image_in_dir(folder: Path) -> Path | None:
    best: Path | None = None
    best_size = 5_000
    if not folder.is_dir():
        return None
    for src in folder.iterdir():
        if not src.is_file() or src.suffix.lower() not in _IMAGE_EXTS:
            continue
        try:
            size = src.stat().st_size
        except OSError:
            continue
        if size > best_size:
            best_size = size
            best = src
    return best


def preferred_banner_source() -> Path | None:
    """사진 배너 원본 — step01_hero_v2.png 우선."""
    for src in _PREFERRED_SOURCES:
        if src.is_file() and src.stat().st_size > 5_000:
            return src
    for folder in (_IMAGES_DIR, _PROJECT_ROOT / "assets"):
        if not folder.is_dir():
            continue
        for name in ("step01_hero_v2.png", "step01_hero_v2.jpg", "step01_hero_v2.webp"):
            exact = folder / name
            if exact.is_file() and exact.stat().st_size > 5_000:
                return exact
        for pattern in ("step01_hero_v2*", "step01_hero*"):
            matches = [
                p
                for p in folder.glob(pattern)
                if p.is_file() and p.suffix.lower() in _IMAGE_EXTS and p.stat().st_size > 5_000
            ]
            if matches:
                return max(matches, key=lambda p: p.stat().st_mtime)
        picked = _pick_largest_image_in_dir(folder)
        if picked is not None:
            return picked
    return None


def ensure_step01_hero_banner_file(*, force: bool = False) -> Path | None:
    """배너를 static/mood 에 동기화(표시는 원본 직접 읽기도 가능)."""
    src = preferred_banner_source()
    if src is None:
        return resolve_mood_image(_BANNER_STEM)
    existing = resolve_mood_image(_BANNER_STEM)
    if existing is not None and not force:
        try:
            if existing.stat().st_mtime >= src.stat().st_mtime:
                return existing
        except OSError:
            pass
    try:
        _write_banner_bytes(src.read_bytes(), ext=src.suffix.lower() or ".png")
    except OSError:
        return existing
    return resolve_mood_image(_BANNER_STEM)


def step01_hero_banner_img_src() -> str | None:
    """data URI 우선(모바일·갤럭시 캐시 안정), 없으면 /app/static."""
    ensure_step01_hero_banner_file(force=True)
    uri = mood_image_data_uri(_BANNER_STEM)
    if uri:
        return uri
    src = preferred_banner_source()
    if src is None:
        return None
    try:
        mime, _ = mimetypes.guess_type(src.name)
        mime = mime or "image/png"
        data = base64.b64encode(src.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{data}"
    except OSError:
        return None


def step01_hero_banner_html() -> str | None:
    """이미지 배너 HTML — step01_hero_v2 상단 고정용 #saju-home-hero-top."""
    src = step01_hero_banner_img_src()
    if not src:
        return None
    return f"""
<div id="saju-home-hero-top" class="saju-home-hero-banner saju-landing-hero--photo" role="banner">
  <figure class="saju-home-hero-banner__figure" aria-label="사주까기 럭셔리 사주풀이">
    <img src="{src}" alt="사주까기 — 럭셔리 사주풀이" loading="eager" decoding="async" fetchpriority="high" />
  </figure>
</div>
""".strip()
