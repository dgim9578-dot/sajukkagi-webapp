"""STEP11 채팅 — 한지 질감·말풍선·역할 배지·AI 장식 SVG."""

from __future__ import annotations

import html
import secrets


def _svg_stars(uid: str) -> str:
    g = f"s11g_{uid}"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="42" height="34" viewBox="0 0 42 34" aria-hidden="true" class="step11-deco-svg">
<defs><linearGradient id="{g}" x1="0%" y1="0%" x2="100%" y2="100%">
<stop offset="0%" stop-color="#94a3b8"/><stop offset="100%" stop-color="#e2e8f0"/></linearGradient></defs>
<path d="M4 22 L10 8 L16 20 L22 6 L28 18 L34 10 L38 24" fill="none" stroke="url(#{g})" stroke-width="1.2" stroke-linecap="round" opacity="0.9"/>
<circle cx="10" cy="8" r="2" fill="#fbbf24" opacity="0.95"/><circle cx="22" cy="6" r="1.6" fill="#e2e8f0"/>
<circle cx="34" cy="10" r="1.5" fill="#f472b6" opacity="0.85"/><circle cx="16" cy="20" r="1.3" fill="#67e8f9" opacity="0.9"/>
</svg>"""


def _svg_hanji(uid: str) -> str:
    h = f"h11_{uid}"
    fnoise = f"hnoise_{uid}"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="38" height="34" viewBox="0 0 38 34" aria-hidden="true" class="step11-deco-svg">
<defs>
<linearGradient id="{h}" x1="0%" y1="0%" x2="100%" y2="100%">
<stop offset="0%" stop-color="#faf6ef"/><stop offset="50%" stop-color="#e8dcc8"/><stop offset="100%" stop-color="#d4c4a8"/></linearGradient>
<filter id="{fnoise}" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch" result="n"/>
<feColorMatrix type="matrix" values="0 0 0 0 .92  0 0 0 0 .88  0 0 0 0 .82  0 0 0 .12 0" in="n" result="c"/>
<feBlend in="SourceGraphic" in2="c" mode="multiply"/></filter>
</defs>
<rect x="1" y="2" width="34" height="28" rx="4" fill="url(#{h})" filter="url(#{fnoise})" stroke="#b45309" stroke-opacity="0.35" stroke-width="0.8"/>
<path d="M8 8v16M14 10v12M20 7v18M26 9v14" stroke="#a16207" stroke-opacity="0.12" stroke-width="1.2"/>
</svg>"""

LEGEND_HTML = """
<div class="step11-legend-row" role="navigation" aria-label="답변 주체 안내">
  <div class="step11-legend-card step11-legend-ai">
    <span class="step11-legend-ic" aria-hidden="true">◇</span>
    <div>
      <div class="step11-legend-title">AI 사주 전문가</div>
      <div class="step11-legend-desc">일간·용신·대운 규칙 기반 자동 초안</div>
    </div>
  </div>
  <div class="step11-legend-card step11-legend-expert">
    <span class="step11-legend-ic" aria-hidden="true">✦</span>
    <div>
      <div class="step11-legend-title">사주까기 전문가</div>
      <div class="step11-legend-desc">실명 상담사가 직접 작성하는 답변</div>
    </div>
  </div>
</div>
""".strip()


def _body_html(raw: str) -> str:
    """본문: 줄바꿈만 <br/>, 나머지 이스케이프."""
    t = str(raw or "")
    t = html.escape(t)
    return t.replace("\n", "<br/>")


def _ai_reply_with_lead(raw: str) -> str:
    """AI 자동 답변 본문 앞에 🔮 또는 🌟(안정적 교대). 이미 있으면 중복 없음."""
    s = str(raw or "")
    t = s.lstrip()
    if t.startswith("🔮") or t.startswith("🌟"):
        return s
    lead = "🔮" if (hash(t) % 2 == 0) else "🌟"
    return f"{lead} {s}".rstrip() if s else lead


def _ai_deco_row(uid: str) -> str:
    return (
        f'<div class="step11-ai-deco" aria-hidden="true">{_svg_stars(uid)}{_svg_hanji(uid)}</div>'
    )


def _expert_deco_row() -> str:
    return '<div class="step11-expert-deco" aria-hidden="true"><span class="step11-seal">印</span></div>'


def render_message_html(msg: dict, *, u_name: str) -> str:
    """단일 메시지: 말풍선 + 역할 배지 (+ AI/전문가 장식)."""
    uid = secrets.token_hex(4)
    role = str(msg.get("role", "assistant"))
    raw = str(msg.get("msg", ""))
    is_manual = bool(msg.get("is_manual", False))
    un = str(u_name or "").strip() or "고객"

    if role == "user":
        who = html.escape(un)
        return (
            '<div class="step11-msg-row step11-msg-user">'
            '<div class="step11-bubble step11-bubble-user">'
            f'<div class="step11-role-row"><span class="step11-role-pill step11-role-user">💬 나 · {who}</span></div>'
            f'<div class="step11-bubble-body">{_body_html(raw)}</div>'
            "</div></div>"
        )

    if is_manual:
        return (
            '<div class="step11-msg-row step11-msg-assistant">'
            '<div class="step11-bubble step11-bubble-expert">'
            '<div class="step11-role-row">'
            '<span class="step11-role-pill step11-role-expert">'
            "✦ 사주까기 전문가</span></div>"
            f"{_expert_deco_row()}"
            f'<div class="step11-bubble-body">{_body_html(raw)}</div>'
            "</div></div>"
        )

    return (
        '<div class="step11-msg-row step11-msg-assistant">'
        '<div class="step11-bubble step11-bubble-ai">'
        '<div class="step11-role-row">'
        '<span class="step11-role-pill step11-role-ai">'
        "◆ AI 사주 전문가</span></div>"
        f"{_ai_deco_row(uid)}"
        f'<div class="step11-bubble-body">{_body_html(_ai_reply_with_lead(raw))}</div>'
        "</div></div>"
    )

