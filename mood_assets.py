"""Resolve mood illustration files under static/mood/."""

from __future__ import annotations

import base64
import mimetypes
from functools import lru_cache
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent
MOOD_DIR = _PROJECT_ROOT / "static" / "mood"
_EXTENSIONS: tuple[str, ...] = (".webp", ".png", ".jpg", ".jpeg")


@lru_cache(maxsize=128)
def resolve_mood_image(slug: str) -> Path | None:
    """Return path for ``slug`` if ``static/mood/{slug}.webp|png|...`` exists."""
    key = str(slug or "").strip().lower()
    if not key or "/" in key or "\\" in key or ".." in key:
        return None
    for ext in _EXTENSIONS:
        path = MOOD_DIR / f"{key}{ext}"
        if path.is_file():
            return path
    return None


@lru_cache(maxsize=128)
def mood_image_data_uri(slug: str) -> str | None:
    path = resolve_mood_image(slug)
    if path is None:
        return None
    mime, _ = mimetypes.guess_type(path.name)
    if not mime:
        mime = "image/png"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def list_mood_slugs() -> list[str]:
    """Installed mood files (slug without extension), sorted."""
    if not MOOD_DIR.is_dir():
        return []
    seen: set[str] = set()
    for path in sorted(MOOD_DIR.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in _EXTENSIONS:
            continue
        seen.add(path.stem.lower())
    return sorted(seen)
