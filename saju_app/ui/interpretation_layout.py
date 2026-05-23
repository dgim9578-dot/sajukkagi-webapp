"""구조화된 해석 UI — 한 줄 요약(골드), 키워드 태그, 상세, 실천 조언, 원형 지수."""

from __future__ import annotations

import html
import math
import re
import secrets
from dataclasses import dataclass
from typing import Any

import streamlit as st

from saju_app.ui import components as M

_EL_KO = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}


def _strip_md_bold(s: str) -> str:
    return re.sub(r"\*\*([^*]+)\*\*", r"\1", str(s or "")).strip()


def _split_sentences(text: str, *, max_parts: int = 4) -> list[str]:
    t = re.sub(r"\s+", " ", str(text or "").strip())
    if not t:
        return []
    parts = re.split(r"(?<=[.!?…])\s+|(?<=다)\s+(?=[가-힣])", t)
    out = [p.strip() for p in parts if p.strip()]
    if len(out) <= 1 and len(t) > 80:
        mid = len(t) // 2
        sp = t.rfind(" ", 20, len(t) - 20)
        if sp > 0:
            out = [t[:sp].strip(), t[sp:].strip()]
        else:
            out = [t]
    return out[:max_parts]


def _harmony_from_engine(engine: dict[str, Any]) -> tuple[int, str]:
    """엔진 기반 종합 균형 지수(0~100)와 짧은 캡션."""
    raw = float(engine.get("strength_score") or 0)
    el = engine.get("elements") or {}
    max_el = str(engine.get("max_el") or "木")
    pct = int(el.get(max_el, 40)) if el else 40
    # 신강약 점수와 오행 쏠림 완화를 함께 반영
    score = 54.0 + raw * 3.8 + min(12, abs(pct - 33) * 0.25)
    n = int(max(38, min(96, round(score))))
    if n >= 78:
        cap = "기운이 비교적 또렷하게 모입니다"
    elif n >= 58:
        cap = "조절 여지가 있는 균형형에 가깝습니다"
    else:
        cap = "보완과 휴식을 병행하면 체감이 좋아집니다"
    return n, cap


def _donut_svg(pct: int, *, uid: str) -> str:
    pct = max(0, min(100, int(pct)))
    r = 52
    cx, cy = 70, 70
    c = 2 * math.pi * r
    dash = c * (pct / 100.0)
    gap = max(c - dash, 0.001)
    gid = f"ixg_{uid}"
    return f"""<svg width="132" height="132" viewBox="0 0 140 140" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
<defs><linearGradient id="{gid}" x1="0%" y1="0%" x2="100%" y2="100%">
<stop offset="0%" stop-color="#d4af37"/><stop offset="55%" stop-color="#fbbf24"/><stop offset="100%" stop-color="#b45309"/>
</linearGradient></defs>
<circle r="{r}" cx="{cx}" cy="{cy}" fill="none" stroke="rgba(120,120,120,0.18)" stroke-width="11"/>
<circle r="{r}" cx="{cx}" cy="{cy}" fill="none" stroke="url(#{gid})" stroke-width="11"
stroke-linecap="round" stroke-dasharray="{dash:.2f} {gap:.2f}" transform="rotate(-90 {cx} {cy})"/>
<text x="{cx}" y="{cy + 7}" text-anchor="middle" font-size="21" font-weight="800" class="saju-ix-donut-num">{pct}</text>
<text x="{cx}" y="{cy + 26}" text-anchor="middle" font-size="10" font-weight="600" fill="rgba(100,100,100,0.85)">지수</text>
</svg>"""


@dataclass(frozen=True)
class StructuredInterpretation:
    one_liner: str
    tags: list[str]
    detail_paragraphs: list[str]
    advice: list[tuple[str, str]]
    harmony_pct: int
    harmony_caption: str


def build_step3_interpretation(
    *,
    u_gapja: list[str],
    engine: dict[str, Any],
    core: dict[str, Any] | None,
) -> StructuredInterpretation:
    strength = str(engine.get("strength", "중화"))
    yongshin = str(engine.get("yongshin", "판단 필요"))
    max_el = str(engine.get("max_el", "木"))
    min_el = str(engine.get("min_el", "水"))
    el = engine.get("elements") or {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    ilju = u_gapja[2] if len(u_gapja) > 2 else ""
    day_hanja = M.element_to_hanja(engine.get("day_el", ""))
    month_branch = u_gapja[1][1] if len(u_gapja) > 1 and len(u_gapja[1]) >= 2 else None
    johu = M.get_johu_advice(month_branch) if month_branch else {"season": "미상", "desc": "", "need_elements": []}
    juk = M.get_jukchunsu_advice(strength, yongshin)

    one_liner = (
        f"{ilju} 일주 · {strength} 구조 — {yongshin}을 중심에 두면 "
        f"흐름이 안정되고 선택의 여지가 넓어집니다."
    )

    tags: list[str] = [strength]
    if yongshin and yongshin != "판단 필요":
        tags.append(f"용신 {yongshin}")
    tags.append(f"우세 {_EL_KO.get(max_el, max_el)}")
    if min_el != max_el:
        tags.append(f"보완 {_EL_KO.get(min_el, min_el)}")
    season = str(johu.get("season") or "")
    if season and season != "미상" and len(tags) < 5:
        tags.append(f"계절 {season}")
    tags = tags[:5]

    paras: list[str] = []
    core_text = ""
    if core:
        core_text = str(core.get("interpretation_200") or "").strip()
    if core_text:
        paras.extend(_split_sentences(core_text, max_parts=3))
    paras.append(
        f"{ilju} 일주는 일간 {day_hanja}이며, 오행 분포상 {_EL_KO.get(max_el, max_el)} 기운이 "
        f"{int(el.get(max_el, 0))}%로 가장 두드러집니다. "
        f"신강약은 {strength}로 정리됩니다."
    )
    desc = str(johu.get("desc") or "").strip()
    if desc:
        paras.append(f"계절·조후 관점에서는 {desc}")
    paras.append(_strip_md_bold(juk))
    paras = [p for p in paras if p][:6]

    need_el = ", ".join(johu.get("need_elements") or []) or "균형"
    advice: list[tuple[str, str]] = [
        (
            "🎯",
            f"용신 **{yongshin}** 방향의 습관(색·음식·동선·대화 톤)을 하루 한 가지씩 붙여 보세요.",
        ),
        (
            "🌤️",
            f"조후에 필요한 **{need_el}** 기운을 생활 속에서 소량이라도 보강하면 체감이 좋아집니다.",
        ),
        (
            "⚖️",
            f"강한 {_EL_KO.get(max_el, max_el)}은 장점으로 쓰고, 약한 {_EL_KO.get(min_el, min_el)}은 과투입을 줄이는 쪽으로 다스리세요.",
        ),
        (
            "🧘",
            "중요한 결정은 하루 밤 사이 거리를 두고, 몸의 컨디션부터 확인한 뒤 실행하세요.",
        ),
    ]
    advice_plain = [(a, _strip_md_bold(b)) for a, b in advice]

    hp, hc = _harmony_from_engine(engine)
    return StructuredInterpretation(
        one_liner=one_liner,
        tags=tags,
        detail_paragraphs=paras,
        advice=advice_plain,
        harmony_pct=hp,
        harmony_caption=hc,
    )


def format_structured_interpretation_for_pdf(data: StructuredInterpretation) -> str:
    """PDF·텍스트보내기용 평문(마크다운 굵게 제거)."""
    lines: list[str] = [
        data.one_liner.strip(),
        "",
        "키워드: " + ", ".join(data.tags),
        "",
        f"균형 지수: {data.harmony_pct} — {data.harmony_caption}",
        "",
        "상세",
        "",
    ]
    for p in data.detail_paragraphs:
        lines.append(_strip_md_bold(p))
        lines.append("")
    lines.append("실천 조언")
    lines.append("")
    for i, (icon, text) in enumerate(data.advice, start=1):
        lines.append(f"{i}. {icon} {_strip_md_bold(text)}")
    return "\n".join(lines).strip()


def build_step6_today_interpretation(
    *,
    ten_detail: str,
    ten_group: str,
    yongshin: str,
    strength: str,
    max_el: str,
    min_el: str,
    base_msg: str,
    harmony_pct: int,
) -> StructuredInterpretation:
    one_liner = (
        f"오늘의 십성은 {ten_detail}({ten_group}) — "
        f"용신 {yongshin}을 살리면 리듬이 안정됩니다."
    )

    tags = [ten_group, ten_detail, strength, f"우세 {_EL_KO.get(max_el, max_el)}"]
    if yongshin and yongshin != "판단 필요":
        tags.insert(1, f"용신 {yongshin}")
    tags = tags[:5]

    paras = _split_sentences(base_msg, max_parts=2)
    if not paras:
        paras = [base_msg]
    paras.append(
        f"신강약은 {strength}이며, 오늘은 {_EL_KO.get(max_el, max_el)} 기운이 상대적으로 잘 드러나는 날입니다."
    )

    advice = [
        ("📌", "아침·저녁 루틴 하나만 용신 방향으로 고정해 보세요."),
        ("💬", "감정이 올라오면 메시지는 짧게, 약속은 확실하게 잡으세요."),
        ("🌙", "수면 전 스크린을 줄이면 다음 날 체감 운이 덜 흔들립니다."),
    ]
    cap = "오늘의 리듬 지수" if harmony_pct >= 60 else "보완하면 체감이 오르는 날"
    return StructuredInterpretation(
        one_liner=one_liner,
        tags=tags,
        detail_paragraphs=paras[:5],
        advice=advice,
        harmony_pct=max(35, min(99, int(harmony_pct))),
        harmony_caption=cap,
    )


def render_structured_interpretation_block(
    data: StructuredInterpretation,
    *,
    container_key: str = "saju_ix",
) -> None:
    """한 줄(골드) · 태그 · 원형 지수 · 상세 · 번호 실천 조언."""
    uid = secrets.token_hex(4)
    with st.container(key=container_key):
        donut = _donut_svg(data.harmony_pct, uid=uid)
        c1, c2 = st.columns([0.42, 0.58])
        with c1:
            st.markdown(
                f'<div class="saju-ix-donut-wrap" role="img" aria-label="운세 지수 {data.harmony_pct}">{donut}</div>',
                unsafe_allow_html=True,
            )
            st.caption(data.harmony_caption)
        with c2:
            st.markdown(
                f'<p class="saju-ix-one-liner">{html.escape(data.one_liner)}</p>',
                unsafe_allow_html=True,
            )
            tag_html = "".join(
                f'<span class="saju-ix-tag">{html.escape(t)}</span>' for t in data.tags
            )
            st.markdown(f'<div class="saju-ix-tags">{tag_html}</div>', unsafe_allow_html=True)

        with st.container(key=f"{container_key}_detail"):
            tones = ("#D4AF37", "#60A5FA", "#34D399", "#A78BFA", "#F59E0B", "#F472B6")
            for idx, p in enumerate(data.detail_paragraphs):
                body = M._md_bold_to_html_safe(str(p or ""))
                tone = html.escape(tones[idx % len(tones)], quote=True)
                st.markdown(
                    f"""
<div class="saju-ix-detail-frame" style="--saju-ix-tone:{tone};">
  <div class="saju-ix-detail-body">{body}</div>
</div>
""",
                    unsafe_allow_html=True,
                )

        st.markdown("#### ✨ 실천 조언")
        for i, (icon, text) in enumerate(data.advice, start=1):
            line = f"{i}. {icon} {html.escape(text)}"
            st.markdown(f'<p class="saju-ix-advice-line">{line}</p>', unsafe_allow_html=True)
