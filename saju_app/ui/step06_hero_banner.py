"""STEP6 오늘의 운세 — 상단 배너 이미지 (images/오늘의 운세.png)."""

from __future__ import annotations

import base64
import html
import mimetypes
from functools import lru_cache
from pathlib import Path

import streamlit as st

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_BANNER_CANDIDATES: tuple[Path, ...] = (
    _PROJECT_ROOT / "images" / "오늘의 운세.png",
    _PROJECT_ROOT / "images" / "오늘의 운세.webp",
    _PROJECT_ROOT / "images" / "오늘의 운세.jpg",
)


@lru_cache(maxsize=1)
def _resolve_step06_banner_path() -> Path | None:
    for path in _BANNER_CANDIDATES:
        if path.is_file() and path.stat().st_size > 0:
            return path
    return None


@lru_cache(maxsize=1)
def step06_hero_banner_src() -> str | None:
    path = _resolve_step06_banner_path()
    if path is None:
        return None
    mime, _ = mimetypes.guess_type(path.name)
    mime = mime or "image/png"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def render_step06_hero_banner(**_kwargs) -> None:
    """STEP6 상단 — ``images/오늘의 운세.png`` 배너."""
    src = step06_hero_banner_src()
    with st.container(key="step6_hero_banner"):
        if not src:
            st.caption("배너 이미지를 찾을 수 없습니다. `images/오늘의 운세.png` 를 확인해 주세요.")
            return
        st.markdown(
            f'<figure class="saju-mood-step6-hero" aria-hidden="false">'
            f'<img src="{src}" alt="{html.escape("오늘의 운세")}" '
            f'loading="lazy" decoding="async" />'
            f"</figure>",
            unsafe_allow_html=True,
        )
