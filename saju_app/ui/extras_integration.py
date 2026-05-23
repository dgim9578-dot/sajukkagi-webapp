"""streamlit-extras 연동(미설치 시 무시).

`streamlit-custom-components`는 단일 패키지명이 아니라, 보통
`streamlit-components-v1` + 공식 component 템플릿으로 iframe 컴포넌트를 빌드하는 흐름입니다.
별도 위젯이 필요하면 그때 전용 모듈을 추가하세요.
"""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from typing import Any

import streamlit as st


def apply_global_streamlit_extras() -> None:
    """앱 전역에 한 번: ``st.metric`` 카드 스타일(골드 액센트)."""
    try:
        from streamlit_extras.metric_cards import style_metric_cards
    except ImportError:
        return
    try:
        import inspect

        sig = inspect.signature(style_metric_cards)
        kwargs: dict[str, Any] = {}
        if "border_left_color" in sig.parameters:
            kwargs["border_left_color"] = "#D4AF37"
        if "border_color" in sig.parameters:
            kwargs["border_color"] = "#C9A227"
        if "box_shadow" in sig.parameters:
            kwargs["box_shadow"] = True
        style_metric_cards(**kwargs)
    except Exception:
        try:
            style_metric_cards()
        except Exception:
            pass


@contextlib.contextmanager
def fortune_strip_stylable() -> Iterator[None]:
    """STEP1 운세 스트립: 골드 라인·라운드(미설치 시 일반 컨텍스트)."""
    try:
        from streamlit_extras.stylable_container import stylable_container
    except ImportError:
        yield
        return
    try:
        with stylable_container(
            key="saju_extras_fortune_strip",
            css_styles="""
[data-testid="stVerticalBlock"] > div {
    border: 1px solid rgba(212, 175, 55, 0.28);
    border-radius: 16px;
    padding: 0.35rem 0.5rem 0.5rem;
    background: rgba(255, 255, 255, 0.04);
}
@media (prefers-color-scheme: light) {
  [data-testid="stVerticalBlock"] > div {
    background: rgba(255, 255, 255, 0.45);
  }
}
""",
        ):
            yield
    except Exception:
        yield


_COLOR_NAME_TO_DIVIDER: dict[str, str] = {
    "light-blue-70": "blue",
    "orange-70": "orange",
    "blue-green-70": "green",
    "blue-70": "blue",
    "violet-70": "violet",
    "red-70": "red",
    "green-70": "green",
    "yellow-80": "yellow",
}


def render_colored_header_or_fallback(
    *,
    label: str,
    description: str,
    color_name: str = "orange-70",
) -> None:
    """색 구분선이 있는 섹션 제목 — Streamlit ``st.header(..., divider=...)`` 사용.

    ``streamlit_extras.colored_header`` 는 호출 시마다 폐기 경고 박스를 띄우므로 사용하지 않습니다.
    """
    divider = _COLOR_NAME_TO_DIVIDER.get(str(color_name or "").strip(), "orange")
    try:
        st.header(label, divider=divider)
    except TypeError:
        st.subheader(label)
    if description:
        st.caption(description)
