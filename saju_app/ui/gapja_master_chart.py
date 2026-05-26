"""사주 메인 차트 — 四柱 · 일간 · 팔괘 · 오행 · hover 팝업 · 생극 흐름 · 테마."""

from __future__ import annotations

import html
import json
import math
import secrets
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from saju_app.persistence import storage as saju_storage


_SLOT_LABELS = (
    ("year", "年", "년주"),
    ("month", "月", "월주"),
    ("day", "日", "일주"),
    ("hour", "時", "시주"),
)

_BAGUA = (
    ("乾", "金", 0),
    ("兑", "金", 45),
    ("离", "火", 90),
    ("震", "木", 135),
    ("巽", "木", 180),
    ("坎", "水", 225),
    ("艮", "土", 270),
    ("坤", "土", 315),
)

_ELEMENT_ORDER = ("木", "火", "土", "金", "水")
_GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_CONTROLS = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}

_TEN_GOD_HINTS: dict[str, str] = {
    "비견": "나와 같은 오행·양 — 자아, 독립, 동료",
    "겁재": "같은 오행·다른 음양 — 경쟁·협력, 분배",
    "식신": "내가 생하는 오행·양 — 창의, 표현, 여유",
    "상관": "내가 생하는 오행·음 — 혁신, 말·기술, 변화",
    "편재": "내가 극하는 오행·양 — 유동 재물, 사업",
    "정재": "내가 극하는 오행·음 — 안정 수입, 실무",
    "편관": "나를 극하는 오행·양 — 압박, 도전, 권위",
    "정관": "나를 극하는 오행·음 — 질서, 책임, 승진",
    "편인": "나를 생하는 오행·양 — 직관, 예술, 독학",
    "정인": "나를 생하는 오행·음 — 학습, 보호, 자격",
}


def _hx(text: str) -> str:
    return html.escape(str(text or ""))


def _ten_hint(ten: str) -> str:
    t = str(ten or "").strip()
    if not t:
        return ""
    return _TEN_GOD_HINTS.get(t, "")


def _pillar_row(meta: dict[str, Any], idx: int, u_gapja: list[str]) -> dict[str, Any]:
    pillars = meta.get("pillars") if isinstance(meta.get("pillars"), list) else []
    if idx < len(pillars) and isinstance(pillars[idx], dict):
        return pillars[idx]
    p = str(u_gapja[idx] if idx < len(u_gapja) else "").strip()
    if not p or p == "모름" or len(p) < 2:
        return {}
    stem, branch = p[0], p[1]
    el = saju_storage.STEM_ELEMENT.get(stem, "")
    return {
        "pillar": p,
        "stem": {
            "char": stem,
            "element": el,
            "element_name": saju_storage.ELEMENT_COLORS.get(el, {}).get("name", ""),
            "yin_yang": saju_storage.STEM_YIN_YANG.get(stem, ""),
            "ten_god": "",
            "color": saju_storage.ELEMENT_COLORS.get(el, {}).get("color", "#D4AF37"),
        },
        "branch": {
            "char": branch,
            "element": saju_storage.BRANCH_ELEMENT.get(branch, ""),
            "element_name": saju_storage.ELEMENT_COLORS.get(
                saju_storage.BRANCH_ELEMENT.get(branch, ""), {}
            ).get("name", ""),
            "hidden_stems": [],
        },
    }


def _popover_html(row: dict[str, Any], *, kor: str, han: str, is_day: bool) -> str:
    stem = row.get("stem") if isinstance(row.get("stem"), dict) else {}
    branch = row.get("branch") if isinstance(row.get("branch"), dict) else {}
    pillar = str(row.get("pillar") or "—")
    stem_ch = str(stem.get("char") or "?")
    branch_ch = str(branch.get("char") or "?")
    stem_ten = str(stem.get("ten_god") or "")
    stem_el = str(stem.get("element_name") or stem.get("element") or "")
    stem_yy = str(stem.get("yin_yang") or "")
    branch_el = str(branch.get("element_name") or branch.get("element") or "")
    hidden = branch.get("hidden_stems") if isinstance(branch.get("hidden_stems"), list) else []

    stem_ten_line = ""
    if is_day:
        stem_ten_line = '<p class="saju-mc-pop-note">일간(日主) — 본원 기운</p>'
    elif stem_ten:
        stem_ten_line = (
            f'<p class="saju-mc-pop-ten"><strong>{_hx(stem_ten)}</strong>'
            f'<span>{_hx(_ten_hint(stem_ten))}</span></p>'
        )

    hidden_items: list[str] = []
    for h in hidden:
        if not isinstance(h, dict):
            continue
        hs = str(h.get("stem") or "")
        ht = str(h.get("ten_god") or "")
        hn = str(h.get("element_name") or h.get("element") or "")
        hint = _ten_hint(ht)
        hidden_items.append(
            f'<li><span class="saju-mc-hs" lang="zh-Hant">{_hx(hs)}</span>'
            f'<span class="saju-mc-hs-meta">{_hx(hn)}</span>'
            f'<span class="saju-mc-hs-ten">{_hx(ht)}</span>'
            f'<span class="saju-mc-hs-hint">{_hx(hint)}</span></li>'
        )
    hidden_block = (
        f'<ul class="saju-mc-pop-hidden">{"".join(hidden_items)}</ul>'
        if hidden_items
        else '<p class="saju-mc-pop-empty">지장간 정보 없음</p>'
    )

    return f"""
    <div class="saju-mc-popover" role="tooltip">
      <p class="saju-mc-pop-title">{_hx(kor)} · {_hx(han)} <span lang="zh-Hant">{_hx(pillar)}</span></p>
      <div class="saju-mc-pop-block">
        <span class="saju-mc-pop-label">천간</span>
        <p lang="zh-Hant"><b>{_hx(stem_ch)}</b> · {_hx(stem_el)} · {_hx(stem_yy)}</p>
        {stem_ten_line}
      </div>
      <div class="saju-mc-pop-block">
        <span class="saju-mc-pop-label">지지</span>
        <p lang="zh-Hant"><b>{_hx(branch_ch)}</b> · {_hx(branch_el)}</p>
        <span class="saju-mc-pop-label saju-mc-pop-label--sub">지장간(숨은 간)</span>
        {hidden_block}
      </div>
    </div>
    """


def _element_positions(cx: float, cy: float, r: float) -> dict[str, tuple[float, float]]:
    pos: dict[str, tuple[float, float]] = {}
    for i, el in enumerate(_ELEMENT_ORDER):
        ang = math.radians(-90 + i * 72)
        pos[el] = (cx + r * math.cos(ang), cy + r * math.sin(ang))
    return pos


def _flow_segment(
    p1: tuple[float, float],
    p2: tuple[float, float],
    *,
    inset: float = 16,
) -> tuple[float, float, float, float]:
    x1, y1 = p1
    x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy) or 1.0
    return (
        x1 + dx / length * inset,
        y1 + dy / length * inset,
        x2 - dx / length * inset,
        y2 - dy / length * inset,
    )


def _flow_arrows_svg(cid: str) -> str:
    cx, cy, r = 200.0, 200.0, 92.0
    pos = _element_positions(cx, cy, r)
    nodes: list[str] = []
    for el in _ELEMENT_ORDER:
        x, y = pos[el]
        col = saju_storage.ELEMENT_COLORS.get(el, {}).get("color", "#888")
        nm = saju_storage.ELEMENT_COLORS.get(el, {}).get("name", el)
        nodes.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="11" fill="{_hx(col)}" fill-opacity="0.22" '
            f'stroke="{_hx(col)}" stroke-width="1.2"/>'
            f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" dominant-baseline="middle" '
            f'class="saju-mc-flow-node">{_hx(el)}</text>'
            f'<text x="{x:.1f}" y="{y + 18:.1f}" text-anchor="middle" class="saju-mc-flow-nm">{_hx(nm)}</text>'
        )

    gen_paths: list[str] = []
    for src in _ELEMENT_ORDER:
        dst = _GENERATES[src]
        x1, y1, x2, y2 = _flow_segment(pos[src], pos[dst])
        gen_paths.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'class="saju-mc-flow-line saju-mc-flow-line--gen" marker-end="url(#{cid}_arr-gen)"/>'
        )

    ctrl_paths: list[str] = []
    for src in _ELEMENT_ORDER:
        dst = _CONTROLS[src]
        x1, y1, x2, y2 = _flow_segment(pos[src], pos[dst], inset=20)
        ctrl_paths.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'class="saju-mc-flow-line saju-mc-flow-line--ctrl" marker-end="url(#{cid}_arr-ctrl)"/>'
        )

    return f"""
    <svg class="saju-mc-flow" viewBox="0 0 400 400" aria-hidden="true">
      <defs>
        <marker id="{cid}_arr-gen" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L6,3 L0,6 Z" class="saju-mc-flow-marker saju-mc-flow-marker--gen"/>
        </marker>
        <marker id="{cid}_arr-ctrl" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L6,3 L0,6 Z" class="saju-mc-flow-marker saju-mc-flow-marker--ctrl"/>
        </marker>
      </defs>
      {''.join(ctrl_paths)}
      {''.join(gen_paths)}
      {''.join(nodes)}
      <text x="200" y="28" text-anchor="middle" class="saju-mc-flow-title">오행 에너지 흐름</text>
      <text x="318" y="42" class="saju-mc-flow-legend saju-mc-flow-legend--gen">生</text>
      <text x="348" y="42" class="saju-mc-flow-legend saju-mc-flow-legend--ctrl">剋</text>
    </svg>
    """


def build_gapja_master_chart_html(
    u_gapja: list[str],
    *,
    chart_id: str | None = None,
    theme: str = "neon",
) -> str:
    """4 기둥 + 일간 + 팔괘·오행 + hover 팝업 + 생극 흐름. theme: ``neon`` | ``hanji``."""
    cid = chart_id or f"smc_{secrets.token_hex(4)}"
    theme_key = "hanji" if str(theme).strip().lower() == "hanji" else "neon"
    meta = saju_storage.build_gapja_design_meta(list(u_gapja or []))
    day_stem = str(meta.get("day_stem") or "")
    day_el = saju_storage.STEM_ELEMENT.get(day_stem, "")
    day_color = saju_storage.ELEMENT_COLORS.get(day_el, {}).get("color", "#D4AF37")
    day_name = saju_storage.ELEMENT_COLORS.get(day_el, {}).get("name", "")
    counts = meta.get("element_counts") if isinstance(meta.get("element_counts"), dict) else {}
    counts_norm = {k: int(counts.get(k, 0) or 0) for k in _ELEMENT_ORDER}
    max_count = max(counts_norm.values()) or 1

    pillars_html: list[str] = []
    for idx, (_slot, han, kor) in enumerate(_SLOT_LABELS):
        row = _pillar_row(meta, idx, list(u_gapja or []))
        stem = row.get("stem") if isinstance(row.get("stem"), dict) else {}
        branch = row.get("branch") if isinstance(row.get("branch"), dict) else {}
        is_day = idx == 2
        stem_ch = str(stem.get("char") or "?")
        branch_ch = str(branch.get("char") or "?")
        col = str(stem.get("color") or "#94a3b8")
        el = str(stem.get("element") or "")
        ten = str(stem.get("ten_god") or "")
        grad_id = f"{cid}_g{idx}"
        pillar_cls = "saju-mc-pillar saju-mc-pillar--day" if is_day else "saju-mc-pillar"
        el_name = str(stem.get("element_name") or saju_storage.ELEMENT_COLORS.get(el, {}).get("name", ""))
        ten_line = (
            f'<div class="saju-mc-ten">{_hx(ten)}</div>' if ten else ""
        )
        popover = _popover_html(row, kor=kor, han=han, is_day=is_day)
        pillars_html.append(
            f"""
            <div class="{pillar_cls}" style="--mc-color:{_hx(col)};" tabindex="0" data-pillar-idx="{idx}">
              <div class="saju-mc-slot">{_hx(kor)}</div>
              <div class="saju-mc-han">{_hx(han)}</div>
              <svg class="saju-mc-pillar-svg" viewBox="0 0 72 200" aria-hidden="true">
                <defs>
                  <linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="{_hx(col)}" stop-opacity="0.95"/>
                    <stop offset="55%" stop-color="{_hx(col)}" stop-opacity="0.35"/>
                    <stop offset="100%" stop-color="#0a0a14" stop-opacity="0.9"/>
                  </linearGradient>
                </defs>
                <rect x="14" y="8" width="44" height="184" rx="10" fill="url(#{grad_id})" stroke="{_hx(col)}" stroke-opacity="0.55" stroke-width="1.2"/>
                <text x="36" y="78" text-anchor="middle" class="saju-mc-glyph">{_hx(stem_ch)}</text>
                <text x="36" y="138" text-anchor="middle" class="saju-mc-glyph saju-mc-glyph--branch">{_hx(branch_ch)}</text>
              </svg>
              {ten_line}
              <div class="saju-mc-el">{_hx(el_name)}</div>
              {popover}
            </div>
            """
        )

    bagua_paths: list[str] = []
    cx, cy, r0, r1 = 200, 200, 118, 152
    for name, el, deg in _BAGUA:
        col = saju_storage.ELEMENT_COLORS.get(el, {}).get("color", "#64748b")
        a0 = (deg - 22.5) * math.pi / 180
        a1 = (deg + 22.5) * math.pi / 180
        x0, y0 = cx + r0 * math.cos(a0), cy + r0 * math.sin(a0)
        x1, y1 = cx + r1 * math.cos(a0), cy + r1 * math.sin(a0)
        x2, y2 = cx + r1 * math.cos(a1), cy + r1 * math.sin(a1)
        x3, y3 = cx + r0 * math.cos(a1), cy + r0 * math.sin(a1)
        bagua_paths.append(
            f'<path d="M{cx:.1f},{cy:.1f} L{x0:.1f},{y0:.1f} L{x1:.1f},{y1:.1f} L{x2:.1f},{y2:.1f} L{x3:.1f},{y3:.1f} Z" '
            f'fill="{_hx(col)}" fill-opacity="0.14" stroke="{_hx(col)}" stroke-opacity="0.35" stroke-width="0.6"/>'
            f'<text x="{cx + (r0 + r1) / 2 * math.cos((a0 + a1) / 2):.1f}" '
            f'y="{cy + (r0 + r1) / 2 * math.sin((a0 + a1) / 2):.1f}" '
            f'text-anchor="middle" dominant-baseline="middle" class="saju-mc-bagua-t">{_hx(name)}</text>'
        )

    oheng_bars: list[str] = []
    bx0, by, bw, gap = 52, 368, 28, 10
    for i, el in enumerate(_ELEMENT_ORDER):
        n = counts_norm.get(el, 0)
        h = 12 + int(48 * n / max_count)
        col = saju_storage.ELEMENT_COLORS.get(el, {}).get("color", "#888")
        nm = saju_storage.ELEMENT_COLORS.get(el, {}).get("name", el)
        x = bx0 + i * (bw + gap)
        oheng_bars.append(
            f'<rect x="{x}" y="{by - h}" width="{bw}" height="{h}" rx="6" fill="{_hx(col)}" fill-opacity="0.85"/>'
            f'<text x="{x + bw/2}" y="{by + 16}" text-anchor="middle" class="saju-mc-oheng-l">{_hx(nm)}</text>'
            f'<text x="{x + bw/2}" y="{by - h - 6}" text-anchor="middle" class="saju-mc-oheng-n">{n}</text>'
        )

    flow_svg = _flow_arrows_svg(cid)
    particle_cfg = {
        "counts": counts_norm,
        "colors": {el: saju_storage.ELEMENT_COLORS.get(el, {}).get("color", "#888") for el in _ELEMENT_ORDER},
        "day": {"stem": day_stem, "element": day_el, "color": day_color},
        "theme": theme_key,
    }

    neon_active = "is-active" if theme_key == "neon" else ""
    hanji_active = "is-active" if theme_key == "hanji" else ""

    return f"""
<div id="{cid}" class="saju-master-chart" data-theme="{theme_key}" role="img" aria-label="사주 메인 차트">
  <div class="saju-mc-toolbar">
    <button type="button" class="saju-mc-theme-btn {neon_active}" data-theme-set="neon">네온 · 모던</button>
    <button type="button" class="saju-mc-theme-btn {hanji_active}" data-theme-set="hanji">한지 · 전통</button>
  </div>
  <canvas class="saju-mc-canvas" aria-hidden="true"></canvas>
  <div class="saju-mc-stage">
    <svg class="saju-mc-ring" viewBox="0 0 400 400" aria-hidden="true">
      <circle cx="200" cy="200" r="156" fill="none" stroke="rgba(212,175,55,0.2)" stroke-width="1"/>
      {''.join(bagua_paths)}
    </svg>
    {flow_svg}
    <div class="saju-mc-center" style="--dm-color:{_hx(day_color)};">
      <div class="saju-mc-center-glow" aria-hidden="true"></div>
      <div class="saju-mc-center-inner">
        <div class="saju-mc-dm-label">日主 · Day Master</div>
        <div class="saju-mc-dm-stem" lang="zh-Hant">{_hx(day_stem or "—")}</div>
        <div class="saju-mc-dm-meta">{_hx(day_name)} · {_hx(saju_storage.STEM_YIN_YANG.get(day_stem, ""))}</div>
      </div>
    </div>
    <div class="saju-mc-pillars">{''.join(pillars_html)}</div>
    <svg class="saju-mc-oheng" viewBox="0 0 400 400" aria-hidden="true">
      {''.join(oheng_bars)}
    </svg>
  </div>
  <div class="saju-mc-mobile-dock" id="{cid}_dock" aria-hidden="true" role="region" aria-label="기둥 상세 설명"></div>
  <p class="saju-mc-hint">기둥 위에 손가락·커서를 올리면 설명이 바로 표시됩니다</p>
</div>
<style>
#{cid}.saju-master-chart {{
  --mc-text: #f0e6c8;
  --mc-muted: rgba(240, 230, 200, 0.65);
  --mc-border: rgba(212, 175, 55, 0.35);
  --mc-bg: radial-gradient(ellipse at 50% 42%, #1a2744 0%, #0a0a14 58%, #050508 100%);
  --mc-pop-bg: rgba(12, 16, 28, 0.96);
  --mc-pop-border: rgba(56, 189, 248, 0.45);
  --mc-flow-gen: #34d399;
  --mc-flow-ctrl: #f87171;
  position: relative;
  width: 100%;
  max-width: 520px;
  margin: 0 auto 0.75rem;
  min-height: 480px;
  height: clamp(480px, 92vw, 560px);
  border-radius: 18px;
  overflow: visible;
  background: var(--mc-bg);
  border: 1px solid var(--mc-border);
  box-shadow: 0 12px 40px rgba(0,0,0,0.35), inset 0 0 60px rgba(212,175,55,0.06);
  font-family: "Pretendard", "Noto Sans KR", system-ui, sans-serif;
}}
#{cid}.saju-master-chart[data-theme="hanji"] {{
  --mc-text: #3d2f1f;
  --mc-muted: rgba(61, 47, 31, 0.72);
  --mc-border: rgba(139, 90, 43, 0.45);
  --mc-bg:
    radial-gradient(ellipse at 30% 20%, rgba(255,248,235,0.9) 0%, transparent 55%),
    linear-gradient(165deg, #f3e4c8 0%, #e8d4b0 42%, #dcc9a0 100%);
  --mc-pop-bg: rgba(255, 250, 240, 0.98);
  --mc-pop-border: rgba(139, 90, 43, 0.55);
  --mc-flow-gen: #2d6a4f;
  --mc-flow-ctrl: #9b2226;
  box-shadow: 0 8px 28px rgba(80, 50, 20, 0.18), inset 0 0 80px rgba(255,255,255,0.35);
}}
#{cid} .saju-mc-toolbar {{
  position: absolute; top: 8px; right: 8px; z-index: 12;
  display: flex; gap: 4px;
}}
#{cid} .saju-mc-theme-btn {{
  font-size: 10px; padding: 4px 8px; border-radius: 999px; cursor: pointer;
  border: 1px solid var(--mc-border);
  background: rgba(0,0,0,0.35); color: var(--mc-text);
}}
#{cid}[data-theme="hanji"] .saju-mc-theme-btn {{
  background: rgba(255,255,255,0.55); color: var(--mc-text);
}}
#{cid} .saju-mc-theme-btn.is-active {{
  border-color: #38bdf8;
  box-shadow: 0 0 12px rgba(56, 189, 248, 0.45);
}}
#{cid}[data-theme="hanji"] .saju-mc-theme-btn.is-active {{
  border-color: #8b5a2b;
  box-shadow: 0 0 8px rgba(139, 90, 43, 0.35);
}}
#{cid} .saju-mc-canvas {{
  position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 1;
}}
#{cid} .saju-mc-stage {{
  position: absolute; inset: 0; z-index: 2; display: flex; align-items: center; justify-content: center;
  padding-top: 28px;
  overflow: visible;
}}
#{cid} .saju-mc-ring, #{cid} .saju-mc-flow {{
  position: absolute; width: 92%; height: auto; top: 6%; left: 4%; pointer-events: none;
}}
#{cid} .saju-mc-flow {{ opacity: 0.88; z-index: 2; }}
#{cid} .saju-mc-flow-line {{
  stroke-width: 1.8; fill: none;
}}
#{cid} .saju-mc-flow-line--gen {{
  stroke: var(--mc-flow-gen);
  stroke-dasharray: 5 9;
  animation: {cid}-flow-gen 2.2s linear infinite;
}}
#{cid} .saju-mc-flow-line--ctrl {{
  stroke: var(--mc-flow-ctrl);
  stroke-dasharray: 3 7;
  opacity: 0.75;
  animation: {cid}-flow-ctrl 2.8s linear infinite reverse;
}}
@keyframes {cid}-flow-gen {{ to {{ stroke-dashoffset: -28; }} }}
@keyframes {cid}-flow-ctrl {{ to {{ stroke-dashoffset: -20; }} }}
#{cid} .saju-mc-flow-marker--gen {{ fill: var(--mc-flow-gen); }}
#{cid} .saju-mc-flow-marker--ctrl {{ fill: var(--mc-flow-ctrl); }}
#{cid} .saju-mc-flow-node {{
  font-size: 11px; font-weight: 800; fill: var(--mc-text);
  font-family: "Noto Serif SC", serif;
}}
#{cid} .saju-mc-flow-nm {{ font-size: 7px; fill: var(--mc-muted); }}
#{cid} .saju-mc-flow-title {{ font-size: 9px; fill: var(--mc-muted); letter-spacing: 0.08em; }}
#{cid} .saju-mc-flow-legend {{ font-size: 9px; font-weight: 700; }}
#{cid} .saju-mc-flow-legend--gen {{ fill: var(--mc-flow-gen); }}
#{cid} .saju-mc-flow-legend--ctrl {{ fill: var(--mc-flow-ctrl); }}
#{cid} .saju-mc-oheng {{
  position: absolute; width: 92%; left: 4%; bottom: 0; pointer-events: none;
}}
#{cid} .saju-mc-bagua-t {{
  font-size: 9px; fill: var(--mc-muted); font-family: "Noto Serif SC", serif;
}}
#{cid}[data-theme="neon"] .saju-mc-bagua-t {{ fill: rgba(250, 243, 224, 0.75); }}
#{cid} .saju-mc-oheng-l {{ font-size: 9px; fill: var(--mc-muted); }}
#{cid}[data-theme="neon"] .saju-mc-oheng-l {{ fill: rgba(250, 243, 224, 0.8); }}
#{cid} .saju-mc-oheng-n {{ font-size: 8px; fill: var(--mc-muted); opacity: 0.85; }}
#{cid} .saju-mc-pillars {{
  position: relative; z-index: 5;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.15rem;
  width: 78%;
  max-width: 380px;
  align-items: end;
  padding-bottom: 12%;
  overflow: visible;
}}
#{cid} .saju-mc-pillar {{
  text-align: center; min-width: 0; position: relative; cursor: pointer;
  outline: none;
  -webkit-tap-highlight-color: rgba(212, 175, 55, 0.25);
  touch-action: manipulation;
  user-select: none;
}}
#{cid} .saju-mc-pillar.is-pop-open {{
  z-index: 35;
}}
#{cid} .saju-mc-pillar.is-pop-open .saju-mc-pillar-svg {{
  filter: drop-shadow(0 0 16px var(--mc-color));
}}
#{cid} .saju-mc-mobile-dock {{
  display: none;
  position: absolute;
  left: 8px;
  right: 8px;
  bottom: 8px;
  z-index: 80;
  max-height: min(46vh, 280px);
  overflow-x: hidden;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  padding: 0.65rem 0.75rem;
  border-radius: 12px;
  background: var(--mc-pop-bg);
  border: 1px solid var(--mc-pop-border);
  box-shadow: 0 14px 36px rgba(0, 0, 0, 0.5);
  color: var(--mc-text);
  text-align: left;
}}
#{cid}.has-mobile-dock-open .saju-mc-mobile-dock {{
  display: block;
}}
#{cid} .saju-mc-pillar:hover,
#{cid} .saju-mc-pillar:focus-visible {{
  z-index: 30;
}}
#{cid} .saju-mc-pillar:hover .saju-mc-pillar-svg,
#{cid} .saju-mc-pillar:focus-visible .saju-mc-pillar-svg,
#{cid} .saju-mc-pillar.is-pop-open .saju-mc-pillar-svg {{
  filter: drop-shadow(0 0 14px var(--mc-color));
  transform: translateY(-4px);
  transition: transform 0.2s ease, filter 0.2s ease;
}}
#{cid} .saju-mc-pillar--day .saju-mc-pillar-svg {{
  filter: drop-shadow(0 0 12px var(--mc-color));
  transform: scale(1.06);
}}
#{cid} .saju-mc-popover {{
  position: absolute;
  left: 50%;
  top: calc(100% + 8px);
  bottom: auto;
  transform: translateX(-50%) scale(0.96);
  width: max(220px, 42vw);
  max-width: 280px;
  max-height: min(72vh, 300px);
  overflow-x: hidden;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  padding: 0.6rem 0.7rem;
  border-radius: 10px;
  background: var(--mc-pop-bg);
  border: 1px solid var(--mc-pop-border);
  box-shadow: 0 12px 32px rgba(0,0,0,0.45);
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  transition: opacity 0.18s ease, transform 0.18s ease, visibility 0.18s;
  text-align: left;
  color: var(--mc-text);
  z-index: 50;
}}
#{cid} .saju-mc-popover--above {{
  top: auto;
  bottom: calc(100% + 8px);
}}
#{cid} .saju-mc-popover--edge-left {{
  left: 0;
  right: auto;
  transform: translateX(0) scale(0.96);
}}
#{cid} .saju-mc-popover--edge-right {{
  left: auto;
  right: 0;
  transform: translateX(0) scale(0.96);
}}
#{cid} .saju-mc-popover--viewport {{
  position: fixed !important;
  z-index: 99999;
  left: 12px !important;
  right: 12px !important;
  width: auto !important;
  max-width: none !important;
  transform: none !important;
  box-sizing: border-box;
}}
#{cid} .saju-mc-pillar.is-pop-open .saju-mc-popover--viewport {{
  transform: none !important;
}}
#{cid}[data-theme="neon"] .saju-mc-popover {{
  color: #e8eef8;
}}
#{cid} .saju-mc-pillar:hover .saju-mc-popover,
#{cid} .saju-mc-pillar:focus-visible .saju-mc-popover,
#{cid} .saju-mc-pillar.is-pop-open .saju-mc-popover {{
  opacity: 1;
  visibility: visible;
  transform: translateX(-50%) scale(1);
  pointer-events: auto;
}}
#{cid} .saju-mc-pillar:hover .saju-mc-popover--edge-left,
#{cid} .saju-mc-pillar:focus-visible .saju-mc-popover--edge-left,
#{cid} .saju-mc-pillar.is-pop-open .saju-mc-popover--edge-left {{
  transform: translateX(0) scale(1);
}}
#{cid} .saju-mc-pillar:hover .saju-mc-popover--edge-right,
#{cid} .saju-mc-pillar:focus-visible .saju-mc-popover--edge-right,
#{cid} .saju-mc-pillar.is-pop-open .saju-mc-popover--edge-right {{
  transform: translateX(0) scale(1);
}}
#{cid} .saju-mc-pop-title {{
  font-size: 12px; font-weight: 800; margin: 0 0 0.35rem;
  border-bottom: 1px solid var(--mc-border); padding-bottom: 0.25rem;
  line-height: 1.35;
}}
#{cid} .saju-mc-pop-label {{
  font-size: 10px; font-weight: 700; opacity: 0.75; display: block; margin-top: 0.25rem;
}}
#{cid} .saju-mc-pop-label--sub {{ margin-top: 0.35rem; }}
#{cid} .saju-mc-pop-block p {{ margin: 0.1rem 0; font-size: 11px; line-height: 1.45; }}
#{cid} .saju-mc-pop-ten {{
  margin: 0.2rem 0 0; font-size: 11px; line-height: 1.4;
}}
#{cid} .saju-mc-pop-ten strong {{ color: #38bdf8; margin-right: 0.25rem; }}
#{cid}[data-theme="hanji"] .saju-mc-pop-ten strong {{ color: #8b5a2b; }}
#{cid} .saju-mc-pop-ten span {{ opacity: 0.88; }}
#{cid} .saju-mc-pop-note {{ font-size: 9px; opacity: 0.8; margin: 0.15rem 0 0; }}
#{cid} .saju-mc-pop-hidden {{
  list-style: none; margin: 0.2rem 0 0; padding: 0;
  font-size: 10px; line-height: 1.45;
}}
#{cid} .saju-mc-pop-hidden li {{
  display: grid; grid-template-columns: 1.2em 2.6em 3.4em minmax(0, 1fr); gap: 0.25rem;
  padding: 0.14rem 0; border-top: 1px dashed var(--mc-border);
}}
#{cid} .saju-mc-hs {{ font-weight: 800; }}
#{cid} .saju-mc-hs-ten {{ font-weight: 700; }}
#{cid} .saju-mc-hs-hint {{ opacity: 0.75; font-size: 8px; }}
#{cid} .saju-mc-pop-empty {{ font-size: 9px; opacity: 0.65; margin: 0.15rem 0 0; }}
#{cid} .saju-mc-slot {{
  font-size: clamp(10px, 2.8vw, 12px); font-weight: 800; color: var(--mc-text); opacity: 0.92;
}}
#{cid} .saju-mc-han {{
  font-size: clamp(9px, 2.4vw, 11px); color: var(--mc-muted); margin-bottom: 0.15rem;
}}
#{cid} .saju-mc-pillar-svg {{ width: 100%; height: auto; display: block; margin: 0 auto; transition: transform 0.2s, filter 0.2s; pointer-events: none; }}
#{cid} .saju-mc-slot,
#{cid} .saju-mc-han,
#{cid} .saju-mc-ten,
#{cid} .saju-mc-el {{
  pointer-events: none;
}}
#{cid} .saju-mc-glyph {{
  font-size: 26px; fill: #fff8ec; font-family: "Noto Serif SC", "Noto Serif KR", serif; font-weight: 800;
}}
#{cid}[data-theme="hanji"] .saju-mc-glyph {{ fill: #2c1810; }}
#{cid} .saju-mc-glyph--branch {{ fill: #f5e0b8; font-size: 24px; }}
#{cid}[data-theme="hanji"] .saju-mc-glyph--branch {{ fill: #5c4030; }}
#{cid} .saju-mc-ten {{
  font-size: 9px; color: rgba(212, 175, 55, 0.9); margin-top: 2px;
}}
#{cid}[data-theme="hanji"] .saju-mc-ten {{ color: #8b5a2b; }}
#{cid} .saju-mc-el {{ font-size: 9px; color: var(--mc-muted); }}
#{cid} .saju-mc-center {{
  position: absolute; left: 50%; top: 46%; transform: translate(-50%, -50%);
  z-index: 4; text-align: center; pointer-events: none;
}}
#{cid} .saju-mc-center-glow {{
  position: absolute; inset: -28px; border-radius: 50%;
  background: radial-gradient(circle, var(--dm-color) 0%, transparent 68%);
  opacity: 0.45;
  animation: {cid}-pulse 2.8s ease-in-out infinite;
}}
@keyframes {cid}-pulse {{
  0%, 100% {{ transform: scale(0.92); opacity: 0.35; }}
  50% {{ transform: scale(1.08); opacity: 0.55; }}
}}
#{cid} .saju-mc-center-inner {{
  position: relative;
  width: clamp(72px, 22vw, 96px);
  height: clamp(72px, 22vw, 96px);
  border-radius: 50%;
  border: 2px solid var(--mc-border);
  background: radial-gradient(circle at 35% 30%, rgba(255,255,255,0.12), rgba(10,10,20,0.92));
  box-shadow: 0 0 28px var(--dm-color), inset 0 0 20px rgba(0,0,0,0.4);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 0.35rem;
}}
#{cid}[data-theme="hanji"] .saju-mc-center-inner {{
  background: radial-gradient(circle at 35% 30%, #fffdf8, #e8d4b0);
  box-shadow: 0 0 20px rgba(139,90,43,0.25), inset 0 0 12px rgba(255,255,255,0.5);
}}
#{cid} .saju-mc-dm-label {{
  font-size: 8px; letter-spacing: 0.06em; color: #e8c547; font-weight: 700;
}}
#{cid}[data-theme="hanji"] .saju-mc-dm-label {{ color: #8b5a2b; }}
#{cid} .saju-mc-dm-stem {{
  font-size: clamp(1.6rem, 6vw, 2.2rem); font-weight: 900; color: #fff8ec; line-height: 1;
  font-family: "Noto Serif SC", "Noto Serif KR", serif;
}}
#{cid}[data-theme="hanji"] .saju-mc-dm-stem {{ color: #2c1810; }}
#{cid} .saju-mc-dm-meta {{
  font-size: 9px; color: var(--mc-muted); margin-top: 0.15rem;
}}
@media (max-width: 520px) {{
  #{cid}.saju-master-chart {{
    min-height: 560px;
    height: auto;
    max-width: 100%;
    margin-bottom: 0.35rem;
  }}
  #{cid} .saju-mc-stage {{
    padding-top: 36px;
    padding-bottom: 12px;
  }}
  #{cid} .saju-mc-pillars {{
    width: 94%;
    max-width: none;
    gap: 0.08rem;
    padding-bottom: 10%;
    z-index: 22;
  }}
  #{cid} .saju-mc-pillar {{
    min-height: 2.75rem;
    padding: 0.15rem 0;
  }}
  #{cid} .saju-mc-pillar .saju-mc-popover {{
    display: none !important;
  }}
  #{cid}.has-mobile-dock-open {{
    padding-bottom: min(46vh, 300px);
  }}
  #{cid} .saju-mc-pop-hidden li {{
    grid-template-columns: 1.1em minmax(0, 1fr);
    gap: 0.2rem 0.35rem;
  }}
  #{cid} .saju-mc-hs-meta,
  #{cid} .saju-mc-hs-ten,
  #{cid} .saju-mc-hs-hint {{
    grid-column: 2;
  }}
  #{cid} .saju-mc-pillar-svg {{
    max-height: 148px;
  }}
  #{cid} .saju-mc-glyph {{
    font-size: 20px;
  }}
  #{cid} .saju-mc-glyph--branch {{
    font-size: 18px;
  }}
  #{cid} .saju-mc-center {{
    top: 44%;
  }}
  #{cid} .saju-mc-oheng {{
    width: 96%;
    left: 2%;
  }}
  #{cid} .saju-mc-toolbar {{
    top: 6px;
    right: 6px;
    flex-wrap: wrap;
    max-width: calc(100% - 12px);
    justify-content: flex-end;
  }}
  #{cid} .saju-mc-theme-btn {{
    font-size: 9px;
    padding: 3px 7px;
  }}
}}
</style>
<script>
(function() {{
  const root = document.getElementById({json.dumps(cid)});
  if (!root) return;

  const THEME_KEY = "saju_mc_theme";
  function applyTheme(name) {{
    const t = name === "hanji" ? "hanji" : "neon";
    root.setAttribute("data-theme", t);
    root.querySelectorAll("[data-theme-set]").forEach((btn) => {{
      btn.classList.toggle("is-active", btn.getAttribute("data-theme-set") === t);
    }});
    try {{ localStorage.setItem(THEME_KEY, t); }} catch (e) {{}}
  }}
  const saved = (() => {{
    try {{ return localStorage.getItem(THEME_KEY); }} catch (e) {{ return null; }}
  }})();
  if (saved === "hanji" || saved === "neon") applyTheme(saved);
  root.querySelectorAll("[data-theme-set]").forEach((btn) => {{
    btn.addEventListener("click", () => applyTheme(btn.getAttribute("data-theme-set")));
  }});

  const MOBILE_MQ = window.matchMedia("(max-width: 520px)");

  function clearPopInline(pop) {{
    pop.style.top = "";
    pop.style.left = "";
    pop.style.right = "";
    pop.style.width = "";
    pop.style.maxWidth = "";
  }}

  function positionMcPopover(pillar) {{
    const pop = pillar.querySelector(".saju-mc-popover");
    if (!pop) return;
    pop.classList.remove(
      "saju-mc-popover--above",
      "saju-mc-popover--below",
      "saju-mc-popover--edge-left",
      "saju-mc-popover--edge-right",
      "saju-mc-popover--viewport"
    );
    clearPopInline(pop);

    pop.classList.add("saju-mc-popover--below");

    if (MOBILE_MQ.matches) {{
      pop.classList.add("saju-mc-popover--viewport");
      const margin = 12;
      const pr = pillar.getBoundingClientRect();
      const vh = window.innerHeight || document.documentElement.clientHeight;
      pop.style.left = margin + "px";
      pop.style.right = margin + "px";
      pop.style.width = "auto";
      let top = pr.bottom + 8;
      const popH = pop.offsetHeight || 220;
      if (top + popH > vh - margin) {{
        top = Math.max(margin, pr.top - popH - 8);
      }}
      pop.style.top = Math.round(top) + "px";
      return;
    }}

    const idx = parseInt(pillar.getAttribute("data-pillar-idx") || "2", 10);
    if (idx === 0) pop.classList.add("saju-mc-popover--edge-left");
    if (idx === 3) pop.classList.add("saju-mc-popover--edge-right");
  }}

  const dock = root.querySelector(".saju-mc-mobile-dock");
  let hoverLeaveTimer = 0;

  function closeAllPillars() {{
    root.querySelectorAll(".saju-mc-pillar.is-pop-open").forEach((p) => {{
      p.classList.remove("is-pop-open");
    }});
    root.classList.remove("has-mobile-dock-open");
    if (dock) {{
      dock.innerHTML = "";
      dock.setAttribute("aria-hidden", "true");
    }}
    root.querySelectorAll(".saju-mc-popover").forEach(clearPopInline);
  }}

  function showMobileDock(pillar) {{
    const pop = pillar.querySelector(".saju-mc-popover");
    if (!dock || !pop) return;
    dock.innerHTML = pop.innerHTML;
    dock.setAttribute("aria-hidden", "false");
    root.classList.add("has-mobile-dock-open");
    requestAnimationFrame(() => {{
      try {{
        dock.scrollIntoView({{ block: "nearest", behavior: "smooth" }});
      }} catch (e) {{}}
    }});
  }}

  function openPillar(pillar) {{
    pillar.classList.add("is-pop-open");
    if (MOBILE_MQ.matches) {{
      showMobileDock(pillar);
      return;
    }}
    positionMcPopover(pillar);
    requestAnimationFrame(() => {{
      positionMcPopover(pillar);
      const pop = pillar.querySelector(".saju-mc-popover");
      if (pop) {{
        try {{
          pop.scrollIntoView({{ block: "nearest", inline: "nearest", behavior: "smooth" }});
        }} catch (e) {{}}
      }}
    }});
  }}

  function activatePillar(pillar) {{
    closeAllPillars();
    openPillar(pillar);
  }}

  root.querySelectorAll(".saju-mc-pillar").forEach((pillar) => {{
    pillar.addEventListener("pointerenter", () => {{
      if (hoverLeaveTimer) {{
        clearTimeout(hoverLeaveTimer);
        hoverLeaveTimer = 0;
      }}
      activatePillar(pillar);
    }});
    pillar.addEventListener("pointerleave", () => {{
      if (MOBILE_MQ.matches) return;
      if (hoverLeaveTimer) clearTimeout(hoverLeaveTimer);
      hoverLeaveTimer = window.setTimeout(() => {{
        const open = root.querySelector(".saju-mc-pillar.is-pop-open");
        if (open === pillar) closeAllPillars();
      }}, 320);
    }});
    pillar.addEventListener("focus", () => {{
      activatePillar(pillar);
    }});
    pillar.addEventListener("keydown", (ev) => {{
      if (ev.key === "Enter" || ev.key === " ") {{
        ev.preventDefault();
        activatePillar(pillar);
      }}
    }});
  }});
  root.addEventListener("click", (ev) => {{
    if (ev.target.closest && ev.target.closest(".saju-mc-pillar")) return;
    if (ev.target.closest && ev.target.closest(".saju-mc-mobile-dock")) return;
    closeAllPillars();
  }});

  window.addEventListener("resize", () => {{
    const open = root.querySelector(".saju-mc-pillar.is-pop-open");
    if (!open) return;
    if (MOBILE_MQ.matches) showMobileDock(open);
    else {{
      closeAllPillars();
      open.classList.add("is-pop-open");
      positionMcPopover(open);
    }}
  }});
  if (MOBILE_MQ.addEventListener) {{
    MOBILE_MQ.addEventListener("change", () => {{
      const open = root.querySelector(".saju-mc-pillar.is-pop-open");
      if (!open) return;
      if (MOBILE_MQ.matches) showMobileDock(open);
      else {{
        root.classList.remove("has-mobile-dock-open");
        if (dock) {{
          dock.innerHTML = "";
          dock.setAttribute("aria-hidden", "true");
        }}
        positionMcPopover(open);
      }}
    }});
  }}

  const cfg = {json.dumps(particle_cfg, ensure_ascii=False)};
  const canvas = root.querySelector(".saju-mc-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  let w = 0, h = 0, parts = [], raf = 0;
  const ELEMENTS = ["木","火","土","金","水"];
  function resize() {{
    const r = root.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    w = Math.max(1, Math.floor(r.width));
    h = Math.max(1, Math.floor(r.height));
    canvas.width = Math.floor(w * dpr);
    canvas.height = Math.floor(h * dpr);
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }}
  function spawn() {{
    const total = ELEMENTS.reduce((s, e) => s + (cfg.counts[e] || 0), 0) || 1;
    let pick = Math.random() * total;
    let el = ELEMENTS[0];
    for (const e of ELEMENTS) {{
      pick -= cfg.counts[e] || 0;
      if (pick <= 0) {{ el = e; break; }}
    }}
    const col = cfg.colors[el] || "#888";
    const x = w * (0.12 + Math.random() * 0.76);
    const y = h * (0.55 + Math.random() * 0.42);
    let vy = -0.35 - Math.random() * 0.9;
    let vx = (Math.random() - 0.5) * 0.45;
    let life = 80 + Math.random() * 100;
    let size = 1.2 + Math.random() * 2.2;
    const hanji = root.getAttribute("data-theme") === "hanji";
    if (hanji) {{ size *= 0.85; }}
    if (el === "火") {{ vy = -0.6 - Math.random() * 1.2; size *= 1.15; }}
    if (el === "水") {{ vy = 0.25 + Math.random() * 0.5; vx *= 0.6; }}
    if (el === "土") {{ vy *= 0.55; vx *= 0.35; }}
    parts.push({{ x, y, vx, vy, life, size, col, kind: el }});
    if (parts.length > 120) parts.shift();
  }}
  function draw() {{
    ctx.clearRect(0, 0, w, h);
    for (const p of parts) {{
      p.life -= 1;
      p.x += p.vx;
      p.y += p.vy;
      const a = Math.max(0, p.life / 120);
      ctx.globalAlpha = a * (root.getAttribute("data-theme") === "hanji" ? 0.5 : 0.75);
      if (p.kind === "火") {{
        const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.size * 3);
        g.addColorStop(0, "#fff7ed");
        g.addColorStop(0.4, p.col);
        g.addColorStop(1, "transparent");
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size * 2.5, 0, Math.PI * 2);
        ctx.fill();
      }} else if (p.kind === "木") {{
        ctx.fillStyle = p.col;
        ctx.beginPath();
        ctx.ellipse(p.x, p.y, p.size * 0.8, p.size * 1.6, 0, 0, Math.PI * 2);
        ctx.fill();
      }} else {{
        ctx.fillStyle = p.col;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
      }}
    }}
    parts = parts.filter((p) => p.life > 0 && p.y > -20 && p.y < h + 20);
    if (Math.random() < 0.45) spawn();
    raf = requestAnimationFrame(draw);
  }}
  resize();
  draw();
  window.addEventListener("resize", resize);
}})();
</script>
"""


def render_gapja_master_chart(
    u_gapja: list[str],
    *,
    height: int | None = None,
    theme: str | None = None,
) -> None:
    """Streamlit에 메인 사주 차트를 렌더합니다. 기본 테마는 네온(다크)."""
    if not u_gapja or len(u_gapja) < 3:
        st.caption("사주 간지가 준비되면 메인 차트가 표시됩니다.")
        return

    if "gapja_chart_theme" not in st.session_state:
        st.session_state.gapja_chart_theme = "neon"
    theme_pick = theme
    if theme_pick is None:
        saved = str(st.session_state.get("gapja_chart_theme") or "neon")
        theme_pick = "hanji" if saved == "hanji" else "neon"
    else:
        theme_pick = "hanji" if str(theme_pick).strip().lower() == "hanji" else "neon"
    st.session_state.gapja_chart_theme = theme_pick

    # 모바일 하단 설명 패널(dock)이 잘리지 않도록 최소 높이 확보
    iframe_h = max(int(height) if height is not None else 700, 620)
    html_body = build_gapja_master_chart_html(list(u_gapja), theme=str(theme_pick))
    components.html(html_body, height=iframe_h, scrolling=False)
