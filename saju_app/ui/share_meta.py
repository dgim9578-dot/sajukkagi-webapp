"""카카오·SNS 링크 미리보기용 메타 태그 (og:image 등)."""

from __future__ import annotations

import html
import json
import os
from pathlib import Path

import streamlit as st

# GitHub Pages / raw — 카카오 공유 디버거·크롤러용 (Streamlit·jsDelivr URL 은 디버거 거부)
_DEFAULT_OG_HERO = (
    "https://raw.githubusercontent.com/dgim9578-dot/sajukkagi-webapp/main/images/step01_hero_v2.png"
)
_DEFAULT_SHARE_PAGE = (
    "https://dgim9578-dot.github.io/sajukkagi-webapp/share-preview.html"
)
_OG_IMAGE_ALT = "사주까기 — 럭셔리 사주풀이 · 무료 사주풀이"


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


def _og_cache_bust() -> str:
    try:
        from saju.ui.og_share_sync import og_share_cache_version

        return og_share_cache_version()
    except Exception:
        og = Path(__file__).resolve().parents[2] / "static" / "og-share.png"
        if og.is_file():
            try:
                return str(int(og.stat().st_mtime))
            except OSError:
                pass
        return "hero-v2"


def _with_og_cache_bust(url: str) -> str:
    url = str(url or "").strip()
    if not url:
        return url
    token = _og_cache_bust()
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}v={token}"


def _og_image_url() -> str:
    """공유 미리보기 배너 URL (카카오·SNS 크롤러용, 절대 경로)."""
    custom = _setting("SAJU_OG_IMAGE_URL")
    if custom:
        return _with_og_cache_bust(custom)
    # jsDelivr — Streamlit Cloud 는 크롤러에 og HTML 을 주지 않음
    return _with_og_cache_bust(_DEFAULT_OG_HERO)


MOBILE_VIEWPORT_CONTENT = (
    "width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, "
    "viewport-fit=cover"
)


def inject_mobile_viewport_meta() -> None:
    """모바일 줌·레이아웃 고정 — ``<head>`` 에 viewport 메타를 보장합니다."""
    content = html.escape(MOBILE_VIEWPORT_CONTENT, quote=True)
    st.markdown(
        f'<meta name="viewport" content="{content}" />',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
<script>
(function () {{
    const doc = document;
    if (!doc || !doc.head) return;
    const desired = {json.dumps(MOBILE_VIEWPORT_CONTENT)};
    let meta = doc.querySelector('meta[name="viewport"]');
    if (!meta) {{
        meta = doc.createElement("meta");
        meta.setAttribute("name", "viewport");
        doc.head.insertBefore(meta, doc.head.firstChild);
    }}
    meta.setAttribute("content", desired);
}})();
</script>
""".strip(),
        unsafe_allow_html=True,
    )


def inject_link_share_meta(*, description: str | None = None) -> None:
    """og:image·설명 메타를 주입합니다."""
    inject_mobile_viewport_meta()
    base = _public_app_base_url()
    image = _og_image_url()
    title = "사주까기 · 무료 사주풀이"
    desc = (
        description
        or "무료 사주풀이 — 사주·궁합·대운·타로·주역·AI 상담"
    ).strip()
    image_alt = _OG_IMAGE_ALT
    page_url = base or ""

    og_url_line = ""
    if page_url:
        og_url_line = f'<meta property="og:url" content="{html.escape(page_url, quote=True)}" />'

    block = f"""
<meta name="viewport" content="{html.escape(MOBILE_VIEWPORT_CONTENT, quote=True)}" />
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
    _inject_share_meta_into_head(
        title=title,
        desc=desc,
        image=image,
        image_alt=image_alt,
        page_url=page_url,
    )


def _inject_share_meta_into_head(
    *,
    title: str,
    desc: str,
    image: str,
    image_alt: str,
    page_url: str,
) -> None:
    """카카오 크롤러용 — og/twitter 메타를 document.head 에 보장."""
    payload = {
        "title": title,
        "desc": desc,
        "image": image,
        "imageAlt": image_alt,
        "pageUrl": page_url,
    }
    st.markdown(
        f"""
<script>
(function () {{
    const doc = document;
    if (!doc || !doc.head) return;
    const cfg = {json.dumps(payload)};
    const upsert = (selector, attrs) => {{
        let el = doc.querySelector(selector);
        if (!el) {{
            el = doc.createElement("meta");
            Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
            doc.head.appendChild(el);
        }} else {{
            Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
        }}
        if (attrs.content !== undefined) el.setAttribute("content", attrs.content);
    }};
    upsert('meta[name="description"]', {{ name: "description", content: cfg.desc }});
    upsert('meta[property="og:type"]', {{ property: "og:type", content: "website" }});
    upsert('meta[property="og:site_name"]', {{ property: "og:site_name", content: "사주까기" }});
    upsert('meta[property="og:title"]', {{ property: "og:title", content: cfg.title }});
    upsert('meta[property="og:description"]', {{ property: "og:description", content: cfg.desc }});
    upsert('meta[property="og:image"]', {{ property: "og:image", content: cfg.image }});
    upsert('meta[property="og:image:secure_url"]', {{
        property: "og:image:secure_url",
        content: cfg.image,
    }});
    upsert('meta[property="og:image:type"]', {{ property: "og:image:type", content: "image/png" }});
    upsert('meta[property="og:image:width"]', {{ property: "og:image:width", content: "1200" }});
    upsert('meta[property="og:image:height"]', {{ property: "og:image:height", content: "630" }});
    upsert('meta[property="og:image:alt"]', {{ property: "og:image:alt", content: cfg.imageAlt }});
    if (cfg.pageUrl) {{
        upsert('meta[property="og:url"]', {{ property: "og:url", content: cfg.pageUrl }});
    }}
    upsert('meta[name="twitter:card"]', {{ name: "twitter:card", content: "summary_large_image" }});
    upsert('meta[name="twitter:title"]', {{ name: "twitter:title", content: cfg.title }});
    upsert('meta[name="twitter:description"]', {{
        name: "twitter:description",
        content: cfg.desc,
    }});
    upsert('meta[name="twitter:image"]', {{ name: "twitter:image", content: cfg.image }});
}})();
</script>
""".strip(),
        unsafe_allow_html=True,
    )
