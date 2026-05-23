"""카카오·SNS 링크 미리보기용 메타 태그 (og:image 등)."""

from __future__ import annotations

import html
import os
import streamlit as st

# GitHub raw — Streamlit Cloud 스크린샷 대신 카카오가 직접 가져올 수 있는 배너
_DEFAULT_GITHUB_RAW_OG = (
    "https://raw.githubusercontent.com/dgim9578-dot/sajukkagi-webapp/main/static/og-share.png"
)


def _setting(name: str, default: str = "") -> str:
    value = str(os.environ.get(name, "") or "").strip()
    if value:
        return value
    try:
        return str(st.secrets.get(name, default) or default).strip()
    except Exception:
        return str(default or "").strip()


def _public_app_base_url() -> str:
    value = _setting("SAJU_PUBLIC_APP_URL")
    return value.rstrip("/")


def _og_image_url() -> str:
    """공유 미리보기 배너 URL (카카오·SNS 크롤러용, 절대 경로)."""
    custom = _setting("SAJU_OG_IMAGE_URL")
    if custom:
        return custom
    base = _public_app_base_url()
    if base:
        return f"{base}/app/static/og-share.png"
    return _DEFAULT_GITHUB_RAW_OG


def inject_link_share_meta(*, description: str | None = None) -> None:
    """og:image·설명 메타를 주입합니다."""
    base = _public_app_base_url()
    image = _og_image_url()
    title = "사주까기 · 무료 사주풀이"
    desc = (
        description
        or "무료 사주풀이 — 사주·궁합·대운·타로·주역·AI 상담"
    ).strip()
    image_alt = "사주까기 — 무료 사주풀이 · LUXURY SAJU INSIGHT"
    page_url = base or ""

    og_url_line = ""
    if page_url:
        og_url_line = f'<meta property="og:url" content="{html.escape(page_url, quote=True)}" />'

    block = f"""
<meta name="description" content="{html.escape(desc, quote=True)}" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="사주까기" />
<meta property="og:title" content="{html.escape(title, quote=True)}" />
<meta property="og:description" content="{html.escape(desc, quote=True)}" />
<meta property="og:image" content="{html.escape(image, quote=True)}" />
<meta property="og:image:secure_url" content="{html.escape(image, quote=True)}" />
<meta property="og:image:type" content="image/png" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:image:alt" content="{html.escape(image_alt, quote=True)}" />
{og_url_line}
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{html.escape(title, quote=True)}" />
<meta name="twitter:description" content="{html.escape(desc, quote=True)}" />
<meta name="twitter:image" content="{html.escape(image, quote=True)}" />
""".strip()
    st.markdown(block, unsafe_allow_html=True)
