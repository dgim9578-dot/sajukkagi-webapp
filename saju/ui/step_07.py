"""STEP 7 — 오늘의 주역점.

64괘 데이터는 ``saju.core.iching_64`` (킹원 순 · 유니코드 ䷀–䷿)를 사용합니다.
"""

from __future__ import annotations

import hashlib
import html
import re
import time

import streamlit as st

from saju.core.iching_64 import get_hexagram
from saju_app.ui import analysis_favorite_memo as AFM
from saju_app.ui import consulting_knowledge as K
from saju_app.ui import components as M

WAIT_TIME = 180

JUYEOK_MASTER_DATABASE: dict[str, dict[str, object]] = {
    "火天大有": {
        "label": "화천대유(火天大有)",
        "basic": "하늘 위에 태양이 떠올라 천하를 비추는 격으로, 모든 것을 크게 소유하는 최고의 길괘입니다.",
        "storytelling": {
            "연애_결혼": "지금 뽑히신 '화천대유' 괘는 하늘 위에 태양이 이글이글 타오르는 형국이랍니다. 상대방이 사주까기님을 바라볼 때 후광이 비치는 시기예요. 고민할 것 없이 마음을 당당하게 표현하시면 백전백승입니다. 다만, 태양이 너무 뜨거우면 상대가 지칠 수 있으니 가끔은 쉬어가는 배려도 필요하겠죠?",
            "재물_투자": "돈줄이 활짝 열리는 '화천대유'의 기운을 잡으셨네요! 뜻밖의 횡재수나 막혔던 자금이 뚫리는 시기입니다. 쩨쩨하게 굴지 말고 과감하게 투자하거나 큰 판을 짜셔도 좋습니다. 다만, 내 주머니가 커지면 시기하는 사람이 생기니 베푸는 것도 잊지 마세요.",
            "직장_이직": "직장에서 나의 가치가 하늘 높이 치솟는 때입니다. 진급이나 좋은 조건의 스카우트 제의가 올 수 있어요. 윗사람들이 나를 눈여겨보고 있으니 기죽지 말고 능력을 과시하세요. 이직을 원하신다면 지금이 가장 몸값을 높여 갈 수 있는 적기랍니다.",
        },
    },
    "水雷屯": {
        "label": "수뢰둔(水雷屯)",
        "basic": "두꺼운 얼음 땅속에서 새싹이 돋아나려 하나, 아직은 시련과 정체가 따르는 난괘입니다.",
        "storytelling": {
            "연애_결혼": "아하, '수뢰둔' 괘가 나왔군요. 지금 연애 전선에 두꺼운 얼음이 얼어붙은 격이랍니다. 마음은 굴뚝같은데 상황이 안 도와주거나 오해가 쌓이기 쉽죠. 지금 억지로 관계를 진전시키려다가는 새싹이 꺾입니다. 조금 더 시간을 두고 상대의 마음이 녹기를 기다리는 지혜가 필요해요.",
            "재물_투자": "재물 면에서는 지금 지출이 많고 자금이 꽁꽁 묶이는 시기입니다. '새로운 투자처가 대박 나겠지?' 하고 덤볐다가는 큰 코 다치기 십상이에요. 지금은 지갑을 닫고 내실을 기하며 소나기를 피해야 하는 '버티기' 전략이 정답입니다.",
            "직장_이직": "직장에서 가슴이 답답하고 당장이라도 때려치우고 싶으시죠? 하지만 수뢰둔 괘는 '섣부른 이동 금지'를 말합니다. 지금 이직하면 늑대 피하려다 호랑이 만나는 격이 될 수 있어요. 내 능력을 더 키우면서 봄이 오기를 기다리셔야 합니다.",
        },
    },
    "地水师": {
        "label": "지수사(地水師)",
        "basic": "땅속에 물이 고여 군사를 일으키는 격으로, 경쟁과 갈등이 따르나 리더십이 필요한 괘입니다.",
        "storytelling": {
            "연애_결혼": "사랑을 쟁취하기 위해 총칼 없는 전쟁을 치르는 '지수사' 괘가 나왔습니다. 라이벌이 있거나 밀당이 아주 치열한 상황이네요. 이 연애는 질질 끌면 지는 겁니다. 사주까기님이 대장군처럼 확실한 리더십을 가지고 관계의 기준을 딱 정해주셔야 잡을 수 있습니다.",
            "재물_투자": "재물에 있어서는 아주 치열한 경쟁 구도에 놓이셨네요. 동업자와의 갈등이나 소송 수가 따를 수 있으니 계약서를 칼같이 확인하셔야 합니다. 무작정 돈을 쫓기보다 명분을 먼저 세우면 재물은 알아서 군사처럼 따라오게 됩니다.",
            "직장_이직": "조직 내에서 큰 프로젝트를 맡거나 치열한 진급 경쟁을 벌여야 하는 시기입니다. 내 편을 많이 만들어두는 것이 핵심이에요. 이직을 생각하신다면 경쟁률이 아주 센 곳이겠지만, 본인의 뚝심을 보여주면 승산이 있습니다.",
        },
    },
}

_NATURAL_TO_BAGUA: dict[str, str] = {
    "天": "乾",
    "地": "坤",
    "水": "坎",
    "火": "离",
    "雷": "震",
    "风": "巽",
    "山": "艮",
    "泽": "兑",
}
_TRIGRAM_YAO_YANG: dict[str, tuple[bool, bool, bool]] = {
    "乾": (True, True, True),
    "坤": (False, False, False),
    "震": (True, False, False),
    "坎": (False, True, False),
    "艮": (False, False, True),
    "巽": (False, True, True),
    "离": (True, False, True),
    "兑": (True, True, False),
}
_TRIGRAM_SYMBOL: dict[str, str] = {
    "乾": "☰",
    "坤": "☷",
    "震": "☳",
    "坎": "☵",
    "艮": "☶",
    "巽": "☴",
    "离": "☲",
    "兑": "☱",
}
_NATURAL_READING: dict[str, str] = {
    "天": "천",
    "地": "지",
    "水": "수",
    "火": "화",
    "雷": "뢰",
    "风": "풍",
    "山": "산",
    "泽": "택",
}
_BAGUA_READING: dict[str, str] = {
    "乾": "건",
    "坤": "곤",
    "震": "진",
    "坎": "감",
    "艮": "간",
    "巽": "손",
    "离": "리",
    "兑": "태",
}


def _char_hangul_reading(ch: str) -> str:
    if not ch:
        return ""
    if ch in _NATURAL_READING:
        return _NATURAL_READING[ch]
    if ch in _BAGUA_READING:
        return _BAGUA_READING[ch]
    return ""


def _name_ko_stem(name_ko: str) -> str:
    """``간(蹇)`` → ``간``, ``소축`` → ``소축``."""
    s = str(name_ko or "").strip()
    if "(" in s:
        return s.split("(", 1)[0].strip()
    return s


def _names_hanja_hangul(names_hanja: str, name_ko: str) -> str:
    """``水山蹇`` → ``수산간``, ``乾为天`` → ``건위천``."""
    nh = str(names_hanja or "").strip()
    if not nh:
        return _name_ko_stem(name_ko)
    if "为" in nh:
        i = nh.index("为")
        upper = _char_hangul_reading(nh[0])
        lower = _char_hangul_reading(nh[i + 1 : i + 2] if i + 1 < len(nh) else "")
        if upper and lower:
            return f"{upper}위{lower}"
        return _name_ko_stem(name_ko)
    parts: list[str] = []
    i = 0
    while i < len(nh) and nh[i] in _NATURAL_READING:
        parts.append(_NATURAL_READING[nh[i]])
        i += 1
    stem = _name_ko_stem(name_ko)
    if parts:
        return "".join(parts) + stem
    return stem or nh


def _trigram_hangul_cap(u_key: str, l_key: str) -> str:
    """팔괘 키 → 오행 한글(``水山`` → 수·산)로 상·하 표기."""
    _el: dict[str, str] = {
        "乾": "천",
        "坤": "지",
        "坎": "수",
        "离": "화",
        "震": "뢰",
        "巽": "풍",
        "艮": "산",
        "兑": "택",
    }
    ur = _el.get(u_key, _BAGUA_READING.get(u_key, u_key))
    lr = _el.get(l_key, _BAGUA_READING.get(l_key, l_key))
    return f"{ur} 상 · {lr} 하"


def _char_to_bagua_key(ch: str) -> str:
    if ch in _TRIGRAM_YAO_YANG:
        return ch
    return _NATURAL_TO_BAGUA.get(ch, ch)


def _upper_lower_bagua(names_hanja: str) -> tuple[str, str]:
    if "为" in names_hanja:
        i = names_hanja.index("为")
        head = names_hanja[0]
        tail = (names_hanja[i + 1 :] or "").strip()
        nat = tail[0] if tail else ""
        upper = _char_to_bagua_key(head)
        lower = _char_to_bagua_key(nat) if nat else upper
        return upper, lower
    if len(names_hanja) >= 2:
        return _char_to_bagua_key(names_hanja[0]), _char_to_bagua_key(names_hanja[1])
    return "乾", "乾"


def _hexagram_six_yao_top_first(names_hanja: str) -> list[bool]:
    u_key, l_key = _upper_lower_bagua(names_hanja)
    u = _TRIGRAM_YAO_YANG.get(u_key, _TRIGRAM_YAO_YANG["乾"])
    lo = _TRIGRAM_YAO_YANG.get(l_key, _TRIGRAM_YAO_YANG["乾"])
    return [u[2], u[1], u[0], lo[2], lo[1], lo[0]]


def _hexagram_display_html(
    *,
    symbol: str,
    names_hanja: str,
    yao_top_first: list[bool],
    name_ko: str = "",
) -> str:
    u_key, l_key = _upper_lower_bagua(names_hanja)
    u_sym = html.escape(_TRIGRAM_SYMBOL.get(u_key, ""))
    l_sym = html.escape(_TRIGRAM_SYMBOL.get(l_key, ""))
    tri_hangul = html.escape(_trigram_hangul_cap(u_key, l_key))
    sym = html.escape(symbol)
    el = "\u0064iv"
    yao_parts: list[str] = []
    for i, yang in enumerate(yao_top_first):
        if i == 3:
            yao_parts.append(f'<{el} class="step7-trigram-gap" aria-hidden="true"></{el}>')
        cls = "step7-yao yang" if yang else "step7-yao yin"
        yao_parts.append(f'<{el} class="{cls}"><span></span></{el}>')
    yao_inner = "".join(yao_parts)
    return (
        f'<{el} class="step7-hex-visual" role="img" aria-label="괘 {sym}">'
        f'<{el} class="step7-hex-glyph">{sym}</{el}>'
        f'<{el} class="step7-hex-trigram-cap">{u_sym} 상 · {l_sym} 하</{el}>'
        f'<{el} class="step7-hex-trigram-hangul">{tri_hangul}</{el}>'
        f'<{el} class="step7-yao-stack">{yao_inner}</{el}>'
        f"</{el}>"
    )


def _gist_interpretation_and_caution(gist: str) -> tuple[str, str | None]:
    g = (gist or "").strip()
    if "\n\n" in g:
        a, b = g.split("\n\n", 1)
        return a.strip(), b.strip() or None
    return g, None


def _today_hex_index(*, salt: str) -> int:
    now = M.now_kst()
    day_key = f"{now.date().isoformat()}|{salt}"
    h = hashlib.sha256(day_key.encode("utf-8")).hexdigest()
    return int(h[:12], 16) % 64


def _question_hex_index(user_question: str) -> int:
    """현재 시각과 질문 글자 수를 조합해 매번 새로운 괘를 산출합니다."""
    now = M.now_kst()
    question_len = len(str(user_question or ""))
    upper_magic = (int(now.hour) + int(now.minute) + question_len) % 8
    lower_magic = (int(now.minute) + int(now.second) + int(now.microsecond / 10000)) % 8
    seed = f"{now.isoformat(timespec='microseconds')}|{question_len}|{upper_magic}|{lower_magic}"
    h = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return (upper_magic * 8 + lower_magic + int(h[:8], 16)) % 64


def _question_category(user_question: str) -> str:
    """질문 주제 — 재물·직장을 연애 키워드보다 먼저 판별합니다."""
    text = str(user_question or "")
    if any(
        k in text
        for k in (
            "돈",
            "재물",
            "투자",
            "사업",
            "금전",
            "매매",
            "부동산",
            "수익",
            "거래",
            "성사",
            "계약",
            "협상",
            "영업",
            "매출",
            "판매",
            "고객",
            "주식",
            "코인",
            "체결",
            "납품",
            "수주",
            "견적",
            "매입",
            "매도",
            "청약",
            "입찰",
        )
    ):
        return "재물_투자"
    if any(
        k in text
        for k in (
            "직장",
            "이직",
            "퇴사",
            "회사",
            "승진",
            "취업",
            "스카우트",
            "프로젝트",
            "면접",
            "합격",
        )
    ):
        return "직장_이직"
    if any(
        k in text
        for k in (
            "연애",
            "결혼",
            "사랑",
            "인연",
            "궁합",
            "재회",
            "이별",
            "썸",
            "애인",
            "배우자",
            "남친",
            "여친",
        )
    ):
        return "연애_결혼"
    return "일반"


def _step7_consulting_html(user_question: str, *, engine: dict, juyeok_cat: str) -> str:
    """질문·주역 주제에 맞는 사주 상담만 (연애·결혼 등 주제 불일치 문단 제외)."""
    q = str(user_question or "").strip()
    if not q or juyeok_cat == "일반":
        return ""

    gender = str(st.session_state.get("u_gender", "") or "")
    strength = str(engine.get("strength", "") or "")
    yongshin = str(engine.get("yongshin", "") or "")
    daewoon_index = 0
    try:
        gt = engine.get("get_timing_flow")
        timing = gt() if callable(gt) else {}
        if isinstance(timing, dict):
            daewoon_index = int(timing.get("daewoon_index", 0))
    except Exception:
        pass
    daewoon_ten = ["인성", "비견", "식상", "재성", "관성"][int(daewoon_index) % 5]

    tip = K.consulting_tip(
        q,
        strength=strength,
        yongshin=yongshin,
        daewoon_ten=daewoon_ten,
        gender=gender,
    )

    return tip


def _fallback_juyeok_storytelling(*, label: str, basic: str, category: str) -> str:
    """64괘 전체에 적용되는 사주까기식 상담문을 만듭니다."""
    if category == "재물_투자":
        return (
            f"이번에 잡힌 '{label}' 괘는 재물 흐름에서 {basic} "
            "돈이 움직일 때는 괘가 말하는 핵심을 먼저 봐야 합니다. "
            "길한 괘라면 판을 넓히되 욕심을 앞세우지 말고, 막힘이 보이는 괘라면 지갑을 닫고 손실을 막는 쪽이 먼저랍니다. "
            "지금은 돈을 벌 수 있느냐보다 내 돈이 새는 구멍이 어디인지 보는 눈이 더 중요합니다."
        )
    if category == "직장_이직":
        return (
            f"직장과 이직 문제로 '{label}' 괘가 나왔다는 건, 지금 일터의 흐름이 {basic} "
            "이 괘는 무작정 움직이라는 뜻이 아니라, 내 위치와 명분을 먼저 정리하라는 신호로 보셔야 합니다. "
            "밀고 나갈 괘라면 능력을 숨기지 말고 드러내야 하고, 기다릴 괘라면 감정적인 퇴사보다 다음 자리를 준비하는 게 맞습니다. "
            "사주까기식으로 말하면, 지금은 자존심보다 타이밍이 밥 먹여주는 구간입니다."
        )
    if category == "일반":
        return (
            f"지금 던지신 고민에 '{label}' 괘가 잡혔는데, {basic} "
            "괘가 말하는 건 억지로 밀어붙일지, 잠시 숨 고르며 때를 볼지의 선택입니다. "
            "오늘 당장 결론을 내리기보다 조건·상대·돈·일정 중 어디가 막혀 있는지부터 짚어보시면 흐름이 보입니다. "
            "길한 괘면 준비된 만큼만 진행하고, 험한 괘면 무리한 밀어붙임보다 조건을 다시 맞추는 편이 낫습니다."
        )
    if category == "연애_결혼":
        return (
            f"연애와 인연 문제에서 '{label}' 괘가 나온 것은 관계의 속마음이 {basic} "
            "상대가 나를 좋아하느냐 아니냐만 보지 말고, 이 관계가 지금 자라나는 중인지 막혀 있는 중인지를 보셔야 합니다. "
            "길한 괘라면 마음을 표현하되 너무 몰아붙이지 말고, 난괘라면 억지로 답을 받으려 하지 말고 시간을 두는 게 지혜랍니다. "
            "인연은 잡는 힘도 중요하지만, 때를 기다리는 품격이 더 큰 결과를 만듭니다."
        )
    return (
        f"지금 던지신 고민에 '{label}' 괘가 잡혔는데, {basic} "
        "괘가 말하는 건 억지로 밀어붙일지, 잠시 숨 고르며 때를 볼지의 선택입니다."
    )


def _render_step7_frame(*, title: str, body_html: str, tone: str = "#D4AF37") -> None:
    st.markdown(
        f"""
<div class="step7-interpret-frame" style="--step7-tone:{html.escape(str(tone), quote=True)};">
    <div class="step7-interpret-title">{html.escape(str(title))}</div>
    <div class="step7-interpret-body">{body_html}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def _md_to_step7_html(text: str) -> str:
    safe = html.escape(str(text or ""))
    safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)
    return safe.replace("\n", "<br>")


def _juyeok_storytelling(hx, user_question: str) -> str:
    hanja_key = str(getattr(hx, "names_hanja", "") or "")
    data = JUYEOK_MASTER_DATABASE.get(str(hanja_key or ""))
    user_question = str(user_question or "").strip()
    category = _question_category(user_question)
    if not isinstance(data, dict):
        hangul = _names_hanja_hangul(hanja_key, str(getattr(hx, "name_ko", "") or ""))
        raw_label = f"{hangul}({hanja_key})" if hanja_key else str(getattr(hx, "name_ko", "주역"))
        raw_basic = str(getattr(hx, "gist", "") or "지금의 흐름을 차분히 살피라는 뜻입니다.").split("\n", 1)[0]
        advice = _fallback_juyeok_storytelling(
            label=raw_label,
            basic=raw_basic,
            category=category,
        )
        label = html.escape(raw_label)
        basic = html.escape(raw_basic)
    else:
        archive = data.get("storytelling")
        if not isinstance(archive, dict):
            archive = {}
        raw_label = str(data.get("label") or hanja_key)
        raw_basic = str(data.get("basic") or "")
        advice = str(archive.get(category) or "").strip()
        if not advice:
            advice = _fallback_juyeok_storytelling(
                label=raw_label,
                basic=raw_basic,
                category=category,
            )
        label = html.escape(raw_label)
        basic = html.escape(raw_basic)
    engine: dict = {}
    gapja = st.session_state.get("u_gapja")
    if isinstance(gapja, (list, tuple)):
        try:
            engine, _core = M.ensure_engine_and_core(list(gapja))
        except Exception:
            engine = {}
    advice_html = html.escape(advice).replace("\n", "<br>")
    parts = [
        "🔮 **bl사주까기 주역 신점 결과** 🔮<br><br>",
        "상담자님께서 던지신 고민을 품고 괘를 뽑으니, 주역 64괘 중 ",
        f"<b>[{label}]</b> 괘가 도출되었습니다.<br>",
        f"이 괘는 기본적으로 {basic}<br><br>",
        advice_html,
    ]
    consulting = _step7_consulting_html(
        user_question,
        engine=engine,
        juyeok_cat=category,
    )
    if consulting:
        consulting_html = html.escape(consulting).replace("\n", "<br>")
        parts.append(f"<br><br><b>사주 기반 상담 포인트</b><br>{consulting_html}")
    return "".join(parts)


def _iching_remain_seconds() -> float:
    last = st.session_state.get("last_iching_time")
    if last is None:
        return 0.0
    return max(0.0, float(WAIT_TIME) - (time.time() - float(last)))


def _iching_cooldown_progress_ui() -> None:
    remain = _iching_remain_seconds()
    if remain <= 0:
        st.caption("쿨다운이 끝났습니다. **다시뽑기** 또는 **오늘의 괘 뽑기**를 이용할 수 있습니다.")
        return
    pct = min(1.0, max(0.0, remain / float(WAIT_TIME)))
    st.progress(pct)
    m, s = int(remain // 60), int(remain % 60)
    st.caption(f"⏳ 다시 뽑기까지 남은 시간: **{m}분 {s}초** (막대가 줄어들면 곧 다시 뽑을 수 있어요)")


def _commit_iching_draw(*, u_name: str) -> None:
    q_saved = str(st.session_state.get("step7_iching_question_input", "") or "").strip()
    idx = _question_hex_index(q_saved)
    hx = get_hexagram(idx)
    st.session_state.last_iching_time = time.time()
    st.session_state.iching_today_revealed = True
    st.session_state["iching_last_idx"] = int(idx)
    st.session_state["iching_question_last"] = q_saved


def render() -> None:
    if st.session_state.get("last_iching_time") is not None:
        st.session_state.setdefault("iching_today_revealed", True)

    revealed = bool(st.session_state.get("iching_today_revealed"))

    with M.premium_analysis_shell(7):
        if not revealed:
            AFM.render_analysis_favorite_memo_band(step=7)
            M.render_mood_image("step07_hero", variant="hero", alt="오늘의 주역")
        st.markdown("## ☯️ 오늘의 주역점")
        if revealed:
            st.caption("다시뽑기는 3분 후에 하세요.")

        st.markdown("##### 💭 질문")
        st.markdown(
            '<div class="saju-step7-question-guide">'
            '<span class="saju-guide-warn">'
            '"누가=언제=(누구)에게=무엇을=결과" 결과는 단문 형식으로 적어 주세요. '
            '"될까요/말까요"'
            "</span> "
            "형식은 안 됩니다. 간절한 마음으로 질문하고 괘를 뽑으세요."
            "</div>",
            unsafe_allow_html=True,
        )
        M.text_area_no_autofill(
            "주역 질문",
            height=96,
            max_chars=500,
            placeholder="궁금한 내용을 입력 하세요",
            key="step7_iching_question_input",
            label_visibility="collapsed",
            help="선택 사항입니다. 적지 않아도 괘를 뽑을 수 있습니다.",
        )

        u_name = str(st.session_state.get("u_name") or "고객님")
        idx = int(st.session_state.get("iching_last_idx", _today_hex_index(salt=u_name)))
        hx = get_hexagram(idx)

        remain = _iching_remain_seconds()

        if remain > 0:
            st.markdown("##### 쿨다운")
            _iching_cooldown_progress_ui()
            st.caption("쿨다운 막대는 화면을 새로고침하거나 버튼을 누를 때 갱신됩니다.")

        with st.container(key="step7_action_row"):
            try:
                col_a, col_b = st.columns(2, gap="small")
            except TypeError:
                col_a, col_b = st.columns(2)
            with col_a:
                draw_first = st.button(
                    "오늘의 괘 뽑기",
                    type="primary",
                    use_container_width=True,
                    disabled=remain > 0 or revealed,
                    help="첫 점사입니다. 쿨다운 중에는 비활성입니다.",
                )
            with col_b:
                draw_again = st.button(
                    "다시뽑기",
                    type="secondary",
                    use_container_width=True,
                    disabled=remain > 0 or not revealed,
                    help=f"이미 본 괘를 다시 확정하면 쿨다운 {WAIT_TIME // 60}분이 적용됩니다.",
                )

        if draw_first:
            if remain > 0:
                st.warning("아직 쿨다운 중입니다.")
            elif revealed:
                st.info("이미 오늘의 괘를 확인하셨습니다. **다시뽑기**를 이용해 주세요.")
            else:
                _commit_iching_draw(u_name=u_name)
                M.rerun_full_app()

        if draw_again:
            if remain > 0:
                st.warning("아직 쿨다운 중입니다.")
            elif not revealed:
                st.info("먼저 **오늘의 괘 뽑기**를 눌러 주세요.")
            else:
                _commit_iching_draw(u_name=u_name)
                M.rerun_full_app()

        if revealed:
            u_key, l_key = _upper_lower_bagua(hx.names_hanja)
            u_sym = html.escape(_TRIGRAM_SYMBOL.get(u_key, ""))
            l_sym = html.escape(_TRIGRAM_SYMBOL.get(l_key, ""))
            title_plain = html.escape(f"제{hx.index + 1}괘 {hx.name_ko}")
            gist_line = html.escape(str(hx.gist or "").split("\n", 1)[0])
            st.markdown(
                f"**{html.escape(u_name)}님의 오늘의 괘:** {u_sym} {title_plain} {l_sym}  \n"
                f"{gist_line}",
            )
            interp, caution = _gist_interpretation_and_caution(hx.gist)
            hanja_line = html.escape(hx.names_hanja)
            hangul_line = html.escape(_names_hanja_hangul(hx.names_hanja, hx.name_ko))
            yao = _hexagram_six_yao_top_first(hx.names_hanja)
            visual = _hexagram_display_html(
                symbol=hx.symbol,
                names_hanja=hx.names_hanja,
                yao_top_first=yao,
                name_ko=hx.name_ko,
            )

            with st.container(key="step7_hex_reveal"):
                st.markdown(
                    '<div class="step7-hex-wrap step7-hex-wrap--reveal">'
                    f'<\u0064iv class="step7-hex-title">{u_sym} {title_plain} {l_sym}</\u0064iv>'
                    f'<\u0064iv class="step7-hex-hanja-line">({hanja_line})</\u0064iv>'
                    f'<\u0064iv class="step7-hex-hangul-line">{hangul_line}</\u0064iv>'
                    f"{visual}"
                    f"</\u0064iv>",
                    unsafe_allow_html=True,
                )
                _, c_mid, _ = st.columns([0.12, 0.76, 0.12])
                with c_mid:
                    story = _juyeok_storytelling(
                        hx,
                        str(st.session_state.get("iching_question_last", "") or ""),
                    )
                    explanation_parts: list[str] = []
                    if story:
                        explanation_parts.append(str(story))
                    explanation_parts.append(_md_to_step7_html(interp))
                    if caution:
                        explanation_parts.append(
                            f'<p class="step7-caution-lead"><b>주의</b></p>{_md_to_step7_html(caution)}'
                        )
                    with st.expander("괘 해설 · 주의 (펼쳐보기)", expanded=True):
                        _render_step7_frame(
                            title="해설",
                            body_html='<div class="step7-interpret-divider"></div>'.join(
                                explanation_parts
                            ),
                            tone="#D4AF37",
                        )

            st.caption("「뽑기」/「다시뽑기」를 누르면 위 괘가 확정되며 쿨다운이 시작됩니다.")
            if st.session_state.get("last_iching_time"):
                st.info(
                    "요지는 참고용입니다. 괘의·효사 등 전문 해석은 사주까기님과 상담 후 드러납니다."
                )
