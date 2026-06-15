"""우리나라 24절기 — 날짜(KST) 기준 현재 절기·설명·준비사항."""

from __future__ import annotations

import datetime
import html
import json
import uuid
from dataclasses import dataclass
from functools import lru_cache
from typing import Sequence
from zoneinfo import ZoneInfo

_KST = ZoneInfo("Asia/Seoul")


@dataclass(frozen=True)
class SolarTerm24:
    key: str
    name_ko: str
    name_hanja: str
    lon_deg: float
    approx_md: tuple[int, int]
    summary: str
    description: str
    prep_items: tuple[str, ...]


# 태양 황경 기준 24절기 (소한=285° … 동지=270°)
_TERMS: tuple[SolarTerm24, ...] = (
    SolarTerm24(
        "sohan",
        "소한",
        "小寒",
        285.0,
        (1, 6),
        "한겨울로 들어가며 몸을 차게 만드는 시기입니다.",
        "기온이 떨어지고 낮이 짧아집니다. 무리한 야외 활동보다 실내 건강·수면 리듬을 먼저 챙기는 것이 좋습니다.",
        ("외출 시 방한·보온", "족욕·스트레칭", "따뜻한 국물·수분"),
    ),
    SolarTerm24(
        "daehan",
        "대한",
        "大寒",
        300.0,
        (1, 20),
        "겨울의 기운이 가장 강한 때입니다.",
        "몸의 에너지 소모가 커지기 쉬우니 과로를 줄이고, 식사·수면을 규칙적으로 맞추면 컨디션이 덜 흔들립니다.",
        ("실내 환기·가습", "비타민·단백질 균형", "무리한 다이어트 자제"),
    ),
    SolarTerm24(
        "ipchun",
        "입춘",
        "立春",
        315.0,
        (2, 4),
        "봄의 문이 열리는 절기입니다.",
        "새 싹이 돋는 기운이므로 계획을 세우고 작은 실천부터 시작하기 좋습니다. 감정도 서서히 밝아질 수 있습니다.",
        ("옷차림 점진적 전환", "가벼운 운동·산책", "올해 목표 한 줄 정리"),
    ),
    SolarTerm24(
        "usu",
        "우수",
        "雨水",
        330.0,
        (2, 19),
        "눈이 그치고 비·습기가 늘기 쉬운 때입니다.",
        "몸이 무겁게 느껴질 수 있어 붓기·감기를 예방하는 생활이 도움이 됩니다.",
        ("우산·방수", "습기·곰팡이 점검", "따뜻한 차·수분"),
    ),
    SolarTerm24(
        "gyeongchip",
        "경칩",
        "驚蟄",
        345.0,
        (3, 6),
        "만물이 깨어나 활동이 늘어나는 시기입니다.",
        "일·관계에서도 움직임이 커질 수 있어 일정을 넉넉히 잡고 컨디션을 자주 확인하세요.",
        ("알레르기·피부 관리", "수면 시간 확보", "급한 결정은 한 박자 늦추기"),
    ),
    SolarTerm24(
        "chunbun",
        "춘분",
        "春分",
        0.0,
        (3, 21),
        "낮과 밤의 길이가 비슷해지는 균형의 절기입니다.",
        "관계·일의 균형을 맞추기 좋은 때입니다. 지나친 한쪽 치우침을 조정해 보세요.",
        ("가벼운 정리·환기", "함께하는 식사·대화", "지출·수입 균형 점검"),
    ),
    SolarTerm24(
        "cheongmyeong",
        "청명",
        "清明",
        15.0,
        (4, 5),
        "하늘이 맑고 기운이 산뜻한 시기입니다.",
        "쌓인 일을 정리하고 마음을 가볍게 하는 데 잘 맞습니다. 봄나들이·성묘도 이 절기에 겹칩니다.",
        ("대청소·정리", "환기·햇빛 쬐기", "존중·감사의 마음 나누기"),
    ),
    SolarTerm24(
        "gogu",
        "곡우",
        "穀雨",
        30.0,
        (4, 20),
        "농사에 비가 내려 곡식이 자라는 때입니다.",
        "성장·학습·콘텐츠 제작에도 기운이 붙기 쉬운 시기입니다. 꾸준히 쌓아 두면 후반에 도움이 됩니다.",
        ("씨앗·계획 심기", "기록·백업", "수분·비타민"),
    ),
    SolarTerm24(
        "ipha",
        "입하",
        "立夏",
        45.0,
        (5, 6),
        "여름이 시작되는 절기입니다.",
        "활동량이 늘기 쉬우니 수분·전해질을 챙기고, 감정의 과열은 식사·수면으로 잡아 주세요.",
        ("얇은 옷·모자", "물·이온음료", "점심 후 가벼운 휴식"),
    ),
    SolarTerm24(
        "soman",
        "소만",
        "小滿",
        60.0,
        (5, 21),
        "알이 차오르듯 기대가 커지는 때입니다.",
        "욕심을 앞세우기보다 확인·검증을 먼저 하면 실수가 줄어듭니다.",
        ("계약·약속 재확인", "지출 상한선", "피부·자외선 대비"),
    ),
    SolarTerm24(
        "mangjong",
        "망종",
        "芒種",
        75.0,
        (6, 6),
        "씨를 뿌리고 수확을 준비하는 바쁜 시기입니다.",
        "일정이 겹치기 쉬우니 우선순위를 정하고, 몸은 무리하지 않는 편이 좋습니다.",
        ("할 일 목록 정리", "팀·가족 역할 분담", "충분한 수면"),
    ),
    SolarTerm24(
        "haji",
        "하지",
        "夏至",
        90.0,
        (6, 21),
        "낮이 가장 길고 양(陽)의 기운이 절정입니다.",
        "에너지는 높지만 소모도 큽니다. 냉음식·냉방 과다는 피하고, 저녁에는 체온을 낮추는 루틴을 두세요.",
        ("모자·선크림", "시원한 저녁 식사", "늦은 카페인 자제"),
    ),
    SolarTerm24(
        "soseo",
        "소서",
        "小暑",
        105.0,
        (7, 7),
        "본격적인 더위가 시작됩니다.",
        "더위·습기로 피로가 쌓이기 쉬우니 일정에 휴식 구간을 넣으세요.",
        ("실내 온도 관리", "가벼운 식사", "수영·샤워로 체온 조절"),
    ),
    SolarTerm24(
        "daeseo",
        "대서",
        "大暑",
        120.0,
        (7, 23),
        "여름 더위가 가장 강한 때입니다.",
        "감정·소화·수면이 흔들리기 쉬우니 무리한 일정을 줄이고, 수분·전해질을 자주 보충하세요.",
        ("이열사 음식", "에어컨·선풍기 점검", "오후 야외 활동 줄이기"),
    ),
    SolarTerm24(
        "ipchu",
        "입추",
        "立秋",
        135.0,
        (8, 8),
        "가을이 시작되는 절기입니다.",
        "결실·정리의 기운이므로 지금까지 한 일을 돌아보고 다음 분기 계획을 세우기 좋습니다.",
        ("옷차림 전환", "가계·재정 점검", "가벼운 독서·학습"),
    ),
    SolarTerm24(
        "cheoseo",
        "처서",
        "處暑",
        150.0,
        (8, 23),
        "더위가 누그러지기 시작합니다.",
        "몸과 마음이 안정되므로 미뤄 둔 정리·대화를 진행하기 좋습니다.",
        ("장 보관·냉동 정리", "수면 리듬 조정", "관계 연락"),
    ),
    SolarTerm24(
        "baekro",
        "백로",
        "白露",
        165.0,
        (9, 8),
        "아침 이슬이 맺히고 차가워지는 때입니다.",
        "건조·호흡기·피부가 예민해질 수 있어 보습·가습에 신경 쓰세요.",
        ("보습·가습", "목·감기 예방", "아침·저녁 외투"),
    ),
    SolarTerm24(
        "chubun",
        "추분",
        "秋分",
        180.0,
        (9, 23),
        "다시 낮과 밤이 비슷해지는 균형의 절기입니다.",
        "수확·감사의 기운이 강합니다. 관계·일의 균형을 맞추고 마음을 정리하세요.",
        ("감사 인사", "제철 음식", "지출·저축 균형"),
    ),
    SolarTerm24(
        "hanro",
        "한로",
        "寒露",
        195.0,
        (10, 8),
        "찬 이슬이 내리며 가을이 깊어집니다.",
        "체온이 떨어지기 쉬우니 따뜻한 차·식사와 가벼운 운동으로 순환을 돕습니다.",
        ("따뜻한 음료", "목·어깨 스트레칭", "면역·수면"),
    ),
    SolarTerm24(
        "sanggang",
        "상강",
        "霜降",
        210.0,
        (10, 24),
        "서리가 내릴 수 있는 시기입니다.",
        "겨울 준비를 시작하기 좋습니다. 무리한 확장보다 내실·저장에 초점을 맞추세요.",
        ("겨울용품 점검", "난방·단열", "비상약·배터리"),
    ),
    SolarTerm24(
        "ipdong",
        "입동",
        "立冬",
        225.0,
        (11, 7),
        "겨울이 시작되는 절기입니다.",
        "에너지를 아끼고 저장하는 시기입니다. 새 프로젝트는 작게 시작해 검증하세요.",
        ("보온·난방", "영양 식사", "일정 여유 두기"),
    ),
    SolarTerm24(
        "soseol",
        "소설",
        "小雪",
        240.0,
        (11, 22),
        "눈이 내리기 시작할 수 있는 때입니다.",
        "교통·미끄럼·건조에 대비하고, 마음은 차분히 유지하는 것이 좋습니다.",
        ("미끄럼 방지 신발", "가습·보습", "운전·이동 시간 여유"),
    ),
    SolarTerm24(
        "daeseol",
        "대설",
        "大雪",
        255.0,
        (12, 7),
        "눈이 많이 내릴 수 있는 시기입니다.",
        "외출·이동이 어려울 수 있으니 집 안에서 할 일을 정리하고, 가족·휴식 시간을 확보하세요.",
        ("비상 식량·물", "난방 안전 점검", "실내 활동·독서"),
    ),
    SolarTerm24(
        "dongji",
        "동지",
        "冬至",
        270.0,
        (12, 22),
        "낮이 가장 짧고 음(陰)이 절정인 뒤 다시 밝아지기 시작합니다.",
        "회복·모임·따뜻한 음식으로 기운을 보충하는 풍습이 있습니다. 새 시작을 마음속으로 준비하기도 좋습니다.",
        ("팥죽·따뜻한 국물", "가족·친지 안부", "일찍 취침·휴식"),
    ),
)


def _term_by_key(key: str) -> SolarTerm24:
    for t in _TERMS:
        if t.key == key:
            return t
    return _TERMS[0]


def _fallback_index_for_date(d: datetime.date) -> int:
    """ephem 없을 때 대략적인 절기 인덱스(월·일)."""
    md_list = [(t.approx_md[0], t.approx_md[1], i) for i, t in enumerate(_TERMS)]
    candidates: list[tuple[datetime.date, int]] = []
    for m, day, idx in md_list:
        try:
            candidates.append((datetime.date(d.year, m, day), idx))
        except ValueError:
            continue
    candidates.sort(key=lambda x: x[0])
    current = 0
    for t_date, idx in candidates:
        if t_date <= d:
            current = idx
        else:
            break
    return current


@lru_cache(maxsize=64)
def _jeolgi24_boundaries_kst(year: int) -> tuple[tuple[datetime.datetime, str], ...]:
    """해당 연도 24절기 입기 시각(KST). ephem 실패 시 빈 튜플."""
    try:
        import ephem as ephem_mod  # type: ignore

        from saju_app.core.calculations import (  # noqa: PLC0415
            _ang_diff_deg,
            _ephem_sun_ecliptic_lon_deg,
        )
    except Exception:
        return ()

    kst = _KST
    out: list[tuple[datetime.datetime, str]] = []

    for term in _TERMS:
        target_lon = term.lon_deg
        approx_local = datetime.datetime(
            year, term.approx_md[0], term.approx_md[1], 12, 0, tzinfo=kst
        )
        center_utc = approx_local.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        step = datetime.timedelta(hours=2)
        start = center_utc - datetime.timedelta(days=4)
        end = center_utc + datetime.timedelta(days=4)
        prev_t = start
        prev_f = _ang_diff_deg(_ephem_sun_ecliptic_lon_deg(ephem_mod, prev_t), target_lon)
        t = start + step
        bracket: tuple[datetime.datetime, datetime.datetime] | None = None
        while t <= end:
            f = _ang_diff_deg(_ephem_sun_ecliptic_lon_deg(ephem_mod, t), target_lon)
            if (prev_f <= 0 <= f) or (f <= 0 <= prev_f):
                bracket = (prev_t, t)
                break
            prev_t, prev_f = t, f
            t += step
        if not bracket:
            continue
        lo, hi = bracket
        for _ in range(50):
            mid = lo + (hi - lo) / 2
            fmid = _ang_diff_deg(_ephem_sun_ecliptic_lon_deg(ephem_mod, mid), target_lon)
            flo = _ang_diff_deg(_ephem_sun_ecliptic_lon_deg(ephem_mod, lo), target_lon)
            if (flo <= 0 <= fmid) or (fmid <= 0 <= flo):
                hi = mid
            else:
                lo = mid
            if (hi - lo).total_seconds() < 1:
                break
        best_utc = hi
        best_kst = best_utc.replace(tzinfo=datetime.timezone.utc).astimezone(kst)
        out.append((best_kst, term.key))

    out.sort(key=lambda x: x[0])
    return tuple(out)


@dataclass(frozen=True)
class CurrentSolarTerm24:
    term: SolarTerm24
    started_at: datetime.datetime | None
    ends_at: datetime.datetime | None
    period_label: str


def resolve_current_solar_term(
    on: datetime.date | datetime.datetime | None = None,
) -> CurrentSolarTerm24:
    """KST 기준 오늘(또는 지정 시각)의 24절기."""
    if on is None:
        dt = datetime.datetime.now(tz=_KST)
    elif isinstance(on, datetime.datetime):
        dt = on.astimezone(_KST) if on.tzinfo else on.replace(tzinfo=_KST)
    else:
        dt = datetime.datetime(on.year, on.month, on.day, 12, 0, tzinfo=_KST)

    d = dt.date()
    y = d.year
    boundaries: list[tuple[datetime.datetime, str]] = []
    for yr in (y - 1, y, y + 1):
        boundaries.extend(list(_jeolgi24_boundaries_kst(yr)))
    boundaries.sort(key=lambda x: x[0])

    if boundaries:
        idx = 0
        for i, (t0, _) in enumerate(boundaries):
            if t0 <= dt:
                idx = i
            else:
                break
        _, key = boundaries[idx]
        term = _term_by_key(key)
        started = boundaries[idx][0]
        next_start = boundaries[idx + 1][0] if idx + 1 < len(boundaries) else None
        period = _format_period(started, next_start)
        return CurrentSolarTerm24(
            term=term,
            started_at=started,
            ends_at=next_start,
            period_label=period,
        )

    fi = _fallback_index_for_date(d)
    term = _TERMS[fi]
    nxt = _TERMS[(fi + 1) % len(_TERMS)]
    period = _approx_period_label(d, term, nxt)
    return CurrentSolarTerm24(
        term=term,
        started_at=None,
        ends_at=None,
        period_label=period,
    )


def _format_period(
    start: datetime.datetime | None,
    end: datetime.datetime | None,
) -> str:
    if start is None:
        return "오늘 기준"
    s = start.astimezone(_KST).strftime("%m월 %d일")
    if end is None:
        return f"{s}~"
    e = (end.astimezone(_KST) - datetime.timedelta(days=1)).strftime("%m월 %d일")
    return f"{s} ~ {e}"


def _approx_period_label(
    d: datetime.date,
    term: SolarTerm24,
    nxt: SolarTerm24,
) -> str:
    try:
        s = datetime.date(d.year, term.approx_md[0], term.approx_md[1])
        e = datetime.date(d.year, nxt.approx_md[0], nxt.approx_md[1])
        if e <= s:
            e = datetime.date(d.year + 1, nxt.approx_md[0], nxt.approx_md[1])
        return f"{s.month}월 {s.day}일 ~ {e.month}월 {e.day}일경"
    except ValueError:
        return "절기 기간(대략)"


_SPRING_KEYS = frozenset(
    {"ipchun", "usu", "gyeongchip", "chunbun", "cheongmyeong", "gogu"}
)
_SUMMER_KEYS = frozenset({"ipha", "soman", "mangjong", "haji", "soseo", "daeseo"})
_AUTUMN_KEYS = frozenset(
    {"ipchu", "cheoseo", "baekro", "chubun", "hanro", "sanggang"}
)


def _season_meta(key: str) -> tuple[str, str, str]:
    """절기 계절 — (강조색, 보조색, 라벨)."""
    if key in _SPRING_KEYS:
        return "#2d6a4f", "#86efac", "봄"
    if key in _SUMMER_KEYS:
        return "#c2410c", "#fbbf24", "여름"
    if key in _AUTUMN_KEYS:
        return "#92400e", "#d97706", "가을"
    return "#1e3a5f", "#94a3b8", "겨울"


def _hx(s: str) -> str:
    return html.escape(str(s or ""), quote=True)


def _s24_popover(title: str, body: str) -> str:
    """화면에 그리지 않고 ``<template>``에만 담아 하단 도크로 복사."""
    return (
        f'<template class="s24-pop-src">'
        f'<p class="s24-pop-title">{_hx(title)}</p>'
        f'<div class="s24-pop-body">{body}</div>'
        "</template>"
    )


def _s24_pillar_block(
    frame_id: str,
    idx: int,
    *,
    slot_ko: str,
    slot_han: str,
    color: str,
    glyph_top: str,
    glyph_bot: str,
    foot: str,
    popover: str,
    highlight: bool = False,
) -> str:
    grad_id = f"{frame_id}_g{idx}"
    cls = "s24-pillar s24-pillar--day" if highlight else "s24-pillar"
    return f"""
<div class="{cls}" style="--s24-color:{_hx(color)};" tabindex="0" data-s24-idx="{idx}">
  <div class="s24-slot">{_hx(slot_ko)}</div>
  <div class="s24-han" lang="zh-Hant">{_hx(slot_han)}</div>
  <div class="s24-pillar-body">
    <svg class="s24-pillar-svg" viewBox="0 0 72 200" aria-hidden="true">
      <defs>
        <linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="{_hx(color)}" stop-opacity="0.95"/>
          <stop offset="55%" stop-color="{_hx(color)}" stop-opacity="0.38"/>
          <stop offset="100%" stop-color="#2c1810" stop-opacity="0.92"/>
        </linearGradient>
        <filter id="{grad_id}_sh" x="-30%" y="-10%" width="160%" height="120%">
          <feDropShadow dx="0" dy="6" stdDeviation="5" flood-color="#3d2f1f" flood-opacity="0.35"/>
        </filter>
      </defs>
      <rect x="12" y="6" width="48" height="188" rx="12" fill="url(#{grad_id})"
        stroke="{_hx(color)}" stroke-opacity="0.6" stroke-width="1.4" filter="url(#{grad_id}_sh)"/>
    </svg>
    <div class="s24-glyphs-overlay" lang="zh-Hant" aria-hidden="true">
      <span class="s24-glyph-t">{_hx(glyph_top)}</span>
      <span class="s24-glyph-b">{_hx(glyph_bot)}</span>
    </div>
  </div>
  <div class="s24-foot">{_hx(foot)}</div>
  {popover}
</div>
""".strip()


def solar_term_frame_html(
    current: CurrentSolarTerm24 | None = None,
    *,
    cid: str | None = None,
) -> str:
    """홈 화면 — 사주 4주 차트형 입체 기둥 + 포인터(호버/터치) 서브 메뉴."""
    cur = current or resolve_current_solar_term()
    t = cur.term
    frame_id = cid or f"s24_{uuid.uuid4().hex[:10]}"
    accent, accent_soft, _season = _season_meta(t.key)
    han = t.name_hanja
    g_top = han[0] if han else "節"
    g_bot = han[1] if len(han) > 1 else (t.name_ko[:1] if t.name_ko else "氣")

    prep_list = "".join(f"<li>{_hx(x)}</li>" for x in t.prep_items)
    prep_pop = _s24_popover(
        "준비사항",
        f'<ul class="s24-pop-list">{prep_list}</ul>',
    )
    pop_term = _s24_popover(
        f"{t.name_ko} · {t.name_hanja}",
        f'<p class="s24-pop-p"><b>{_hx(cur.period_label)}</b></p>'
        f'<p class="s24-pop-p">{_hx(t.summary)}</p>',
    )
    pop_summary = _s24_popover("한 줄 요지", f'<p class="s24-pop-p">{_hx(t.summary)}</p>')
    pop_desc = _s24_popover("절기 설명", f'<p class="s24-pop-p">{_hx(t.description)}</p>')

    pillars = [
        _s24_pillar_block(
            frame_id,
            0,
            slot_ko="절기",
            slot_han="節氣",
            color=accent,
            glyph_top=g_top,
            glyph_bot=g_bot,
            foot=cur.period_label[:8] + ("…" if len(cur.period_label) > 8 else ""),
            popover=pop_term,
            highlight=True,
        ),
        _s24_pillar_block(
            frame_id,
            1,
            slot_ko="요지",
            slot_han="要旨",
            color=accent_soft,
            glyph_top="要",
            glyph_bot="旨",
            foot="핵심",
            popover=pop_summary,
        ),
        _s24_pillar_block(
            frame_id,
            2,
            slot_ko="설명",
            slot_han="說明",
            color="#8b5a2b",
            glyph_top="說",
            glyph_bot="明",
            foot="자세히",
            popover=pop_desc,
        ),
        _s24_pillar_block(
            frame_id,
            3,
            slot_ko="준비",
            slot_han="準備",
            color="#475569",
            glyph_top="準",
            glyph_bot="備",
            foot=f"{len(t.prep_items)}가지",
            popover=prep_pop,
        ),
    ]
    ring_svg = f"""
<svg class="s24-ring" viewBox="0 0 400 400" aria-hidden="true">
  <circle cx="200" cy="200" r="156" fill="none" stroke="{_hx(accent)}" stroke-opacity="0.22" stroke-width="1.2"/>
  <circle cx="200" cy="200" r="118" fill="none" stroke="rgba(139,90,43,0.28)" stroke-width="0.8" stroke-dasharray="4 6"/>
</svg>
""".strip()

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
</head>
<body style="margin:0;padding:0;">
<div id="{_hx(frame_id)}" class="saju-solar24-master" data-theme="hanji" role="region" aria-label="{_hx(t.name_ko)} 절기">
  <p class="s24-flow-title">24절기 에너지 흐름</p>
  <div class="s24-stage">
    {ring_svg}
    <div class="s24-center" style="--s24-accent:{_hx(accent)};">
      <div class="s24-center-glow" aria-hidden="true"></div>
      <div class="s24-center-inner">
        <div class="s24-dm-label">節氣 · Solar Term</div>
        <div class="s24-dm-stem" lang="zh-Hant">{_hx(t.name_hanja)}</div>
        <div class="s24-dm-meta">{_hx(t.name_ko)} · {_hx(cur.period_label)}</div>
      </div>
    </div>
    <div class="s24-pillars">
      {''.join(pillars)}
    </div>
  </div>
  <div class="s24-detail-dock" id="{frame_id}_dock" aria-hidden="true" role="region" aria-label="기둥 상세 설명"></div>
  <p class="s24-hint">기둥 위에 커서·손가락을 올리면 설명이 바로 표시됩니다</p>
</div>
<style>
@import url("https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&display=swap");
#{frame_id}.saju-solar24-master {{
  --s24-text: #3d2f1f;
  --s24-muted: rgba(61, 47, 31, 0.72);
  --s24-border: rgba(139, 90, 43, 0.45);
  --s24-bg:
    radial-gradient(ellipse at 30% 18%, rgba(255,248,235,0.95) 0%, transparent 52%),
    linear-gradient(165deg, #f3e4c8 0%, #e8d4b0 42%, #dcc9a0 100%);
  --s24-pop-bg: rgba(255, 250, 240, 0.98);
  --s24-pop-border: rgba(139, 90, 43, 0.55);
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 520px;
  margin-left: auto;
  margin-right: auto;
  margin-bottom: 0.75rem;
  min-height: 480px;
  height: auto;
  border-radius: 18px;
  overflow: visible;
  background: var(--s24-bg);
  border: 1px solid var(--s24-border);
  box-shadow: 0 8px 28px rgba(80, 50, 20, 0.18), inset 0 0 80px rgba(255,255,255,0.35);
  font-family: "Pretendard", "Noto Sans KR", system-ui, sans-serif;
  color: var(--s24-text);
  box-sizing: border-box;
}}
#{frame_id} .s24-toolbar {{
  position: relative; z-index: 12;
  display: flex; align-items: center; justify-content: flex-end;
  padding: 8px 12px 2px;
}}
#{frame_id} .s24-toolbar-title {{ display: none !important; }}
#{frame_id} .s24-toolbar-badge {{
  font-size: 10px; padding: 4px 10px; border-radius: 999px;
  border: 1px solid var(--s24-border); background: rgba(255,255,255,0.55); font-weight: 700;
}}
#{frame_id} .s24-flow-title {{
  text-align: center; margin: 10px 0 2px; font-size: 13px; letter-spacing: 0.1em;
  color: var(--s24-text); font-weight: 800;
}}
#{frame_id} .s24-stage {{
  position: relative; z-index: 2; flex: 1 1 auto;
  display: flex; align-items: flex-end; justify-content: center;
  min-height: 300px; padding: 12px 0 10px; overflow: visible;
  box-sizing: border-box;
}}
#{frame_id} .s24-ring {{
  position: absolute; width: 92%; max-width: 380px; height: auto;
  top: 8%; left: 50%; transform: translateX(-50%); pointer-events: none; opacity: 0.9;
}}
#{frame_id} .s24-center {{
  position: absolute; left: 50%; top: 46%; transform: translate(-50%, -50%);
  z-index: 6; text-align: center; pointer-events: none;
}}
#{frame_id} .s24-center-glow {{
  position: absolute; inset: -28px; border-radius: 50%;
  background: radial-gradient(circle, color-mix(in srgb, var(--s24-accent) 45%, transparent) 0%, transparent 68%);
  opacity: 0.5; animation: {frame_id}-pulse 2.8s ease-in-out infinite;
}}
@keyframes {frame_id}-pulse {{
  0%, 100% {{ transform: scale(0.92); opacity: 0.35; }}
  50% {{ transform: scale(1.08); opacity: 0.58; }}
}}
#{frame_id} .s24-center-inner {{
  position: relative;
  width: clamp(72px, 22vw, 96px); height: clamp(72px, 22vw, 96px);
  border-radius: 50%; border: 2px solid var(--s24-border);
  background: radial-gradient(circle at 35% 28%, #fffdf8, #e8d4b0);
  box-shadow: 0 0 24px color-mix(in srgb, var(--s24-accent) 30%, transparent),
    inset 0 0 14px rgba(255,255,255,0.55);
  display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 0.3rem;
}}
#{frame_id} .s24-dm-label {{ font-size: 7px; font-weight: 700; color: #8b5a2b; letter-spacing: 0.04em; }}
#{frame_id} .s24-dm-stem {{
  font-size: clamp(1.35rem, 5vw, 1.75rem); font-weight: 900; line-height: 1;
  font-family: "Noto Serif SC", "Noto Serif KR", serif; color: #2c1810;
}}
#{frame_id} .s24-dm-meta {{ font-size: 8px; color: var(--s24-muted); margin-top: 0.2rem; line-height: 1.25; }}
#{frame_id} .s24-pillars {{
  position: relative; z-index: 8;
  display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.15rem; width: 78%; max-width: 380px;
  align-items: end; padding-bottom: 0; overflow: visible;
}}
#{frame_id} .s24-pillar {{
  text-align: center; min-width: 0; position: relative; cursor: pointer; outline: none;
}}
#{frame_id} .s24-pillar:hover,
#{frame_id} .s24-pillar:focus-visible,
#{frame_id} .s24-pillar.is-pop-open {{ z-index: 40; }}
#{frame_id} .s24-pillar:hover .s24-pillar-svg,
#{frame_id} .s24-pillar:focus-visible .s24-pillar-svg,
#{frame_id} .s24-pillar.is-pop-open .s24-pillar-svg {{
  filter: drop-shadow(0 8px 14px rgba(61,47,31,0.45)) drop-shadow(0 0 14px var(--s24-color));
  transform: translateY(-4px);
}}
#{frame_id} .s24-pillar--day .s24-pillar-svg {{
  filter: drop-shadow(0 6px 12px rgba(61,47,31,0.4)) drop-shadow(0 0 12px var(--s24-color));
  transform: scale(1.05);
}}
#{frame_id} .s24-slot {{ font-size: clamp(10px, 2.8vw, 12px); font-weight: 800; }}
#{frame_id} .s24-han {{ font-size: clamp(9px, 2.4vw, 11px); color: var(--s24-muted); margin-bottom: 0.12rem; }}
#{frame_id} .s24-foot {{ font-size: 9px; color: var(--s24-muted); margin-top: 2px; }}
#{frame_id} .s24-pillar-body {{
  position: relative; width: 100%; max-width: 76px; margin: 0 auto;
}}
#{frame_id} .s24-pillar-svg {{
  width: 100%; height: auto; display: block;
  transition: transform 0.2s ease, filter 0.2s ease;
}}
#{frame_id} .s24-glyphs-overlay {{
  position: absolute; left: 8%; right: 8%; top: 14%; bottom: 20%;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 0.2rem; pointer-events: none; z-index: 2;
}}
#{frame_id} .s24-glyph-t,
#{frame_id} .s24-glyph-b {{
  font-family: "Noto Serif SC", "Noto Serif TC", "Noto Serif KR", "Apple SD Gothic Neo", serif;
  font-weight: 900; line-height: 1;
  color: #2c1810;
  text-shadow:
    0 0 1px rgba(255, 248, 236, 0.95),
    0 1px 2px rgba(255, 248, 236, 0.75),
    0 2px 8px rgba(61, 47, 31, 0.25);
}}
#{frame_id} .s24-glyph-t {{ font-size: clamp(1.35rem, 5.2vw, 1.7rem); }}
#{frame_id} .s24-glyph-b {{
  font-size: clamp(1.1rem, 4.4vw, 1.45rem);
  color: #4a3728;
}}
#{frame_id} .s24-pop-src {{
  display: none;
}}
#{frame_id} .s24-pop-title {{
  font-size: 12px; font-weight: 800; margin: 0 0 0.35rem;
  border-bottom: 1px solid rgba(139,90,43,0.25); padding-bottom: 0.25rem;
}}
#{frame_id} .s24-pop-p {{ margin: 0.15rem 0; font-size: 11px; line-height: 1.48; }}
#{frame_id} .s24-pop-list {{ margin: 0.2rem 0 0; padding-left: 1rem; font-size: 11px; line-height: 1.45; }}
#{frame_id} .s24-footer {{
  flex-shrink: 0; z-index: 20;
  padding: 0.35rem 0.65rem 0.55rem;
  border-top: 1px solid rgba(139, 90, 43, 0.2);
  background: linear-gradient(180deg, rgba(255,250,240,0.55) 0%, rgba(243,228,200,0.92) 100%);
}}
#{frame_id} .s24-prep-bar {{
  position: relative; width: 100%;
  display: flex; flex-wrap: wrap; gap: 0.35rem; justify-content: center;
  pointer-events: none; z-index: 20;
  opacity: 1; visibility: visible;
}}
#{frame_id} .s24-bar {{
  font-size: 9px; padding: 0.28rem 0.55rem; border-radius: 999px;
  background: color-mix(in srgb, var(--bc) 14%, #fffaf3);
  border: 1px solid color-mix(in srgb, var(--bc) 35%, transparent);
  font-weight: 700;
  white-space: nowrap;
}}
#{frame_id} .s24-hint {{
  margin: 0.35rem 0 0; text-align: center;
  font-size: 9px; color: var(--s24-muted);
}}
#{frame_id} .s24-detail-dock {{
  display: none;
  flex-shrink: 0;
  width: min(320px, calc(100% - 24px));
  max-width: calc(100% - 24px);
  margin: 0.2rem auto 0.35rem;
  padding: 0.6rem 0.7rem;
  border-radius: 12px;
  background: var(--s24-pop-bg);
  border: 1px solid var(--s24-pop-border);
  box-shadow: 0 10px 28px rgba(61,47,31,0.28);
  max-height: min(38vh, 240px);
  overflow-x: hidden;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  box-sizing: border-box;
  text-align: left;
  z-index: 30;
}}
#{frame_id}.has-s24-dock-open .s24-detail-dock {{
  display: block;
}}
@media (max-width: 520px) {{
  #{frame_id}.saju-solar24-master {{
    min-height: 500px; height: auto; overflow: visible;
    padding-top: 6px; box-sizing: border-box;
  }}
  #{frame_id} .s24-stage {{
    min-height: 300px; padding: 8px 0 10px;
    align-items: flex-end; justify-content: center;
  }}
  #{frame_id} .s24-ring {{ top: 10%; width: 88%; max-width: 340px; opacity: 0.75; }}
  #{frame_id} .s24-center {{ top: 44%; }}
  #{frame_id} .s24-pillars {{ width: 94%; padding-bottom: 2px; }}
  #{frame_id} .s24-slot {{ font-size: clamp(9px, 2.6vw, 11px); line-height: 1.2; }}
  #{frame_id} .s24-han {{ margin-bottom: 0.08rem; }}
  #{frame_id} .s24-hint {{ display: none; }}
  #{frame_id} .s24-toolbar {{ padding: 8px 10px 0; }}
  #{frame_id} .s24-center-inner {{
    width: clamp(64px, 20vw, 88px);
    height: clamp(64px, 20vw, 88px);
  }}
}}
</style>
<script>
(function() {{
  const root = document.getElementById({json.dumps(frame_id)});
  if (!root) return;
  const dock = document.getElementById({json.dumps(frame_id + "_dock")});
  const pillarsWrap = root.querySelector(".s24-pillars");
  let closeTimer = null;

  function cancelClose() {{
    if (closeTimer) {{
      clearTimeout(closeTimer);
      closeTimer = null;
    }}
  }}

  function scheduleClose(delayMs) {{
    cancelClose();
    closeTimer = setTimeout(closeAll, delayMs);
  }}

  function closeAll() {{
    cancelClose();
    root.querySelectorAll(".s24-pillar.is-pop-open").forEach((p) => p.classList.remove("is-pop-open"));
    root.classList.remove("has-s24-pop-open", "has-s24-dock-open");
    if (dock) {{
      dock.innerHTML = "";
      dock.setAttribute("aria-hidden", "true");
    }}
  }}

  function popHtmlFromPillar(pillar) {{
    const tpl = pillar.querySelector("template.s24-pop-src");
    if (tpl) {{
      if (tpl.innerHTML && tpl.innerHTML.trim()) return tpl.innerHTML;
      if (tpl.content && tpl.content.childNodes.length) {{
        const box = document.createElement("div");
        box.appendChild(tpl.content.cloneNode(true));
        return box.innerHTML;
      }}
    }}
    const legacy = pillar.querySelector(".s24-popover");
    return legacy ? legacy.innerHTML : "";
  }}

  function showDock(pillar) {{
    if (!dock) return;
    const html = popHtmlFromPillar(pillar);
    if (!html) return;
    dock.innerHTML = html;
    dock.setAttribute("aria-hidden", "false");
    root.classList.add("has-s24-dock-open", "has-s24-pop-open");
    requestAnimationFrame(() => {{
      try {{
        dock.scrollIntoView({{ block: "nearest", behavior: "smooth" }});
      }} catch (_e) {{
        dock.scrollIntoView(false);
      }}
    }});
  }}

  function openPillarHover(pillar) {{
    cancelClose();
    root.querySelectorAll(".s24-pillar.is-pop-open").forEach((p) => {{
      if (p !== pillar) p.classList.remove("is-pop-open");
    }});
    pillar.classList.add("is-pop-open");
    showDock(pillar);
  }}

  function isInHoverZone(node) {{
    if (!node || !node.closest) return false;
    return !!(node.closest(".s24-pillar") || node.closest(".s24-detail-dock"));
  }}

  function bindPointerOpen(pillar) {{
    const open = () => openPillarHover(pillar);
    pillar.addEventListener("mouseenter", open);
    pillar.addEventListener("focus", open);
    pillar.addEventListener("pointerenter", open);
    pillar.addEventListener("touchstart", open, {{ passive: true }});
  }}

  root.querySelectorAll(".s24-pillar").forEach(bindPointerOpen);

  if (pillarsWrap) {{
    pillarsWrap.addEventListener("mouseleave", () => scheduleClose(140));
    pillarsWrap.addEventListener("pointerleave", (ev) => {{
      if (isInHoverZone(ev.relatedTarget)) return;
      scheduleClose(160);
    }});
  }}
  if (dock) {{
    dock.addEventListener("mouseenter", cancelClose);
    dock.addEventListener("pointerenter", cancelClose);
    dock.addEventListener("mouseleave", () => scheduleClose(140));
    dock.addEventListener("pointerleave", (ev) => {{
      if (isInHoverZone(ev.relatedTarget)) return;
      scheduleClose(160);
    }});
  }}
  root.addEventListener("pointerdown", (ev) => {{
    if (isInHoverZone(ev.target)) return;
    closeAll();
  }});

  function reportHeight() {{
    try {{
      const h = Math.ceil(
        root.getBoundingClientRect().height ||
        root.offsetHeight ||
        document.documentElement.scrollHeight ||
        document.body.scrollHeight ||
        0
      );
      if (h > 0) {{
        window.parent.postMessage({{ type: "saju-solar24-resize", height: h }}, "*");
      }}
    }} catch (e) {{}}
  }}
  reportHeight();
  [80, 280, 720].forEach((t) => setTimeout(reportHeight, t));
  try {{
    if (typeof ResizeObserver !== "undefined") {{
      new ResizeObserver(reportHeight).observe(root);
    }}
  }} catch (e) {{}}
  try {{
    window.addEventListener("load", reportHeight);
    window.addEventListener("resize", reportHeight);
  }} catch (e) {{}}
}})();
</script>
</body>
</html>
""".strip()


def solar_term_grid_html(
    current: CurrentSolarTerm24 | None = None,
) -> str:
    """하위 호환 — 단일 액자 HTML."""
    return solar_term_frame_html(current)
