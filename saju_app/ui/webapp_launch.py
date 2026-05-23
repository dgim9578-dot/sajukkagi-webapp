"""웹앱 공개 배포용 상담/수익화 안내 컴포넌트."""

from __future__ import annotations

import html
import os
from typing import Any

import streamlit as st


def _setting(name: str, default: str = "") -> str:
    """환경변수 우선, 없으면 Streamlit secrets에서 문자열 설정을 읽습니다."""
    value = str(os.environ.get(name, "") or "").strip()
    if value:
        return value
    try:
        return str(st.secrets.get(name, default) or default).strip()
    except Exception:
        return str(default or "").strip()


def public_webapp_settings() -> dict[str, str]:
    return {
        "app_name": _setting("SAJU_APP_NAME", "사주까기"),
        "operator_name": _setting("SAJU_OPERATOR_NAME", "사주까기 상담실"),
        "phone": _setting("SAJU_PUBLIC_PHONE", "010-8173-7471"),
        "kakao_url": _setting("SAJU_KAKAO_OPENCHAT_URL", "https://open.kakao.com/o/s6OhFXni"),
        "premium_url": _setting("SAJU_PREMIUM_PAYMENT_URL", ""),
        "booking_url": _setting("SAJU_BOOKING_URL", ""),
        "privacy_url": _setting("SAJU_PRIVACY_URL", ""),
        "terms_url": _setting("SAJU_TERMS_URL", ""),
        "ad_notice": _setting("SAJU_AD_NOTICE", "일부 화면에 광고가 표시될 수 있습니다"),
    }


def _a_button(label: str, href: str, *, primary: bool = False) -> str:
    if not href:
        return ""
    bg = "#b8860b" if primary else "#f8fafc"
    fg = "#ffffff" if primary else "#334155"
    border = "rgba(184,134,11,0.55)" if primary else "#e5e7eb"
    return (
        f'<a href="{html.escape(href, quote=True)}" target="_blank" rel="noopener noreferrer" '
        f'style="display:block;text-align:center;padding:0.64rem 0.75rem;border-radius:0.75rem;'
        f'background:{bg};border:1px solid {border};color:{fg};font-weight:800;'
        'text-decoration:none;line-height:1.2;">'
        f"{html.escape(label)}</a>"
    )


def render_step1_premium_button(*, key: str = "step1_premium_btn") -> None:
    """홈 CTA 2열 — 프리미엄 링크 또는 준비중."""
    s = public_webapp_settings()
    premium = s["premium_url"]
    if premium:
        st.link_button(
            "프리미엄 리포트",
            premium,
            use_container_width=True,
            type="primary",
            key=key,
        )
    else:
        st.button(
            "프리미엄 준비중",
            use_container_width=True,
            disabled=True,
            key=key,
        )


def render_step1_phone_caption() -> None:
    """홈 하단 — 광고 안내."""
    s = public_webapp_settings()
    notice = s["ad_notice"] or "일부 화면에 광고가 표시될 수 있습니다"
    st.caption(notice)


def render_policy_footer() -> None:
    s = public_webapp_settings()
    links: list[str] = []
    if s["privacy_url"]:
        links.append(f'<a href="{html.escape(s["privacy_url"], quote=True)}" target="_blank">개인정보처리방침</a>')
    if s["terms_url"]:
        links.append(f'<a href="{html.escape(s["terms_url"], quote=True)}" target="_blank">이용약관</a>')
    link_html = " · ".join(links)
    if link_html:
        link_html = " · " + link_html
    st.caption(
        "본 서비스는 운세.성향 참고용입니다 건강. 질병. 법률 등 중요한 사항은 전문가와 상담하세요"
    )
    if link_html:
        st.markdown(
            f'<div style="font-size:0.85rem;color:#6b7280;">운영자: {html.escape(s["operator_name"])}{link_html}</div>',
            unsafe_allow_html=True,
        )

