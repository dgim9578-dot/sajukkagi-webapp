"""이사·이직·결혼·임신·건강·재물 등 행동 타이밍(세운·일지 참고). 의료·법률 조언 아님."""

from __future__ import annotations

from typing import Any

import streamlit as st

from saju.core.engine import STEM_ELEMENT
from saju_app.core import calculations as C
from saju_app.ui import consulting_corpus as CC
from saju_app.ui import consulting_knowledge as K
from saju_app.ui import components as M


def _dae_row_for_year(rows: list[dict[str, Any]], year: int) -> dict[str, Any] | None:
    for r in rows:
        try:
            ys = int(r.get("year_start", 0))
            ye = int(r.get("year_end", ys + 9))
        except (TypeError, ValueError):
            continue
        if ys <= year <= ye:
            return r
    return None


def _year_saeun_ctx(
    *,
    year: int,
    u_gapja: list[str],
    hour: int | None,
) -> dict[str, Any]:
    day_p = str(u_gapja[2]) if len(u_gapja) > 2 else "甲子"
    day_stem = day_p[0] if day_p else "甲"
    day_branch = day_p[1] if len(day_p) > 1 else None
    pillar = C.get_bazi_year_pillar_lichun(int(year), 6, 15, hour)
    if not pillar or len(pillar) < 2:
        return {
            "year": year,
            "연주": "—",
            "세천간": "",
            "세지지": "",
            "세운십성": "비견",
            "일지": day_branch,
            "지지관계": "없음",
        }
    ys, yb = pillar[0], pillar[1]
    ten = M.get_detailed_ten_stem(day_stem, ys)
    rel = M.branch_pair_relation(day_branch, yb)
    return {
        "year": int(year),
        "연주": pillar,
        "세천간": ys,
        "세지지": yb,
        "세운십성": ten,
        "일지": day_branch,
        "지지관계": str(rel or "없음"),
    }


def _yong_aligns_stem(yongshin: str, stem: str) -> bool:
    ys = str(yongshin or "").strip()
    if ys not in ("木", "火", "土", "金", "水"):
        return False
    return STEM_ELEMENT.get(stem, "") == ys


def _year_label(ctx: dict[str, Any]) -> str:
    y = int(ctx.get("year") or 0)
    pill = str(ctx.get("연주") or "—")
    ten = str(ctx.get("세운십성") or "—")
    return f"**{y}년** 세운 `{pill}`(**{ten}**)"


def _verdict_move(*, ctx: dict[str, Any], yongshin: str) -> tuple[str, str]:
    rel = str(ctx.get("지지관계") or "")
    stem = str(ctx.get("세천간") or "")
    yl = _year_label(ctx)
    if "충" in rel:
        return (
            "🟡",
            f"{yl} — 일지·세운 **충(沖)**이 겹쳐 이사·대이동 에너지는 살아나지만, "
            "**계약·이사 일정·몸 컨디션**을 더 촘촘히 맞추는 편이 안전합니다.",
        )
    if "합" in rel:
        return (
            "🟢",
            f"{yl} — 일지·세운 **합(六合)**이 보이면 거처·환경을 새로 잡는 데 **동조**가 나오기 쉽습니다.",
        )
    if stem and _yong_aligns_stem(yongshin, stem):
        return (
            "🟢",
            f"{yl} — 세운 천간이 용신 **{yongshin}**과 맞닿아, 이전 후 **안정감**이 빨리 붙기 쉽습니다.",
        )
    return (
        "🟡",
        f"{yl} — 지지 합·충이 두드러지지 않으면 **생활 루틴·예산**만 잡혀 있을 때 무난한 해로 보는 편입니다.",
    )


def _verdict_job(*, ctx: dict[str, Any]) -> tuple[str, str]:
    ten = str(ctx.get("세운십성") or "")
    yl = _year_label(ctx)
    if any(x in ten for x in ("정관", "편관", "정재", "편재", "식신", "상관")):
        return (
            "🟢",
            f"{yl} — 세운 **{ten}**은 제안·이직·성과가 **겉으로 드러나기 쉬운** 흐름으로 읽는 경우가 많습니다.",
        )
    if "인" in ten:
        return (
            "🟡",
            f"{yl} — 세운 **{ten}**(인성)은 배움·자격·내부 정비에 유리하고, 겉 움직임은 **천천히** 보일 수 있습니다.",
        )
    return (
        "🟡",
        f"{yl} — 세운 **{ten}**은 이직보다 **실력·포트폴리오**를 쌓는 타이밍으로 읽는 경우가 많습니다.",
    )


def _is_female_gender(gender: str) -> bool:
    return any(token in str(gender or "") for token in ("여", "女", "F", "f"))


def _age_at_year(*, birth_year: int, year: int) -> int:
    return max(0, int(year) - int(birth_year))


def _action_timing_profile(*, age: int) -> str:
    """연령대별 관심사 묶음 — young(≤40) / mid(41~49) / mature(≥50)."""
    if age >= 50:
        return "mature"
    if age <= 40:
        return "young"
    return "mid"


def _action_section_copy(profile: str) -> tuple[str, str]:
    if profile == "young":
        return (
            "📌 이사·이직·결혼·임신 — 올해·내년 행동 타이밍(참고)",
            "‘올해 이사 가도 되나’, ‘언제 결혼·임신 준비를 검토할까’처럼 **실제 행동**과 맞닿는 질문을, "
            "**입춘 기준 세운(연주)**과 **일지** 관계로만 짧게 짚습니다. "
            "계약·이직·의료 결정은 전문가와 상의하고, 여기 출력은 **참고용**입니다.",
        )
    if profile == "mid":
        return (
            "📌 이사·이직·재물·건강 — 올해·내년 행동 타이밍(참고)",
            "40대 중후반에는 **생활·일·재정·컨디션** 균형이 핵심입니다. "
            "**입춘 기준 세운**과 **일지** 관계로 올해·내년의 **이사·이직·재물·건강** 흐름만 짧게 참고하세요.",
        )
    return (
        "📌 이사·이직·건강·재물 — 올해·내년 행동 타이밍(참고)",
        "50세 이후에는 **거처·일·건강·재정**이 중심 관심사인 경우가 많습니다. "
        "**입춘 기준 세운**과 **일지** 관계로 **이사·이직·건강·재물** 흐름만 짧게 참고하세요. "
        "의료·투자·법률 결정은 전문가 상담이 우선입니다.",
    )


def _action_tab_labels(*, profile: str, is_female: bool) -> list[str]:
    if profile == "young":
        fourth = "임신·준비" if is_female else "연애·인연"
        return ["이사", "이직", "결혼", fourth]
    if profile == "mid":
        return ["이사", "이직", "재물", "건강"]
    return ["이사", "이직", "건강", "재물"]


def _verdict_health(*, ctx: dict[str, Any]) -> tuple[str, str]:
    ten = str(ctx.get("세운십성") or "")
    rel = str(ctx.get("지지관계") or "")
    yl = _year_label(ctx)
    if "충" in rel:
        return (
            "🟡",
            f"{yl} — 일지·세운 **충**이면 피로·수면·일정 리듬이 흔들리기 쉬워 "
            "**무리한 활동·검진 미루기**는 피하는 편이 좋습니다.",
        )
    if any(x in ten for x in ("정관", "편관")):
        return (
            "🟡",
            f"{yl} — 세운 **{ten}**은 책임·스트레스·업무 부담이 몸에 쌓이기 쉬운 해로 읽히는 경우가 많습니다. "
            "**휴식·혈압·소화** 등 루틴 점검을 우선하세요.",
        )
    if any(x in ten for x in ("식신", "상관", "정인", "편인")):
        return (
            "🟢",
            f"{yl} — 세운 **{ten}**은 **회복·영양·생활 습관**을 정비하기 좋은 흐름으로 읽는 해석이 많습니다.",
        )
    if "합" in rel:
        return (
            "🟢",
            f"{yl} — 지지 **합**이면 컨디션·주변 돌봄·생활 환경을 **안정적으로 맞추기** 좋은 해로 보는 경우가 있습니다.",
        )
    return (
        "🟡",
        f"{yl} — 세운 **{ten}**은 **정기 검진·수면·가벼운 운동** 같은 기본 루틴을 지키는 해로 보는 편입니다.",
    )


def _verdict_wealth(*, ctx: dict[str, Any], yongshin: str) -> tuple[str, str]:
    ten = str(ctx.get("세운십성") or "")
    rel = str(ctx.get("지지관계") or "")
    stem = str(ctx.get("세천간") or "")
    yl = _year_label(ctx)
    if any(x in ten for x in ("정재", "편재")):
        return (
            "🟢",
            f"{yl} — 세운 **{ten}**은 **저축·연금·임대·고정 수입** 등 재정을 정리·확장하기 좋은 흐름으로 읽히는 경우가 많습니다.",
        )
    if any(x in ten for x in ("식신", "상관")):
        return (
            "🟢",
            f"{yl} — 세운 **{ten}**은 **기술·전문성·콘텐츠**를 수익으로 연결하기 좋은 해로 읽히는 경우가 있습니다.",
        )
    if ten in ("비견", "겁재"):
        return (
            "🟡",
            f"{yl} — 세운 **{ten}**은 **지출·보증·동업·충동 매매**를 줄이고 현금·안전자산 비중을 두는 편이 낫습니다.",
        )
    if stem and _yong_aligns_stem(yongshin, stem):
        return (
            "🟢",
            f"{yl} — 세운 천간이 용신 **{yongshin}**과 맞닿아 **재정 판단·계약**이 덜 흔들리기 쉽습니다.",
        )
    if "충" in rel:
        return (
            "🟡",
            f"{yl} — 일지·세운 **충**이면 **큰 거래·투자 일정**이 바뀌기 쉬워 서류·자금 계획을 먼저 고정하세요.",
        )
    return (
        "🟡",
        f"{yl} — 세운 **{ten}**은 **무리한 확장**보다 **현금 흐름·부채·연금**을 점검하는 해로 보는 편입니다.",
    )


def _verdict_marriage(*, ctx: dict[str, Any]) -> tuple[str, str]:
    ten = str(ctx.get("세운십성") or "")
    rel = str(ctx.get("지지관계") or "")
    yl = _year_label(ctx)
    if "충" in rel:
        return (
            "🟡",
            f"{yl} — 일지·세운 **충**이면 약속·일정이 어긋나기 쉬워 **대화·합의**를 먼저 두는 편이 좋습니다.",
        )
    if any(x in ten for x in ("정관", "편관", "정재", "편재")):
        return (
            "🟢",
            f"{yl} — 세운 **{ten}**은 책임·관계를 **공식화**하기 좋은 리듬으로 읽는 경우가 많습니다.",
        )
    if "합" in rel:
        return (
            "🟢",
            f"{yl} — 지지 **합**이 보이면 정서적 **끌림·동조**가 살아나기 쉽습니다.",
        )
    return (
        "🟡",
        f"{yl} — 인연 체감은 **월운·일진**까지 겹칠 때 커지므로, 세운은 **큰 방향**만 참고하세요.",
    )


def _verdict_pregnancy(*, ctx: dict[str, Any]) -> tuple[str, str]:
    ten = str(ctx.get("세운십성") or "")
    rel = str(ctx.get("지지관계") or "")
    yl = _year_label(ctx)
    if "충" in rel:
        return (
            "🟡",
            f"{yl} — 지지 **충**이면 몸·일정이 바쁘게 느껴질 수 있어 **무리한 일정 압축**은 피하는 편이 좋습니다.",
        )
    if any(x in ten for x in ("식신", "상관", "정인", "편인")):
        return (
            "🟢",
            f"{yl} — 세운 **{ten}**은 준비·보강 축으로 읽혀 **영양·휴식**을 챙기기 좋은 해로 보는 해석이 많습니다.",
        )
    return (
        "🟡",
        f"{yl} — 세운만으로 임신 가능성을 단정하지 않습니다. **산부인과 상담·검사**가 항상 우선입니다.",
    )


def _action_consulting_text(
    topic: str,
    *,
    ctx: dict[str, Any],
    strength: str,
    yongshin: str,
    gender: str,
    apply: str,
) -> str:
    base = K.consulting_tip_for_action_year(
        topic,
        year=int(ctx.get("year") or 0),
        year_pillar=str(ctx.get("연주") or ""),
        seyun_ten=str(ctx.get("세운십성") or ""),
        branch_rel=str(ctx.get("지지관계") or ""),
        daewoon_pillar=str(ctx.get("대운간지") or ""),
        daewoon_ten=str(ctx.get("대운십성") or ""),
        strength=strength,
        yongshin=yongshin,
        gender=gender,
        yong_aligns=_yong_aligns_stem(
            yongshin, str(ctx.get("세천간") or "")
        ),
    )
    q = (
        f"{topic} {ctx.get('year')} {ctx.get('연주')} {ctx.get('세운십성')} "
        f"{ctx.get('지지관계')} {ctx.get('대운십성')}"
    )
    hits = CC.match_consulting(q, apply=apply, limit=1)
    extra = CC.format_answers_plain(hits, max_chars=420) if hits else ""
    if not extra:
        return base
    return f"{base}\n\n📎 현장 상담: {extra}"


def _render_action_timing_frame(
    *,
    title: str,
    verdict: str,
    message: str,
    note: str,
    tone: str,
    caution: str = "",
    consulting: str = "",
    frame_key: str,
) -> None:
    """탭마다 DOM 트리가 달라지지 않도록 Streamlit 기본 위젯만 사용(removeChild 오류 방지)."""
    with st.container(border=True, key=frame_key):
        st.markdown(
            f'<p class="saju-step9-action-title" style="--step9-action-tone:{M._hx(tone)};">'
            f"{M._hx(title)}</p>",
            unsafe_allow_html=True,
        )
        st.markdown(f"**{verdict}** 총평(참고)")
        st.markdown(str(message or ""))
        st.caption(str(note or ""))
        if str(consulting or "").strip():
            st.markdown("**상담 포인트**")
            st.markdown(str(consulting))
        if str(caution or "").strip():
            st.warning(str(caution))


def render_action_timing_block(
    *,
    u_gapja: list[str],
    u_data: tuple | list,
    birth_year: int,
    zi_boundary: str,
    yongshin: str,
    dae: dict[str, Any],
) -> None:
    try:
        t_str = u_data[3] if isinstance(u_data, (list, tuple)) and len(u_data) > 3 else "모름"
        h = C.convert_time_str_to_hour(str(t_str), zi_boundary=str(zi_boundary))
    except Exception:
        h = None

    cy = M.now_kst().year
    year_opts = [cy, cy + 1, cy + 2, cy + 3]
    y_labels = {y: f"{y}년 (만 {max(0, y - int(birth_year))}세)" for y in year_opts}
    pick_y = st.radio(
        "기준 연도",
        options=year_opts,
        format_func=lambda y: y_labels[int(y)],
        horizontal=True,
        key="step9_action_year",
    )
    rows = list(dae.get("rows") or [])
    day_stem = u_gapja[2][0] if len(u_gapja) > 2 else "甲"
    ctx = _year_saeun_ctx(year=int(pick_y), u_gapja=list(u_gapja), hour=h)
    dr = _dae_row_for_year(rows, int(pick_y))
    if dr:
        dp = str(dr.get("pillar", "") or "").strip()
        if len(dp) >= 2:
            ctx["대운간지"] = dp
            ctx["대운십성"] = M.get_detailed_ten_stem(day_stem, dp[0])
    engine, _core = M.ensure_engine_and_core(list(u_gapja), birth_record=u_data)
    strength = str(engine.get("strength", "") or "")
    gender = str(st.session_state.get("u_gender", "") or "")
    apply = " ".join(str(x) for x in u_gapja if x)
    age_at_pick = _age_at_year(birth_year=int(birth_year), year=int(pick_y))
    profile = _action_timing_profile(age=age_at_pick)
    heading, intro = _action_section_copy(profile)
    st.subheader(heading)
    st.caption(intro)
    st.caption(f"**만 {age_at_pick}세** 기준으로 이 연령대에 맞는 관심사 탭을 표시합니다.")

    st.markdown(
        f"- **{pick_y}년 세운 연주**: `{ctx.get('연주')}` · 천간 십성 **{ctx.get('세운십성')}**  \n"
        f"- **일지 ↔ 세운 지지**: **{ctx.get('지지관계')}**"
    )
    if dr:
        pill = str(dr.get("pillar", "") or "").strip()
        dten = str(ctx.get("대운십성") or "—")
        a0 = int(dr.get("age_start", 0))
        a1 = int(dr.get("age_end", a0 + 9))
        ys = int(dr.get("year_start", 0))
        ye = int(dr.get("year_end", ys + 9))
        st.caption(
            f"같은 해의 **대운 구간**: {pill} · 천간 십성 **{dten}** ({ys}~{ye}년, 만 {a0}~{a1}세) — "
            "대운이 바뀌는 해이면 생활 테마도 함께 바뀌는 경우가 많습니다."
        )

    _render_action_timing_tabs(
        ctx=ctx,
        pick_y=int(pick_y),
        yongshin=str(yongshin),
        strength=strength,
        gender=gender,
        apply=apply,
        profile=profile,
    )


def _render_action_timing_tabs(
    *,
    ctx: dict[str, Any],
    pick_y: int,
    yongshin: str,
    strength: str,
    gender: str,
    apply: str,
    profile: str,
) -> None:
    is_female = _is_female_gender(gender)
    tab_labels = _action_tab_labels(profile=profile, is_female=is_female)
    tabs = st.tabs(tab_labels)

    def _move_tab(tab) -> None:
        v, msg = _verdict_move(ctx=ctx, yongshin=yongshin)
        _render_action_timing_frame(
            title="이사 타이밍",
            verdict=v,
            message=msg,
            note="실제 이사는 날씨·대출·병원·근무지·돌봄 거리 등 현실 조건과 함께 보세요.",
            consulting=_action_consulting_text(
                "이사",
                ctx=ctx,
                strength=strength,
                yongshin=yongshin,
                gender=gender,
                apply=apply,
            ),
            tone="#D4AF37",
            frame_key=f"step9_action_move_{pick_y}",
        )

    def _job_tab(tab) -> None:
        v, msg = _verdict_job(ctx=ctx)
        note = (
            "은퇴·자문·단기 계약 등 **역할 전환**도 세운·대운 흐름과 함께 보면 좋습니다."
            if profile == "mature"
            else "대운·세운 흐름과 함께 보면 분기·월 단위 감각을 더 얹기 좋습니다."
        )
        _render_action_timing_frame(
            title="이직 타이밍",
            verdict=v,
            message=msg,
            note=note,
            consulting=_action_consulting_text(
                "이직",
                ctx=ctx,
                strength=strength,
                yongshin=yongshin,
                gender=gender,
                apply=apply,
            ),
            tone="#60A5FA",
            frame_key=f"step9_action_job_{pick_y}",
        )

    def _marriage_tab(
        tab,
        *,
        title: str = "결혼 타이밍",
        topic: str = "결혼",
        frame_key: str | None = None,
    ) -> None:
        v, msg = _verdict_marriage(ctx=ctx)
        _render_action_timing_frame(
            title=title,
            verdict=v,
            message=msg,
            note="궁합·일지 상세는 STEP4, 인연 상담은 STEP11을 함께 참고하세요.",
            consulting=_action_consulting_text(
                topic,
                ctx=ctx,
                strength=strength,
                yongshin=yongshin,
                gender=gender,
                apply=apply,
            ),
            tone="#F472B6",
            frame_key=frame_key or f"step9_action_marriage_{pick_y}",
        )

    def _pregnancy_tab(tab) -> None:
        v, msg = _verdict_pregnancy(ctx=ctx)
        _render_action_timing_frame(
            title="임신·준비 타이밍",
            verdict=v,
            message=msg,
            note="몸 상태와 생활 리듬을 우선으로 보면서 무리한 일정 압축은 피하는 편이 좋습니다.",
            consulting=_action_consulting_text(
                "임신 준비",
                ctx=ctx,
                strength=strength,
                yongshin=yongshin,
                gender=gender,
                apply=apply,
            ),
            caution=(
                "**임신·출산**은 반드시 산부인과 진료로 결정하세요. 사주는 생활 리듬 참고용이며, "
                "불임·유산 등 민감한 주제를 단정하지 않습니다."
            ),
            tone="#A78BFA",
            frame_key=f"step9_action_pregnancy_{pick_y}",
        )

    def _health_tab(tab) -> None:
        v, msg = _verdict_health(ctx=ctx)
        _render_action_timing_frame(
            title="건강·컨디션 타이밍",
            verdict=v,
            message=msg,
            note="정기 검진·수면·식사·가벼운 운동을 우선하고, 증상·치료는 의료진과 상의하세요.",
            consulting=_action_consulting_text(
                "건강",
                ctx=ctx,
                strength=strength,
                yongshin=yongshin,
                gender=gender,
                apply=apply,
            ),
            caution=(
                "**건강·질병·수술**은 사주로 단정하지 않습니다. "
                "이 화면은 생활 리듬 참고용이며, 진단·치료는 의료진 상담이 우선입니다."
            ),
            tone="#34D399",
            frame_key=f"step9_action_health_{pick_y}",
        )

    def _wealth_tab(tab) -> None:
        v, msg = _verdict_wealth(ctx=ctx, yongshin=yongshin)
        _render_action_timing_frame(
            title="재물·재정 타이밍",
            verdict=v,
            message=msg,
            note="연금·저축·부동산·투자는 세운 참고와 함께 세금·현금 흐름·전문가 상담을 우선하세요.",
            consulting=_action_consulting_text(
                "재물",
                ctx=ctx,
                strength=strength,
                yongshin=yongshin,
                gender=gender,
                apply=apply,
            ),
            caution="**투자·대출·큰 거래**는 손실 가능성이 있으므로, 사주 해석만으로 결정하지 마세요.",
            tone="#FBBF24",
            frame_key=f"step9_action_wealth_{pick_y}",
        )

    renderers: list[tuple[str, object]] = []
    if profile == "young":
        fourth = _pregnancy_tab if is_female else (
            lambda tab: _marriage_tab(
                tab,
                title="연애·인연 타이밍",
                topic="연애",
                frame_key=f"step9_action_love_{pick_y}",
            )
        )
        renderers = [
            ("move", _move_tab),
            ("job", _job_tab),
            ("marriage", _marriage_tab),
            ("fourth", fourth),
        ]
    elif profile == "mid":
        renderers = [
            ("move", _move_tab),
            ("job", _job_tab),
            ("wealth", _wealth_tab),
            ("health", _health_tab),
        ]
    else:
        renderers = [
            ("move", _move_tab),
            ("job", _job_tab),
            ("health", _health_tab),
            ("wealth", _wealth_tab),
        ]

    for tab, (_, render_fn) in zip(tabs, renderers):
        with tab:
            render_fn(tab)
