"""STEP11/12 공유 채팅 — 메시지 중복 제거·전송 가드."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from saju_app.utils import match_body_html


def message_signature(msg: dict) -> tuple[str, str, bool]:
    return (
        str(msg.get("role") or ""),
        str(msg.get("msg") or ""),
        bool(msg.get("is_manual", False)),
    )


def dedupe_chat_messages(msgs: list[Any]) -> list[dict]:
    """연속으로 동일한 메시지(역할·본문·수동 여부)가 쌓인 경우 한 번만 유지합니다."""
    out: list[dict] = []
    prev: tuple[str, str, bool] | None = None
    for m in msgs or []:
        if not isinstance(m, dict):
            continue
        sig = message_signature(m)
        if sig == prev:
            continue
        prev = sig
        out.append(m)
    return out


def tail_matches_user(msgs: list[dict], text: str) -> bool:
    if not msgs:
        return False
    tail = msgs[-1]
    return (
        str(tail.get("role") or "") == "user"
        and str(tail.get("msg") or "").strip() == str(text or "").strip()
    )


def tail_matches_assistant(msgs: list[dict], body: str) -> bool:
    if not msgs:
        return False
    tail = msgs[-1]
    return (
        str(tail.get("role") or "") == "assistant"
        and not bool(tail.get("is_manual", False))
        and str(tail.get("msg") or "").strip() == str(body or "").strip()
    )


def bubble_html(msg: dict, *, customer_label: str = "고객") -> str:
    """말풍선 HTML 한 덩어리(React insertBefore 오류 방지용)."""
    role = str(msg.get("role") or "assistant")
    body = str(msg.get("msg") or "")
    is_manual = bool(msg.get("is_manual", False))
    if role == "user":
        safe = html.escape(body).replace("\n", "<br>")
        return (
            '<div class="saju-chat-msg saju-chat-msg--user">'
            '<div class="saju-chat-bubble" style="background:#1e40af;color:#fff;padding:14px 18px;'
            'border-radius:20px 20px 5px 20px;">'
            f"<small>👤 {html.escape(customer_label)}</small><br>{safe}"
            "</div></div>"
        )
    if is_manual:
        safe = match_body_html(body)
        return (
            '<div class="saju-chat-msg">'
            '<div class="saju-chat-bubble saju-chat-bubble--expert" style="background:#4c1d95;color:#e2e8f0;'
            'padding:16px 18px;border-radius:14px;border-left:5px solid #c4b5fd;">'
            '<b style="color:#ddd6fe;">⭐ 사주까기 전문가 답변</b><br><br>'
            f"{safe}"
            "</div></div>"
        )
    safe = match_body_html(body)
    return (
        '<div class="saju-chat-msg">'
        '<div class="saju-chat-bubble saju-chat-bubble--ai" style="background:#1f2937;color:#e2e8f0;'
        'padding:16px 18px;border-radius:14px;border-left:5px solid #facc15;line-height:1.65;">'
        '<b style="color:#fcd34d;">🤖 AI 자동 분석</b><br><br>'
        f"{safe}"
        "</div></div>"
    )


def chat_viewport_html(inner: str) -> str:
    """채팅 본문 — 고정 높이·내부 스크롤(STEP11/12)."""
    body = str(inner or "")
    return f'<div class="saju-chat-viewport">{body}</div>'


def render_conversation_chat_ui(
    messages: list[dict],
    *,
    customer_label: str = "고객",
    empty_text: str = "현재 수신된 고객 메시지가 없습니다.",
) -> None:
    """채팅 전체를 **한 번의** ``st.markdown`` 으로 렌더(``st.chat_message`` N개는 rerun 시 removeChild 유발)."""
    empty_html = (
        f'<p style="margin:0;color:#6b7280;">{html.escape(empty_text)}</p>'
    )
    body = conversation_html(
        messages,
        empty_html=empty_html,
        customer_label=customer_label,
    )
    st.markdown(body, unsafe_allow_html=True)


def conversation_html(
    messages: list[dict],
    *,
    empty_html: str = "",
    customer_label: str = "고객",
) -> str:
    """채팅 전체를 단일 HTML로 묶어 Streamlit DOM 패치 충돌을 줄입니다."""
    if not messages:
        return chat_viewport_html(empty_html)
    parts = [
        bubble_html(m, customer_label=customer_label)
        for m in messages
        if isinstance(m, dict)
    ]
    return chat_viewport_html(f'<div class="saju-chat-thread">{"".join(parts)}</div>')
