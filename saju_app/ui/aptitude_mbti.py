"""사주 적성 + MBTI 결합(참고). MBTI는 심리유형 도구이며 직업 적성의 전부가 아님."""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import TYPE_CHECKING, Any

import streamlit as st

from saju_app.ui import components as M
from saju_app.ui import consulting_corpus as CC
from saju_app.utils import html_br

if TYPE_CHECKING:
    from saju_app.ui.interpretation_types import StructuredInterpretation

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_STEP3_MBTI_BANNER = _PROJECT_ROOT / "images" / "사주+MBTI.png"

MBTI_CHOICES: tuple[str, ...] = (
    "선택 안 함",
    "INTJ",
    "INTP",
    "ENTJ",
    "ENTP",
    "INFJ",
    "INFP",
    "ENFJ",
    "ENFP",
    "ISTJ",
    "ISFJ",
    "ESTJ",
    "ESFJ",
    "ISTP",
    "ISFP",
    "ESTP",
    "ESFP",
)

MBTI_16_TYPES: frozenset[str] = frozenset(x for x in MBTI_CHOICES if x != "선택 안 함")


# MBTI + 사주 참고용 고정 카피(일간 오행·용신은 `analyze_saju_mbti_aptitude`에서 덧붙임).
_SAJU_MBTI_MAPPINGS: dict[str, dict[str, str]] = {
    "ENTJ": {
        "type": "전략가형 리더",
        "strength": "비견+편관 강함 → 결단력과 리더십이 뛰어남",
        "career": "• CEO, 전략 컨설턴트, 창업, 투자, 기술 경영",
        "advice": "큰 그림을 그리고 추진하는 역할이 가장 잘 맞습니다.",
    },
    "INTJ": {
        "type": "비전 설계자",
        "strength": "편인+편관 조합 → 장기 전략 수립 능력",
        "career": "• 연구개발, AI·데이터 전략, 기업 기획, 변호사",
        "advice": "독립적인 환경에서 깊이 있는 일을 할 때 빛납니다.",
    },
    "ENFP": {
        "type": "아이디어 뮤지션",
        "strength": "식신+상관 에너지",
        "career": "• 콘텐츠 크리에이터, 마케팅, 교육, 스타트업",
        "advice": "자유로운 환경에서 창의력을 발휘하세요.",
    },
    "INTP": {
        "type": "이론·프레임 빌더",
        "strength": "편인+식상 기운 → 모델링·가설 검증에 강함",
        "career": "• 연구, 백엔드·아키텍처, 데이터, 기술 컨설팅",
        "advice": "명확한 질문과 실험 사이클이 있을 때 몰입이 커집니다.",
    },
    "ENTP": {
        "type": "혁신 협상가",
        "strength": "상관+편재 흐름 → 기회 포착과 설득에 강함",
        "career": "• 사업개발, 전략기획, 마케팅, VC·스타트업",
        "advice": "다양한 프로젝트를 오가며 학습하는 구조가 잘 맞습니다.",
    },
    "INFJ": {
        "type": "의미 중심 조율자",
        "strength": "정인+정관 조화 → 신뢰·비전 정렬에 강함",
        "career": "• 상담, 브랜드 기획, UX 리서치, 교육·코칭",
        "advice": "가치가 맞는 팀·미션에서 장기 몰입이 나옵니다.",
    },
    "INFP": {
        "type": "가치·표현형 창작가",
        "strength": "편인+식신 → 내면 서사와 산출물의 퀄리티",
        "career": "• 디자인, 글·영상, 기획, 복지·돌봄",
        "advice": "자율과 공감이 함께하는 환경을 우선하세요.",
    },
    "ENFJ": {
        "type": "성장 코디네이터",
        "strength": "정관+식상 → 사람·프로세스를 함께 끌어감",
        "career": "• HR, 교육운영, 커뮤니티, CS 리드",
        "advice": "피드백 루프가 빠른 조직에서 강점이 커집니다.",
    },
    "ISTJ": {
        "type": "시스템 실행가",
        "strength": "정관+정재 → 규범·마감·정확도",
        "career": "• 회계, 감사, 운영, QA, 규제 대응",
        "advice": "체크리스트와 역할 분담이 분명할수록 안정적입니다.",
    },
    "ISFJ": {
        "type": "세심한 서포터",
        "strength": "정인+정관 → 현장 배려와 책임감",
        "career": "• 행정, 의료·돌봄 지원, CS, 교육보조",
        "advice": "반복 업무도 ‘누군가의 안전’과 연결되면 에너지가 붙습니다.",
    },
    "ESTJ": {
        "type": "운영 총괄",
        "strength": "관성+재성 → KPI·현장 통제",
        "career": "• 관리직, 영업운영, 공공·군수, 물류",
        "advice": "목표가 숫자로 명확할 때 추진력이 극대화됩니다.",
    },
    "ESFJ": {
        "type": "팀 케어 리더",
        "strength": "비겁+관성 → 협업과 서비스 품질",
        "career": "• 행사, 교육지원, CS 매니저, 운영지원",
        "advice": "팀 분위기와 고객 경험을 동시에 챙기는 역할이 맞습니다.",
    },
    "ISTP": {
        "type": "장비·문제 해결사",
        "strength": "편관+식신 → 손으로 검증하는 실행",
        "career": "• 엔지니어링, 정비, 보안, QA",
        "advice": "짧은 사이클로 결과물을 만드는 프로젝트가 잘 맞습니다.",
    },
    "ISFP": {
        "type": "감각 실무 크리에이터",
        "strength": "식신+편관 → 감각·현장 밸런스",
        "career": "• 디자인 제작, 촬영, 돌봄, 공예·제조",
        "advice": "조용한 몰입과 가벼운 협업이 섞인 환경이 좋습니다.",
    },
    "ESTP": {
        "type": "현장 액션 플레이어",
        "strength": "편재+상관 → 순발·협상·리스크 감각",
        "career": "• 영업, 현장 PM, 사업, 이벤트",
        "advice": "즉각적인 피드백이 있는 역할에서 강점이 드러납니다.",
    },
    "ESFP": {
        "type": "현장 분위기 메이커",
        "strength": "식상+재성 → 사람·콘텐츠·매출 연결",
        "career": "• 행사, 방송·공연, 서비스, 라이브커머스",
        "advice": "에너지 소모를 관리하면서 ‘현장’을 유지하면 좋습니다.",
    },
}


def _step3_mbti_banner_data_uri() -> str | None:
    """images/사주+MBTI.png → data URI (Streamlit 경로 이슈 회피)."""
    path = _STEP3_MBTI_BANNER
    if not path.is_file():
        return None
    try:
        mime, _ = mimetypes.guess_type(path.name)
        mime = mime or "image/png"
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{data}"
    except OSError:
        return None


def _render_step3_mbti_banner() -> None:
    """사주+MBTI 분석 제목 아래 배너."""
    uri = _step3_mbti_banner_data_uri()
    if uri:
        st.markdown(
            f'<figure class="saju-mood-mid step3-mbti-banner" aria-hidden="false">'
            f'<img src="{uri}" alt="사주 MBTI" loading="lazy" decoding="async" />'
            f"</figure>",
            unsafe_allow_html=True,
        )
        return
    if M.render_mood_image("step03_mbti", variant="mid", alt="사주 MBTI"):
        return
    st.caption("배너 이미지를 찾을 수 없습니다. images/사주+MBTI.png 를 확인해 주세요.")


def analyze_saju_mbti_aptitude(
    gapja: list[str],
    mbti: str,
    engine: dict[str, Any],
) -> dict[str, str]:
    """MBTI별 고정 카피 + 일간 오행·용신·엔진 커리어 코멘트 보강(참고)."""
    mbti_u = (mbti or "").strip().upper()
    day_stem = gapja[2][0] if len(gapja) > 2 and gapja[2] else "甲"
    day_el = str(engine.get("day_el", "木"))

    yong = str(engine.get("yongshin", "판단 필요")).strip()
    career_hint = str(engine.get("career_comment") or "").strip()

    default: dict[str, str] = {
        "type": "다재다능형",
        "strength": f"일간 천간 「{day_stem}」·오행 「{day_el}」과 MBTI 조합이 독특합니다.",
        "career": "• 기획, 컨설팅, 교육, 창의 직군",
        "advice": "용신을 살리는 방향으로 커리어를 선택하면 큰 성과를 낼 수 있습니다.",
    }

    out = dict(_SAJU_MBTI_MAPPINGS.get(mbti_u, default))
    if yong not in ("", "판단 필요"):
        out["advice"] = f"{out['advice']} 용신 「{yong}」이 살아나는 환경을 곁들이면 좋습니다."
    if career_hint:
        out["career"] = f"{out['career']}\n• 사주 커리어 힌트: {career_hint}"
    return out


def _commit_step3_mbti_input() -> None:
    draft = str(st.session_state.get("step3_mbti_text_input") or "").strip().upper()[:4]
    st.session_state.user_mbti = draft


@st.fragment
def _render_step3_mbti_interactive(
    *,
    u_gapja: list[str],
    ix3: StructuredInterpretation,
    engine: dict[str, Any],
) -> None:
    """MBTI 입력·분석하기·결과 — fragment rerun 으로 클릭 시 스크롤이 위로 튕기지 않게."""
    with st.container(key="step3_mbti_input_row"):
        st.markdown('<p class="step3-mbti-field-label">입력</p>', unsafe_allow_html=True)
        in_c, btn_c = st.columns([3, 1], gap="small")
        with in_c:
            M.text_input_no_autofill(
                "MBTI 입력",
                max_chars=4,
                key="step3_mbti_text_input",
                placeholder="ENTJ",
                label_visibility="collapsed",
                help="영문 4자 (예: INTJ). 모르면 비워 두셔도 됩니다.",
                on_change=_commit_step3_mbti_input,
            )
        with btn_c:
            st.button(
                "분석하기",
                type="primary",
                use_container_width=True,
                key="step3_mbti_analyze_btn",
                on_click=_commit_step3_mbti_input,
            )

    mbti = str(st.session_state.get("user_mbti") or "").strip().upper()[:4]

    if mbti and len(mbti) == 4 and mbti in MBTI_16_TYPES:
        ilju = u_gapja[2] if len(u_gapja) > 2 else "—"
        result = analyze_saju_mbti_aptitude(list(u_gapja), mbti, engine)
        advice_full = result["advice"]
        if getattr(ix3, "one_liner", None):
            advice_full = f"{advice_full}\n\n사주 한 줄: {ix3.one_liner}"

        r_type = result["type"]
        r_strength = result["strength"]
        r_career = result["career"]

        st.markdown(
            f"""
<div class="saju-mbti-blend-card">
    <div class="saju-mbti-blend-head">
        <div class="saju-mbti-blend-title">{M._hx(mbti)} × {M._hx(ilju)} <span class="saju-mbti-blend-label">사주 적성</span></div>
        <div class="saju-mbti-blend-type">{M._hx(r_type)}</div>
    </div>
    <div class="saju-mbti-blend-strength">
        <b>주요 강점</b><br>
        {html_br(r_strength)}
    </div>
    <div class="saju-mbti-blend-career">
        <b>추천 커리어 방향</b><br>
        {html_br(r_career)}
    </div>
    <div class="saju-mbti-blend-advice">
        {html_br(advice_full)}
    </div>
</div>
""",
            unsafe_allow_html=True,
        )
        CC.render_consulting_panel(
            f"{CC.mbti_consulting_query(mbti)} 시험 진로 합격",
            apply="mbti",
            title="📎 현장 상담 참고 (적성·진로·시험)",
            expanded=False,
            container_key="step3_mbti_consulting",
        )
    else:
        if mbti and len(mbti) == 4 and mbti not in MBTI_16_TYPES:
            st.warning("MBTI는 INTJ, ENFP처럼 **알려진 16유형 코드**만 입력해 주세요.")
        st.info("💡 MBTI를 입력하면 사주와 결합한 맞춤형 적성 분석을 해드립니다.")


def render_step3_aptitude_mbti_block(
    *,
    u_name: str,
    u_gapja: list[str],
    strength: str,
    yongshin: str,
    max_el: str,
    min_el: str,
    ix3: StructuredInterpretation,
    engine: dict[str, Any],
) -> None:
    """STEP3: 사주 × MBTI 적성(텍스트 입력 + 시안 카드)."""
    _ = (strength, yongshin, max_el, min_el)

    if st.session_state.get("user_mbti") == "선택 안 함":
        st.session_state.user_mbti = ""
    st.session_state.setdefault("user_mbti", "")
    # `value=`와 `key=`를 동시에 쓰면 위젯 세션 키와 충돌할 수 있어, 최초 1회만 키를 시드합니다.
    seed_mbti = str(st.session_state.get("user_mbti") or "")
    if "step3_mbti_text_input" not in st.session_state:
        st.session_state["step3_mbti_text_input"] = seed_mbti

    st.markdown(
        '<div class="saju-section-title-badge">사주+MBTI 분석</div>',
        unsafe_allow_html=True,
    )
    _render_step3_mbti_banner()
    st.caption("MBTI 4자 입력 (예: ENTJ, ISFP) 후 **엔터** 또는 **분석하기**를 누르면 분석합니다.")

    _render_step3_mbti_interactive(
        u_gapja=list(u_gapja),
        ix3=ix3,
        engine=engine,
    )
