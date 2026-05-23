"""카카오·SNS 링크 미리보기용 메타 태그 (og:image 등)."""

from __future__ import annotations

import html
import os

import streamlit as st


def _public_app_base_url() -> str:
    value = str(os.environ.get("SAJU_PUBLIC_APP_URL", "") or "").strip()
    if value:
        return value.rstrip("/")
    try:
        value = str(st.secrets.get("SAJU_PUBLIC_APP_URL", "") or "").strip()
    except Exception:
        value = ""
    return value.rstrip("/")


def inject_link_share_meta(*, description: str | None = None) -> None:
    """og:image·설명 메타를 주입합니다. Cloud에서는 스크린샷과 병행됩니다."""
    base = _public_app_base_url()
    title = "사주까기"
    desc = (
        description
        or "사주·궁합·대운·타로·주역·AI 상담 — 당신의 운명을 정밀하게 읽습니다."
    ).strip()
    if base:
        image = f"{base}/app/static/og-share.png"
        image_svg = f"{base}/app/static/og-share.svg"
    else:
        image = "/app/static/og-share.png"
        image_svg = "/app/static/og-share.svg"

    block = f"""
<meta name="description" content="{html.escape(desc, quote=True)}" />
<meta property="og:type" content="website" />
<meta property="og:title" content="{html.escape(title, quote=True)}" />
<meta property="og:description" content="{html.escape(desc, quote=True)}" />
<meta property="og:image" content="{html.escape(image, quote=True)}" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:image:alt" content="사주까기 — LUXURY SAJU INSIGHT" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{html.escape(title, quote=True)}" />
<meta name="twitter:description" content="{html.escape(desc, quote=True)}" />
<meta name="twitter:image" content="{html.escape(image, quote=True)}" />
<link rel="image_src" href="{html.escape(image_svg, quote=True)}" />
""".strip()
    st.markdown(block, unsafe_allow_html=True)
