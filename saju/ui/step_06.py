"""STEP 6 — 오늘의 운세."""

from __future__ import annotations

import html

import streamlit as st

from saju.core.engine import STEM_ELEMENT

from saju_app.ui import analysis_favorite_memo as AFM
from saju_app.ui import consulting_corpus as CC
from saju_app.ui import components as M
from saju_app.ui.interpretation_layout import (
    build_step6_today_interpretation,
)


def _step6_score_bar_html(score: int, tone: str) -> str:
    """오늘의 운세 점수 막대 — 퍼센트를 막대 위에 표시."""
    pct = max(0, min(100, int(score)))
    tone_esc = html.escape(tone)
    return (
        f'<div class="saju-step6-score-bar" style="--step6-tone:{tone_esc};--step6-pct:{pct};" '
        f'role="progressbar" aria-valuenow="{pct}" aria-valuemin="0" aria-valuemax="100" '
        f'aria-label="점수 {pct}퍼센트">'
        '<div class="saju-step6-score-track">'
        '<div class="saju-step6-score-fill"></div>'
        f'<span class="saju-step6-score-label">{pct}%</span>'
        "</div></div>"
    )


def render() -> None:
    M._resync_user_gapja_from_u_data()
    u_name = st.session_state.get("u_name", "사주까기님")
    u_gapja = st.session_state.get("u_gapja")

    if not u_gapja or len(u_gapja) < 3:
        st.warning("⚠️ 사주 정보가 없습니다. 먼저 사주 분석을 진행해주세요.")
        if st.button(
            "← 사주 분석 결과로",
            use_container_width=True,
            help="STEP3 사주 분석 결과 화면으로 이동합니다.",
        ):
            M.prepare_step_change_ui()
            st.session_state.step = 3
            M.rerun_full_app()
        st.stop()

    engine, core = M.ensure_engine_and_core(u_gapja)

    with M.premium_analysis_shell(6):
        AFM.render_analysis_favorite_memo_band(step=6)
        now = M.now_kst()
        today_gapja = M.get_saju_data(now.year, now.month, now.day, 12, False, False)

        u_stem, u_branch = u_gapja[2][0], u_gapja[2][1]
        t_stem, t_branch = today_gapja[2][0], today_gapja[2][1]

        st.markdown(
            f"## 🔮 {u_name}님의 {now.strftime('%m월 %d일')} 오늘의 운세 심층분석"
        )
        M.render_mood_image("step06_hero", variant="hero", alt="오늘의 운세")

        ten_detail = M.get_detailed_ten_stem(
            u_stem, t_stem
        )
        if ten_detail in ("비견", "겁재"):
            ten_group = "비겁"
        elif ten_detail in ("식신", "상관"):
            ten_group = "식상"
        elif ten_detail in ("정재", "편재"):
            ten_group = "재성"
        elif ten_detail in ("정관", "편관"):
            ten_group = "관성"
        else:
            ten_group = "인성"

        t_el = STEM_ELEMENT.get(t_stem, "木")
        yongshin = str(engine.get("yongshin", "판단 필요"))
        strength = str(engine.get("strength", "중화"))
        max_el = str(engine.get("max_el", "木"))
        min_el = str(engine.get("min_el", "水"))

        base = 68
        yong_bonus = 6 if yongshin and (yongshin == t_el or yongshin == max_el) else 0
        cold_penalty = -4 if (min_el == t_el and strength == "신약") else 0

        category_weights = {
            "직장": {"관성": 10, "식상": 6, "인성": 4, "재성": 2, "비겁": -3},
            "연애": {"재성": 8, "식상": 6, "관성": 4, "인성": 3, "비겁": -4},
            "재물": {"재성": 12, "식상": 6, "관성": 2, "인성": 2, "비겁": -6},
            "공부": {"인성": 12, "관성": 7, "식상": 3, "재성": -2, "비겁": -3},
            # 건강은 '인성(회복/보강)' + '관성(루틴/관리)'를 우선
            "건강": {"인성": 10, "관성": 8, "식상": 4, "재성": 1, "비겁": -2},
        }

        category_meta = {
            "직장": {"icon": "💼", "tone": "#60a5fa"},
            "연애": {"icon": "💖", "tone": "#fb7185"},
            "재물": {"icon": "💰", "tone": "#fbbf24"},
            "공부": {"icon": "📚", "tone": "#34d399"},
            "건강": {"icon": "🩺", "tone": "#a78bfa"},
        }

        desc_by_group = {
            "직장": {
                "관성": "규칙·책임·평가가 강해지는 흐름입니다. 오늘은 '정확도'와 '마감'이 성과를 좌우합니다.",
                "식상": "기획·발표·설득이 먹히는 날입니다. 한 번에 완성하려 하기보다, 60% 초안을 빠르게 공유하세요.",
                "재성": "성과가 숫자로 연결되기 쉽습니다. 단, 욕심을 내면 과투입·과로로 번질 수 있어 페이스 조절이 핵심입니다.",
                "인성": "지원군/정보가 들어옵니다. 혼자 해결하려 하지 말고, 레퍼런스·선배 조언을 적극 활용하세요.",
                "비겁": "동료·팀 이슈가 부각될 수 있습니다. 오늘은 이기기보다 '합의'를 먼저 잡는 쪽이 유리합니다.",
            },
            "연애": {
                "재성": "호감·끌림이 잘 살아납니다. 약속을 잡거나 관계를 한 단계 진전시키기 좋은 날입니다.",
                "식상": "표현이 관계를 움직입니다. 말/메시지는 짧고 명확하게, 칭찬은 구체적으로 하세요.",
                "관성": "진중함이 신뢰로 연결됩니다. 가벼운 밀당보다, 약속·예의를 지키는 태도가 득점입니다.",
                "인성": "편안한 대화가 힘이 됩니다. 감정 정리·공감이 잘 되는 날이라 관계 회복에도 유리합니다.",
                "비겁": "고집/자존심 싸움이 생기기 쉽습니다. '맞다/틀리다'보다 '기분'을 먼저 확인하세요.",
            },
            "재물": {
                "재성": "돈의 흐름이 보이는 날입니다. 수익 기회가 오지만, 조건·리스크 확인은 반드시 하세요.",
                "식상": "아이디어가 수익으로 이어질 수 있습니다. 부업/판매/콘텐츠는 '작게 테스트'가 정답입니다.",
                "관성": "고정지출·의무지출이 잡힐 수 있습니다. 계획된 지출이면 OK, 충동 결제는 보류하세요.",
                "인성": "문서·정보가 돈을 지킵니다. 계약/약관/세금/정산 체크에 시간을 쓰면 손실을 막습니다.",
                "비겁": "돈이 새기 쉽습니다(동업/빌려줌/과소비). 오늘은 지갑을 '잠그는 날'로 두세요.",
            },
            "공부": {
                "인성": "흡수력이 올라갑니다. 어려운 과목/개념을 정리하기 좋은 날입니다.",
                "관성": "루틴·계획이 잘 먹힙니다. 시간표대로 밀어붙이면 성과가 납니다.",
                "식상": "설명·요약이 빠릅니다. 발표/서술형/포트폴리오 정리에 유리합니다.",
                "재성": "공부 외 유혹이 늘 수 있습니다. 환경(폰/알림)부터 정리하면 효율이 유지됩니다.",
                "비겁": "경쟁심은 좋지만 비교로 지치기 쉽습니다. 오늘은 '나의 페이스'를 지키는 게 핵심입니다.",
            },
            "건강": {
                "인성": "회복·보강이 잘 되는 흐름입니다. 수면/수분/스트레칭만 지켜도 컨디션이 빠르게 올라옵니다.",
                "관성": "관리·루틴이 성과를 냅니다. 오늘은 '시간 정해 운동/식사'처럼 규칙을 만들면 좋습니다.",
                "식상": "활력이 올라가지만 무리하면 탈이 납니다. 강도보다 '지속'으로 잡아야 안전합니다.",
                "재성": "밖일/이동으로 체력이 새기 쉽습니다. 일정 사이 휴식(10분)으로 회복을 먼저 챙기세요.",
                "비겁": "승부욕/페이스 경쟁은 금물입니다. 남과 비교하지 말고 내 리듬으로 정리하세요.",
            },
        }

        def score_for(cat: str) -> int:
            w = int(category_weights.get(cat, {}).get(ten_group, 0))
            return max(35, min(99, base + w + yong_bonus + cold_penalty))

        def analysis_100_plus(cat: str) -> str:
            """상담자 사주 + 오늘 십성(ten_group) 기반 100자 이상 문장."""
            base_msg = desc_by_group.get(cat, {}).get(ten_group, "오늘 흐름에 맞춰 유연하게 조절하세요.")
            engine_comment = {
                "재물": str(engine.get("wealth_comment") or ""),
                "연애": str(engine.get("marriage_comment") or ""),
                "직장": str(engine.get("career_comment") or ""),
                "건강": "오늘 컨디션은 무리한 승부보다 회복 리듬과 생활 패턴을 먼저 맞출 때 안정됩니다.",
                "공부": "오늘 학습은 새 범위를 많이 넓히기보다 이미 본 내용을 정리하고 반복하는 쪽이 효율적입니다.",
            }.get(cat, "")
            category_focus = {
                "재물": (
                    f"{u_name}님은 {max_el} 기운이 강하게 잡혀 있어 돈을 움직일 때도 한 번 정한 방식과 패턴을 반복하는 힘이 있습니다. "
                    f"다만 약한 {min_el} 기운 때문에 숫자 검토, 계약 조건, 손익 계산처럼 차갑게 따져보는 과정은 의식적으로 보완하는 편이 좋습니다."
                ),
                "연애": (
                    f"{u_name}님의 오늘 연애 흐름은 감정 표현보다 안정감과 태도가 더 크게 작용합니다. "
                    f"{strength} 구조에서는 마음이 앞설 때도 상대의 반응을 확인하며 속도를 맞추는 것이 관계를 편하게 만듭니다."
                ),
                "직장": (
                    f"직장운에서는 {ten_detail} 기운이 오늘의 업무 태도에 영향을 줍니다. "
                    f"강한 {max_el}은 책임감과 버티는 힘으로 쓰고, 약한 {min_el}은 보고·정리·우선순위 체크로 보완하면 성과가 더 선명해집니다."
                ),
                "건강": (
                    f"건강운은 진단이 아니라 컨디션 관리 관점으로 보세요. {strength} 흐름에서는 몸의 신호를 늦게 알아차리거나 반대로 예민하게 느낄 수 있으니, "
                    "오늘은 수면, 수분, 식사 시간, 가벼운 움직임처럼 기본 루틴을 먼저 맞추는 것이 좋습니다."
                ),
                "공부": (
                    f"공부운은 집중력의 방향을 잡는 것이 중요합니다. {max_el} 기운이 강하면 한 번 몰입했을 때 오래 끌고 가는 힘이 있지만, "
                    f"약한 {min_el} 보완을 위해 오답 정리, 메모, 시간표처럼 구조화된 방식이 필요합니다."
                ),
            }.get(cat, "")
            yongshin_tip = {
                "재물": f"용신 {yongshin}은 지출을 줄이는 기준과 수익 기회를 고르는 기준으로 쓰면 좋습니다.",
                "연애": f"용신 {yongshin}은 대화 톤, 만나는 장소, 관계 속 거리감을 조절하는 기준이 됩니다.",
                "직장": f"용신 {yongshin}은 업무 환경, 협업 방식, 오늘 먼저 처리할 일을 고르는 기준으로 삼기 좋습니다.",
                "건강": f"용신 {yongshin}은 생활 습관과 회복 루틴을 정할 때 참고하면 컨디션 균형을 잡는 데 도움이 됩니다.",
                "공부": f"용신 {yongshin}은 공부 장소, 시간대, 반복 방식처럼 학습 환경을 고르는 기준으로 쓰기 좋습니다.",
            }.get(cat, f"용신 {yongshin} 기운을 살리는 선택이 유리합니다.")
            tips: list[str] = [base_msg]
            if engine_comment:
                tips.append(engine_comment)
            if category_focus:
                tips.append(category_focus)
            if yongshin and yongshin != "판단 필요":
                tips.append(yongshin_tip)
            tips.append("오늘은 큰 결론을 서두르기보다, 이 항목에서 바로 실행할 수 있는 작은 행동 하나를 정하는 것이 가장 현실적입니다.")
            msg = " ".join(t for t in tips if t).strip()
            if len(msg) > 520:
                msg = msg[:519] + "…"
            return msg

        def render_panel(cat: str) -> None:
            sc = int(score_for(cat))
            meta = category_meta[cat]
            msg = analysis_100_plus(cat)
            tone = str(meta["tone"])
            st.subheader(f"{meta['icon']} {cat}")
            st.markdown(_step6_score_bar_html(sc, tone), unsafe_allow_html=True)
            st.markdown(
                f"""
<div style="
    margin:0.8rem 0 0.75rem;
    padding:1rem 1.05rem 1.05rem;
    border-radius:16px;
    border:1px solid {tone};
    background:
        radial-gradient(circle at 12% 18%, {tone}24 0 3px, transparent 4px),
        linear-gradient(135deg, {tone}22 0%, rgba(255,255,255,0.06) 100%);
    box-shadow:0 10px 28px rgba(0,0,0,0.12), inset 0 0 0 1px rgba(255,255,255,0.08);
">
  <div style="font-weight:800;color:{tone};margin-bottom:0.5rem;">{html.escape(str(cat))} 해석 포인트</div>
  <div style="line-height:1.72;">{html.escape(msg)}</div>
  <div style="
      margin-top:0.8rem;
      padding:0.62rem 0.72rem;
      border-radius:12px;
      background:rgba(255,255,255,0.08);
      border:1px solid rgba(148,163,184,0.22);
      font-size:0.92rem;
      line-height:1.55;
  ">
    체크포인트: 십성 {html.escape(str(ten_detail))}({html.escape(str(ten_group))}) · 용신 {html.escape(str(yongshin))}
  </div>
</div>
""",
                unsafe_allow_html=True,
            )

        def _render_daily_focus_cards() -> None:
            cards = [
                (
                    "오늘의 중심 기운",
                    f"오늘은 {ten_detail}({ten_group}) 기운이 중심입니다.",
                    "#D4AF37",
                ),
                (
                    "용신 활용",
                    f"용신 {yongshin}을 살리는 선택(루틴·환경·대화 톤)을 하면 체감 운이 더 안정적으로 올라갑니다.",
                    "#60A5FA",
                ),
                (
                    "신강약 메모",
                    f"신강약은 {strength}이며, 오늘은 {t_el} 기운이 상대적으로 잘 드러나는 날입니다.",
                    "#34D399",
                ),
            ]
            for title, body, tone in cards:
                st.markdown(
                    f"""
<div class="step6-daily-focus-card" style="--step6-tone:{html.escape(tone)};">
  <div class="step6-daily-focus-title">{html.escape(title)}</div>
  <div class="step6-daily-focus-body">{html.escape(body)}</div>
</div>
""",
                    unsafe_allow_html=True,
                )

        st.divider()

        core_box = (
            f"오늘은 **{ten_detail}({ten_group})** 기운이 중심입니다. "
            f"용신 **{yongshin}**을 살리는 선택(루틴·환경·대화 톤)을 하면 체감 운이 더 안정적으로 올라옵니다."
        )
        if len(core_box) < 50:
            core_box += " 작은 선택을 반복해 흐름을 굳히세요."
        if len(core_box) > 120:
            core_box = core_box[:119] + "…"

        cats = ("재물", "연애", "직장", "건강", "공부")
        avg_today = int(sum(score_for(c) for c in cats) / len(cats))

        st.subheader("오늘의 핵심 운세")
        _ix6 = build_step6_today_interpretation(
            ten_detail=ten_detail,
            ten_group=ten_group,
            yongshin=yongshin,
            strength=strength,
            max_el=max_el,
            min_el=min_el,
            base_msg=core_box.replace("**", ""),
            harmony_pct=avg_today,
        )
        _render_daily_focus_cards()

        st.divider()

        if "step6_today_pick" not in st.session_state:
            st.session_state.step6_today_pick = "재물"

        def _pick(cat: str):
            def _h():
                st.session_state.step6_today_pick = cat

            return _h

        with st.container(key="step6_today_pick_row"):
            pick_cols = M._columns_compat(len(cats))
            for i, cat in enumerate(cats):
                with pick_cols[i]:
                    emo = category_meta[cat]["icon"]
                    st.button(
                        emo,
                        key=f"step6_pick_{cat}",
                        on_click=_pick(cat),
                        use_container_width=True,
                        help=f"{cat}운 상세 보기",
                    )
                    st.markdown(
                        f'<p class="step6-pick-cap">{html.escape(cat)}</p>',
                        unsafe_allow_html=True,
                    )

        st.divider()
        _pick6 = str(st.session_state.get("step6_today_pick") or "재물")
        render_panel(_pick6)
        _cat_q = {
            "재물": "재물 돈 투자",
            "연애": "연애 썸 결혼",
            "직장": "직장 이직 커리어",
            "건강": "건강 컨디션 마음",
            "공부": "공부 시험 자격증",
        }
