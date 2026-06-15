"""구조화된 해석 UI — 한 줄 요약(골드), 키워드 태그, 상세, 실천 조언, 원형 지수."""

from __future__ import annotations

import html
import math
import re
import secrets
from typing import Any

import streamlit as st

from saju_app.ui.interpretation_types import StructuredInterpretation

__all__ = [
    "StructuredInterpretation",
    "build_step3_interpretation",
    "build_step6_today_interpretation",
    "format_structured_interpretation_for_pdf",
    "render_structured_interpretation_block",
]

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
        cap = "기운이 또렷하게 모이는 편이에요"
    elif n >= 58:
        cap = "균형 잡고 조절할 여지가 있어요"
    else:
        cap = "휴식·보완을 챙기면 체감이 좋아져요"
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


def _advice_pool(
    *,
    ilju: str,
    strength: str,
    yongshin: str,
    max_el: str,
    min_el: str,
    need_el: str,
) -> list[tuple[str, str]]:
    """일주·용신 조합마다 다른 실천 조언."""
    pools: list[tuple[str, str]] = [
        (
            "🎯",
            f"용신 **{yongshin}** 방향(색·음식·동선·대화 톤)을 하루 한 가지씩 붙여 보세요.",
        ),
        (
            "🌤️",
            f"조후 보완 **{need_el}** — 수면·식사·실내 온도 중 하나만이라도 맞추면 체감이 좋아집니다.",
        ),
        (
            "⚖️",
            f"강한 {_EL_KO.get(max_el, max_el)}은 재능으로, 약한 {_EL_KO.get(min_el, min_el)}은 과투입을 줄이는 쪽으로 다스리세요.",
        ),
    ]
    extra_by_strength = {
        "신강": [
            ("💪", "기회가 보일 때 일정·계약·돈 거래 조건을 먼저 글로 적어 두고 움직이세요."),
            ("🧭", "혼자 결정하기보다 ‘누가 검증해 주는지’를 정해 두면 실수가 줄어듭니다."),
        ],
        "신약": [
            ("🤝", "혼자 끙끙대기보다 믿을 만한 사람·멘토·루틴을 하나씩 붙이세요."),
            ("🛌", "컨디션이 떨어지면 결정을 미루고, 회복 루틴을 먼저 챙기세요."),
        ],
        "중화": [
            ("📋", "한 달에 한 번, 재물·관계·일 중 ‘지금 가장 신경 쓸 하나’만 정해 집중하세요."),
            ("🔄", "같은 방식만 고집하지 말고, 분기마다 생활 패턴을 가볍게 조정해 보세요."),
        ],
    }
    idx = sum(ord(c) for c in f"{ilju}{strength}{yongshin}") % 2
    pools.append(extra_by_strength.get(strength, extra_by_strength["중화"])[idx])
    yong_extra = {
        "木": ("🌱", "새 배움·새 프로젝트를 ‘작게’ 시작해 성장 신호를 확인하세요."),
        "火": ("✨", "말·표현·SNS·대면 만남 중 하나를 일정에 고정해 두세요."),
        "土": ("🏠", "생활 공간·식사·수면 시간을 먼저 정리하면 다른 운이 붙기 쉽습니다."),
        "金": ("📐", "계약·정리·마감·품질 기준을 명확히 하면 손해가 줄어듭니다."),
        "水": ("🌊", "정보 수집·휴식·이동 동선을 넓히되, 감정 소모는 줄이세요."),
    }
    if yongshin in yong_extra:
        pools.append(yong_extra[yongshin])
    return pools[:5]


def _collapse_duplicate_chunks(text: str, *, min_chunk: int = 36) -> str:
    """같은 문장·구절이 반복되면 한 번만 남깁니다."""
    t = " ".join(str(text or "").split())
    if len(t) < min_chunk * 2:
        return t
    for n in range(min(len(t) // 2, 180), min_chunk - 1, -1):
        head = t[:n]
        tail = t[n : n + n]
        if tail == head or t.count(head) > 1:
            rest = t[n:]
            while head and head in rest:
                rest = rest.replace(head, " ", 1).strip()
            return (head + (" " + rest if rest else "")).strip()
    return t


def _is_ilju_section_block(block: str) -> bool:
    b = str(block or "")
    return "일주 · 성격】" in b or "일주 · 직업】" in b or "일주 · 연애】" in b


def _ilju_detail_paragraphs(ilju: str) -> list[str]:
    """ilju_60 DB — 성격·직업·연애 전용 문단 (메모리 DB 우선)."""
    key = str(ilju or "").strip()
    if len(key) < 2:
        return []

    prof: dict[str, str] = {"personality": "", "career": "", "relationship": ""}
    try:
        from saju_app.ui.ilju_data import build_ilju_db

        entry = build_ilju_db().get(key)
        if isinstance(entry, dict):
            prof = {
                "personality": str(entry.get("personality") or "").strip(),
                "career": str(entry.get("career") or "").strip(),
                "relationship": str(entry.get("relationship") or "").strip(),
            }
    except Exception:
        pass

    if not any(len(prof.get(k) or "") >= 40 for k in ("personality", "career", "relationship")):
        try:
            from saju_app.ui.ilju_profiles import get_ilju_profile

            loaded = get_ilju_profile(key)
            if loaded:
                prof = loaded
        except Exception:
            pass

    out: list[str] = []
    seen: set[str] = set()
    for field, label in (
        ("personality", "성격"),
        ("career", "직업"),
        ("relationship", "연애"),
    ):
        body = _collapse_duplicate_chunks(str(prof.get(field) or "").strip())
        if len(body) < 40 or body in seen:
            continue
        seen.add(body)
        from saju_app.ui.plain_language import to_plain_text

        out.append(f"【{key} 일주 · {label}】\n{to_plain_text(body)}")
    return out


def build_step3_interpretation(
    *,
    u_gapja: list[str],
    engine: dict[str, Any],
    core: dict[str, Any] | None,
) -> StructuredInterpretation:
    from saju_app.ui import components as M

    strength = str(engine.get("strength", "중화"))
    yongshin = str(engine.get("yongshin", "판단 필요"))
    max_el = str(engine.get("max_el", "木"))
    min_el = str(engine.get("min_el", "水"))
    el = engine.get("elements") or {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    ilju = u_gapja[2] if len(u_gapja) > 2 else ""
    month_branch = u_gapja[1][1] if len(u_gapja) > 1 and len(u_gapja[1]) >= 2 else None
    johu = M.get_johu_advice(month_branch) if month_branch else {"season": "미상", "desc": "", "need_elements": []}
    juk = M.get_jukchunsu_advice(strength, yongshin)
    day_stem = str(engine.get("day_stem") or (ilju[0] if ilju else ""))

    one_liner_variants = {
        "신강": f"{ilju} 일주(나) · 에너지 강한 편 — {yongshin} 기운으로 힘을 나눠 쓰면 추진력이 살아나요.",
        "신약": f"{ilju} 일주(나) · 에너지 약한 편 — {yongshin}·도움 기운으로 컨디션을 채우면 선택이 좋아져요.",
        "중화": f"{ilju} 일주(나) · 균형형 — {yongshin}을 기준으로 강·약을 번갈아 쓰면 흐름이 안정돼요.",
    }
    one_liner = one_liner_variants.get(strength, one_liner_variants["중화"])

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
    paras.extend(_ilju_detail_paragraphs(ilju))

    core_text = ""
    if core:
        core_text = str(core.get("interpretation_200") or "").strip()
    if core_text:
        for block in core_text.split("\n\n"):
            block = _collapse_duplicate_chunks(block.strip())
            if not block or _is_ilju_section_block(block):
                continue
            paras.append(_strip_md_bold(block))
    elif not paras:
        from saju_app.ui.briefing_life_sync import _DAY_STEM_ROLE

        day_stem = str(engine.get("day_stem") or (ilju[0] if ilju else ""))
        stem_role = _DAY_STEM_ROLE.get(day_stem, "")
        if stem_role:
            paras.append(f"{ilju} 일주 — {stem_role}")

    paras.append(
        f"오행 분포상 {_EL_KO.get(max_el, max_el)} {int(el.get(max_el, 0))}% · "
        f"보완 {_EL_KO.get(min_el, min_el)} {int(el.get(min_el, 0))}% · "
        f"신강약 {strength}(점수 {engine.get('strength_score', '—')})."
    )
    desc = str(johu.get("desc") or "").strip()
    if desc:
        paras.append(f"월지·조후({johu.get('season', '')}) — {desc}")
    paras.append(_strip_md_bold(juk))

    clash = int(engine.get("clash") or 0)
    combine = int(engine.get("combine") or 0)
    if clash or combine:
        paras.append(
            f"원국 지지 — 합 {combine} · 충 {clash}. "
            + (
                "변화·이동·관계 재정비 신호가 섞여 있습니다."
                if clash >= 2
                else "협력·인연에서 도움을 받기 쉬운 편입니다."
                if combine >= 2
                else "합·충이 적어 비교적 안정적인 흐름입니다."
            )
        )
    paras = [p for p in paras if p][:12]

    need_el = ", ".join(johu.get("need_elements") or []) or "균형"
    advice = _advice_pool(
        ilju=ilju,
        strength=strength,
        yongshin=yongshin,
        max_el=max_el,
        min_el=min_el,
        need_el=need_el,
    )
    advice_plain = [(a, _strip_md_bold(b)) for a, b in advice]

    hp, hc = _harmony_from_engine(engine)
    from saju_app.ui.plain_language import to_plain_structured

    return to_plain_structured(
        StructuredInterpretation(
            one_liner=one_liner,
            tags=tags,
            detail_paragraphs=paras,
            advice=advice_plain,
            harmony_pct=hp,
            harmony_caption=hc,
        )
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
    today_el: str = "",
    day_el: str = "",
    base_msg: str,
    harmony_pct: int,
) -> StructuredInterpretation:
    one_liner = (
        f"오늘의 십성은 {ten_detail}({ten_group}) — "
        f"용신 {_EL_KO.get(yongshin, yongshin)}을 살리면 리듬이 안정됩니다."
    )

    tags = [ten_group, ten_detail, strength, f"우세 {_EL_KO.get(max_el, max_el)}"]
    if yongshin and yongshin != "판단 필요":
        tags.insert(1, f"용신 {_EL_KO.get(yongshin, yongshin)}")
    if day_el:
        tags.append(f"일간 {_EL_KO.get(day_el, day_el)}")
    tags = tags[:6]

    paras = _split_sentences(base_msg, max_parts=2)
    if not paras:
        paras = [base_msg]
    t_el = today_el or max_el
    paras.append(
        f"신강약은 {strength}이며, 본인 사주는 {_EL_KO.get(max_el, max_el)} 기운이 강하고 "
        f"{_EL_KO.get(min_el, min_el)} 보완이 필요합니다. "
        f"오늘 일진은 {_EL_KO.get(t_el, t_el)}·{ten_detail} 기운이 더 드러납니다."
    )

    advice = [
        ("📌", "아침·저녁 루틴 하나만 용신 방향으로 고정해 보세요."),
        ("💬", "감정이 올라오면 메시지는 짧게, 약속은 확실하게 잡으세요."),
        ("🌙", "수면 전 스크린을 줄이면 다음 날 체감 운이 덜 흔들립니다."),
    ]
    cap = "오늘의 리듬 지수" if harmony_pct >= 60 else "보완하면 체감이 오르는 날"
    from saju_app.ui.plain_language import to_plain_structured

    return to_plain_structured(
        StructuredInterpretation(
            one_liner=one_liner,
            tags=tags,
            detail_paragraphs=paras[:5],
            advice=advice,
            harmony_pct=max(35, min(99, int(harmony_pct))),
            harmony_caption=cap,
        )
    )


def render_structured_interpretation_block(
    data: StructuredInterpretation,
    *,
    container_key: str = "saju_ix",
) -> None:
    """한 줄(골드) · 태그 · 원형 지수 · 상세 · 번호 실천 조언."""
    from saju_app.ui import components as M
    from saju_app.ui.plain_language import plain_caption_line, to_plain_structured

    data = to_plain_structured(data)
    uid = secrets.token_hex(4)
    with st.container(key=container_key):
        st.caption(plain_caption_line())
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
                raw = str(p or "").strip()
                if not raw:
                    continue
                if "\n" in raw and raw.startswith("【"):
                    title, _, body = raw.partition("\n")
                    tone = html.escape(tones[idx % len(tones)], quote=True)
                    body_html = M._md_bold_to_html_safe(body)
                    st.markdown(
                        f"""
<div class="saju-ix-detail-frame" style="--saju-ix-tone:{tone};">
  <div class="saju-ix-detail-title">{html.escape(title)}</div>
  <div class="saju-ix-detail-body">{body_html}</div>
</div>
""",
                        unsafe_allow_html=True,
                    )
                else:
                    body = M._md_bold_to_html_safe(raw)
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
