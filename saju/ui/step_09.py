"""STEP 9 — 대운 (대운 구간별 해설)."""

from __future__ import annotations

import html

import streamlit as st

from saju.core.engine import STEM_ELEMENT

from saju_app.ui import action_timing as AT
from saju_app.ui import analysis_favorite_memo as AFM
from saju_app.ui import components as M
from saju_app.ui import oheng_visuals as OV


def _daewoon_table_rows(
    *,
    dae: dict,
    user_stem: str,
    birth_year: int,
    current_age: int,
) -> None:
    for row in dae.get("rows") or []:
        dae_ganji = str(row.get("pillar", ""))
        if len(dae_ganji) < 2:
            continue
        dae_stem = dae_ganji[0]
        age_start = int(row.get("age_start", 0))
        age_end = int(row.get("age_end", age_start + 9))
        start_year = int(row.get("year_start", birth_year + age_start))
        end_year = int(row.get("year_end", start_year + 9))

        ten = M.get_detailed_ten_stem(user_stem, dae_stem)
        result = M.DAEWON_TEN_INTERP.get(ten, "기본 운 흐름")

        expanded = age_start <= current_age <= age_end

        with st.expander(
            f"📅 {start_year} ~ {end_year}년  ({age_start}~{age_end}세)  **{dae_ganji}**",
            expanded=expanded,
        ):
            col1, col2 = st.columns([1, 3])
            with col1:
                st.caption("십성")
                _ic = OV.ten_stem_icon(ten)
                st.markdown(
                    f'<p class="saju-ten-mini">{_ic} <b>{html.escape(str(ten))}</b></p>',
                    unsafe_allow_html=True,
                )
            with col2:
                st.success(result)

            st.markdown(
                f"**대운 기운**: {dae_ganji} ({STEM_ELEMENT.get(dae_stem, '木')})"
            )


def render() -> None:
    u_gapja = M._require_u_gapja_or_halt()

    u_name = st.session_state.get("u_name", "고객님")
    u_data = st.session_state.get("u_data", (2000, 1, 1))
    u_gender = st.session_state.get("u_gender", "남자")
    opt = st.session_state.get("saju_options", {})
    zi_boundary = str(opt.get("zi_boundary", "23:30"))

    engine9, core9 = M.ensure_engine_and_core(u_gapja)
    yongshin = str(
        core9.get("yongshin") or engine9.get("yongshin", "판단 필요")
    )

    birth_year = int(u_data[0]) if u_data else 2000
    current_age = M.now_kst().year - birth_year

    n_terms = max(12, (2035 - birth_year) // 10 + 6)
    dae = M.compute_daewoon_schedule(
        u_gapja,
        u_data,
        str(u_gender),
        birth_year,
        zi_boundary=zi_boundary,
        n_terms=n_terms,
    )
    dir_ko = "순행" if dae.get("forward") else "역행"
    start_age = int(dae.get("start_age") or 0)
    days_j = int(dae.get("days_to_jie") or 0)

    with M.premium_analysis_shell(9):
        AFM.render_analysis_favorite_memo_band(step=9)
        st.header(f"📈 {u_name}님의 대운 흐름")
        st.caption(
            f"월주 기준 육십갑자 **{dir_ko}**. "
            f"첫 대운 입연은 출생 시각과 절입 간 **{days_j}일** 근사(3일=1년)로 **약 {start_age}세**부터로 계산했습니다. "
            "ephem(절입 정밀) 미설치 시 입연 나이는 0세부터 표시될 수 있습니다."
        )

        user_stem = u_gapja[2][0] if len(u_gapja) > 2 else "甲"

        with st.expander("전체 대운 목록 (펼쳐보기)", expanded=True):
            _daewoon_table_rows(
                dae=dae,
                user_stem=user_stem,
                birth_year=birth_year,
                current_age=current_age,
            )

        st.divider()
        with st.container(key="step9_action_timing"):
            AT.render_action_timing_block(
                u_gapja=list(u_gapja),
                u_data=u_data,
                birth_year=birth_year,
                zi_boundary=zi_boundary,
                yongshin=yongshin,
                dae=dae,
            )

        st.caption(
            "※이사·결혼·임신·건강·재물 등 행동 타이밍은 세운·일지 참고용이며 의료·법률·투자 조언을 대체하지 않습니다."
        )
