"""STEP 2 — 정보 입력 (본인·상대방 탭, 저장 시 엔진 연동)."""

from __future__ import annotations

import calendar
from datetime import date

import streamlit as st

from saju_app.ui import components as M


_SELF_NAME_INPUT_KEY = "step2_self_name_input"
_OPP_NAME_INPUT_KEY = "step2_opp_name_input"

_STEP2_PERSONAL_STATE_KEYS = (
    "u_name",
    _SELF_NAME_INPUT_KEY,
    "user_name_snapshot",
    "u_gender",
    "u_y",
    "u_m",
    "u_d",
    "u_time",
    "u_lunar",
    "u_leap",
    "u_contact",
    "contact_value",
    "u_data",
    "u_gapja",
    "p_name",
    _OPP_NAME_INPUT_KEY,
    "partner_name_snapshot",
    "p_gender",
    "p_y",
    "p_m",
    "p_d",
    "p_time",
    "p_lunar",
    "p_leap",
    "p_data",
    "p_gapja",
    "agree",
    "_step2_payload",
    "_step2_apply_pending",
    "saju_briefing",
    "saju_briefing_fp",
)


def _clear_step2_personal_state() -> None:
    """새 사용자 입력 시작 시 이전 개인정보/분석 세션을 모두 비웁니다."""
    for key in _STEP2_PERSONAL_STATE_KEYS:
        st.session_state.pop(key, None)
    for key in list(st.session_state.keys()):
        if str(key).startswith("_step2_tabs_seeded_"):
            st.session_state.pop(key, None)
    st.session_state._step2_prefill_payload = {}
    st.session_state.reset_id = int(st.session_state.get("reset_id", 0)) + 1


def _safe_date(y: int, m: int, d: int) -> date:
    last = calendar.monthrange(int(y), int(m))[1]
    return date(int(y), int(m), min(int(d), last))


def _default_self_ymd() -> tuple[int, int, int]:
    ud = st.session_state.get("u_data")
    if ud and len(ud) >= 3:
        return int(ud[0]), int(ud[1]), int(ud[2])
    cur = st.session_state.get("step2_u_bdate")
    if isinstance(cur, date):
        return int(cur.year), int(cur.month), int(cur.day)
    pre = st.session_state.get("_step2_prefill_payload")
    if isinstance(pre, dict):
        try:
            return int(pre.get("u_y", 1995)), int(pre.get("u_m", 1)), int(pre.get("u_d", 1))
        except Exception:
            pass
    return (
        int(st.session_state.get("birth_year", 1995)),
        int(st.session_state.get("birth_month", 1)),
        int(st.session_state.get("birth_day", 1)),
    )


def _default_self_name() -> str:
    v = str(st.session_state.get("u_name") or "").strip()
    if v:
        return v
    return ""


def _default_self_gender() -> str:
    g = st.session_state.get("u_gender")
    return g if g in ("남자", "여자") else "남자"


def _default_self_cal_leap() -> tuple[str, str]:
    ud = st.session_state.get("u_data")
    if ud and len(ud) >= 6:
        lunar = bool(ud[4])
        leap = bool(ud[5])
        return ("음력" if lunar else "양력", "윤달" if leap else "평달")
    pre = st.session_state.get("_step2_prefill_payload")
    if isinstance(pre, dict):
        cal = str(pre.get("u_lunar") or "양력")
        leap = str(pre.get("u_leap") or "평달")
        return (cal if cal in ("양력", "음력") else "양력", leap if leap in ("평달", "윤달") else "평달")
    return "양력", "평달"


def _default_self_time() -> str:
    """저장된 ``u_data``·프리필보다 **현재 위젯 세션**을 우선합니다.

    시드 함수가 ``reset_id`` 변경 등으로 다시 돌 때 ``u_data``의 시각은 아직 ``모름``인데
    사용자가 선택한 ``st.session_state.u_time``만 유효한 경우가 있어, 그 값을 잃지 않습니다.
    """
    cur = str(st.session_state.get("u_time") or "").strip()
    if cur in M.STEP2_TIME_OPTIONS:
        return cur
    ud = st.session_state.get("u_data")
    if ud and len(ud) >= 4 and ud[3]:
        t = str(ud[3])
        if t in M.STEP2_TIME_OPTIONS:
            return t
    return "모름"


def _default_contact() -> str:
    c = str(st.session_state.get("contact_value") or "").strip()
    if c and c != "미등록":
        return c
    return "010-0000-0000"


def _default_opp_ymd() -> tuple[int, int, int]:
    pd = st.session_state.get("p_data")
    if pd and len(pd) >= 3:
        return int(pd[0]), int(pd[1]), int(pd[2])
    return _default_self_ymd()


def _default_opp_cal_leap() -> tuple[str, str]:
    pd = st.session_state.get("p_data")
    if pd and len(pd) >= 6:
        lunar = bool(pd[4])
        leap = bool(pd[5])
        return ("음력" if lunar else "양력", "윤달" if leap else "평달")
    return "양력", "평달"


def _default_opp_time() -> str:
    cur = str(st.session_state.get("p_time") or "").strip()
    if cur in M.STEP2_TIME_OPTIONS:
        return cur
    pd = st.session_state.get("p_data")
    if pd and len(pd) >= 4 and pd[3]:
        t = str(pd[3])
        if t in M.STEP2_TIME_OPTIONS:
            return t
    return "모름"


def _default_opp_gender() -> str:
    g = st.session_state.get("p_gender")
    return g if g in ("남자", "여자") else "여자"


def _seed_step2_tab_widgets_if_needed() -> None:
    """``reset_id``가 바뀔 때마다 한 번, 저장된 ``u_data`` / ``p_data``로 위젯 세션을 맞춥니다."""
    rid = int(st.session_state.get("reset_id", 0))
    mk = f"_step2_tabs_seeded_{rid}"
    if st.session_state.get(mk):
        return
    st.session_state[mk] = True

    cy, cm, cd = _default_self_ymd()
    cal, leap = _default_self_cal_leap()
    st.session_state.u_y = cy
    st.session_state.u_m = cm
    st.session_state.u_d = cd
    st.session_state.u_lunar = cal
    st.session_state.u_leap = leap
    st.session_state.u_time = _default_self_time()
    self_name = _default_self_name()
    st.session_state.u_name = self_name
    st.session_state[_SELF_NAME_INPUT_KEY] = self_name
    st.session_state.u_gender = _default_self_gender()
    st.session_state.u_contact = _default_contact()
    st.session_state.agree = True

    pd = st.session_state.get("p_data")
    pn = str(
        st.session_state.get("p_name")
        or st.session_state.get("partner_name_snapshot")
        or ""
    ).strip()
    if pd and len(pd) >= 6:
        st.session_state.p_name = pn
        st.session_state[_OPP_NAME_INPUT_KEY] = pn
        st.session_state.p_y = int(pd[0])
        st.session_state.p_m = int(pd[1])
        st.session_state.p_d = int(pd[2])
        pt = str(pd[3] or "모름")
        st.session_state.p_time = pt if pt in M.STEP2_TIME_OPTIONS else "모름"
        st.session_state.p_lunar = "음력" if bool(pd[4]) else "양력"
        st.session_state.p_leap = "윤달" if bool(pd[5]) else "평달"
        st.session_state.p_gender = _default_opp_gender()
    else:
        st.session_state.p_name = pn
        st.session_state[_OPP_NAME_INPUT_KEY] = pn
        oy, om, od = _default_opp_ymd()
        ol, olp = _default_opp_cal_leap()
        st.session_state.setdefault("p_y", oy)
        st.session_state.setdefault("p_m", om)
        st.session_state.setdefault("p_d", od)
        st.session_state.setdefault("p_lunar", ol)
        st.session_state.setdefault("p_leap", olp)
        st.session_state.setdefault("p_time", "모름")
        st.session_state.setdefault("p_gender", _default_opp_gender())


def _collect_step2_payload_from_session() -> dict[str, object]:
    lunar_s = str(st.session_state.get("u_lunar") or "양력")
    if lunar_s not in ("양력", "음력"):
        lunar_s = "양력"
    leap_s = "평달" if lunar_s == "양력" else str(st.session_state.get("u_leap") or "평달")
    if leap_s not in ("평달", "윤달"):
        leap_s = "평달"

    u_y = int(st.session_state.get("u_y", 1995))
    u_m = int(st.session_state.get("u_m", 1))
    u_d = int(st.session_state.get("u_d", 1))
    u_t_str = str(st.session_state.get("u_time") or "모름")
    if u_t_str not in M.STEP2_TIME_OPTIONS:
        u_t_str = "모름"

    self_name = str(
        st.session_state.get(_SELF_NAME_INPUT_KEY)
        or st.session_state.get("u_name")
        or ""
    ).strip()
    opp_name = str(
        st.session_state.get(_OPP_NAME_INPUT_KEY)
        or st.session_state.get("p_name")
        or ""
    ).strip()
    pl = str(st.session_state.get("p_lunar") or "양력")
    if pl not in ("양력", "음력"):
        pl = "양력"
    plp = "평달" if pl == "양력" else str(st.session_state.get("p_leap") or "평달")
    if plp not in ("평달", "윤달"):
        plp = "평달"
    py = int(st.session_state.get("p_y", 1995))
    pm = int(st.session_state.get("p_m", 1))
    pd_ = int(st.session_state.get("p_d", 1))
    p_t = str(st.session_state.get("p_time") or "모름")
    if p_t not in M.STEP2_TIME_OPTIONS:
        p_t = "모름"
    p_gen = str(st.session_state.get("p_gender") or "여자")
    if p_gen not in ("남자", "여자"):
        p_gen = "여자"

    u_gen = str(st.session_state.get("u_gender") or "남자")
    if u_gen not in ("남자", "여자"):
        u_gen = "남자"

    return {
        "u_name": self_name,
        "u_gender": u_gen,
        "u_y": u_y,
        "u_m": u_m,
        "u_d": u_d,
        "u_t_str": u_t_str,
        "u_lunar": lunar_s,
        "u_leap": leap_s,
        "opponent_name": opp_name,
        "p_gender": p_gen,
        "opponent_year": py,
        "opponent_month": pm,
        "opponent_day": pd_,
        "opponent_time": p_t,
        "opponent_lunar": pl,
        "opponent_leap": plp,
        "contact_num": str(st.session_state.get("u_contact") or "").strip(),
        "agree": bool(st.session_state.get("agree", False)),
        "revisit_pin": str(st.session_state.get("step2_revisit_pin") or "").strip(),
        "revisit_pin_confirm": str(
            st.session_state.get("step2_revisit_pin_confirm") or ""
        ).strip(),
    }


def _fold_two_choices(*, state_key: str, options: tuple[str, str], key_prefix: str) -> None:
    """접이식(expander): 제목은 현재 선택값만 표시, 펼치면 두 버튼으로 고릅니다."""
    a, b = options
    cur = str(st.session_state.get(state_key) or a)
    if cur not in options:
        cur = a
    with st.expander(cur, expanded=False):
        c1, c2 = st.columns(2, gap="small")
        with c1:
            t = "primary" if cur == a else "secondary"
            if st.button(a, type=t, use_container_width=True, key=f"{key_prefix}_a"):
                st.session_state[state_key] = a
                M.rerun_full_app()
        with c2:
            t = "primary" if cur == b else "secondary"
            if st.button(b, type=t, use_container_width=True, key=f"{key_prefix}_b"):
                st.session_state[state_key] = b
                M.rerun_full_app()


def _fold_many_choices(*, state_key: str, options: list[str], key_prefix: str) -> None:
    """모바일 인앱에서 selectbox 값 고정 문제를 피하기 위한 아코디언형 선택."""
    cur = str(st.session_state.get(state_key) or (options[0] if options else ""))
    if cur not in options and options:
        cur = options[0]

    def _pick_time(value: str) -> None:
        st.session_state[state_key] = value

    with st.expander(cur, expanded=False):
        for idx, opt in enumerate(options):
            label = opt
            st.button(
                label,
                type="primary" if cur == opt else "secondary",
                use_container_width=True,
                key=f"{key_prefix}_{idx}_{st.session_state.get('reset_id', 0)}",
                on_click=_pick_time,
                args=(opt,),
            )


def _fold_lunar_self(*, key_prefix: str) -> None:
    cur = str(st.session_state.get("u_lunar") or "양력")
    if cur not in ("양력", "음력"):
        cur = "양력"
    with st.expander(cur, expanded=False):
        c1, c2 = st.columns(2, gap="small")
        with c1:
            t = "primary" if cur == "양력" else "secondary"
            if st.button("양력", type=t, use_container_width=True, key=f"{key_prefix}_sol"):
                st.session_state.u_lunar = "양력"
                st.session_state.u_leap = "평달"
                M.rerun_full_app()
        with c2:
            t = "primary" if cur == "음력" else "secondary"
            if st.button("음력", type=t, use_container_width=True, key=f"{key_prefix}_lun"):
                st.session_state.u_lunar = "음력"
                M.rerun_full_app()


def _fold_leap_self(*, key_prefix: str) -> None:
    lunar = str(st.session_state.get("u_lunar") or "양력")
    if lunar == "양력":
        st.session_state.u_leap = "평달"
        st.caption("평달")
        return
    _fold_two_choices(state_key="u_leap", options=("평달", "윤달"), key_prefix=key_prefix)


def _fold_lunar_opp(*, key_prefix: str) -> None:
    cur = str(st.session_state.get("p_lunar") or "양력")
    if cur not in ("양력", "음력"):
        cur = "양력"
    with st.expander(cur, expanded=False):
        c1, c2 = st.columns(2, gap="small")
        with c1:
            t = "primary" if cur == "양력" else "secondary"
            if st.button("양력", type=t, use_container_width=True, key=f"{key_prefix}_sol"):
                st.session_state.p_lunar = "양력"
                st.session_state.p_leap = "평달"
                M.rerun_full_app()
        with c2:
            t = "primary" if cur == "음력" else "secondary"
            if st.button("음력", type=t, use_container_width=True, key=f"{key_prefix}_lun"):
                st.session_state.p_lunar = "음력"
                M.rerun_full_app()


def _fold_leap_opp(*, key_prefix: str) -> None:
    lunar = str(st.session_state.get("p_lunar") or "양력")
    if lunar == "양력":
        st.session_state.p_leap = "평달"
        st.caption("평달")
        return
    _fold_two_choices(state_key="p_leap", options=("평달", "윤달"), key_prefix=key_prefix)


def render() -> None:
    if "_step2_prefill_payload" not in st.session_state:
        # 개인정보 입력 화면은 새로고침/재접속 시 이전 사용자 이름을 자동 복원하지 않습니다.
        st.session_state._step2_prefill_payload = {}
    if "reset_id" not in st.session_state:
        st.session_state.reset_id = 0

    # 위젯 생성 전에 payload 적용(이전 run의 form 제출값)
    if st.session_state.pop("_step2_apply_pending", False):
        M.apply_step2_next_from_payload()

    apply_err = st.session_state.pop("_step2_apply_error", None)
    if apply_err:
        st.error(str(apply_err))

    if st.session_state.pop("_step2_force_blank", False) or not st.session_state.get(
        "_step2_privacy_clear_applied_v1"
    ):
        _clear_step2_personal_state()
        st.session_state._step2_privacy_clear_applied_v1 = True

    _seed_step2_tab_widgets_if_needed()

    st.markdown(
        """
    <h2 style='text-align:center; color:#D4AF37; margin-bottom:1.2rem;'>
        📋 정보 입력
    </h2>
    """,
        unsafe_allow_html=True,
    )

    ret_after = st.session_state.get("_return_step_after_input")
    if ret_after is not None and str(ret_after).strip().isdigit():
        rs = int(str(ret_after).strip())
        if M.STEP_NAV_MIN <= rs <= M.STEP_NAV_MAX:
            st.info(
                f"**STEP{rs}**으로 이어가려면 아래 본인·상대방 정보를 입력한 뒤, 맨 아래 **저장하고 사주 분석 시작**을 눌러 주세요."
            )

    st.markdown(
        """
<div class="saju-privacy-disclosure">
  <b>개인정보 수집·이용 안내</b><br>
  입력 정보 는 사주·상담 제공에만 사용합니다. 삭제 요청 시 지울 수 있으며, 건강·의료 해석은 참고용입니다.
</div>
""",
        unsafe_allow_html=True,
    )

    time_options = list(M.STEP2_TIME_OPTIONS)

    tab_main, tab_opp = st.tabs(["본인정보", "상대방정보"])

    with tab_main:
        with st.container(key="step2_navertone_self"):
            st.caption("본인 정보를 입력한 뒤, 접이식에서 선택하세요.")

            with st.container(key="s2self_r1"):
                s1a, s1b = st.columns(2, gap="small")
                with s1a:
                    M.text_input_no_autofill(
                        "성함",
                        placeholder="이름",
                        key=_SELF_NAME_INPUT_KEY,
                    )
                with s1b:
                    st.number_input(
                        "년도", min_value=1900, max_value=2100, step=1, key="u_y"
                    )

            with st.container(key="s2self_r2"):
                s2a, s2b = st.columns(2, gap="small")
                with s2a:
                    st.number_input("월", min_value=1, max_value=12, step=1, key="u_m")
                with s2b:
                    st.number_input("일", min_value=1, max_value=31, step=1, key="u_d")

            with st.container(key="s2self_r3"):
                s3a, s3b = st.columns(2, gap="small")
                with s3a:
                    st.caption("태어난 시간")
                    _fold_many_choices(
                        state_key="u_time",
                        options=time_options,
                        key_prefix="s2_self_time",
                    )
                with s3b:
                    st.caption("성별")
                    _fold_two_choices(
                        state_key="u_gender",
                        options=("남자", "여자"),
                        key_prefix="s2_self_g",
                    )

            with st.container(key="s2self_r4"):
                s4a, s4b = st.columns(2, gap="small")
                with s4a:
                    _fold_lunar_self(key_prefix="s2_self_lun")
                with s4b:
                    _fold_leap_self(key_prefix="s2_self_leap")

            with st.container(key="s2self_r5"):
                st.caption("연락처는 선택입니다.")
                M.text_input_no_autofill(
                    "연락처 (선택)",
                    placeholder="010-0000-0000",
                    key="u_contact",
                )

    with tab_opp:
        with st.container(key="step2_navertone_opp"):
            st.caption("상대방 정보를 입력한 뒤, 접이식에서 선택하세요.")

            with st.container(key="s2opp_r1"):
                o1a, o1b = st.columns(2, gap="small")
                with o1a:
                    M.text_input_no_autofill(
                        "상대방 이름",
                        placeholder="이름",
                        key=_OPP_NAME_INPUT_KEY,
                    )
                with o1b:
                    st.number_input("년도", min_value=1900, max_value=2100, step=1, key="p_y")

            with st.container(key="s2opp_r2"):
                o2a, o2b = st.columns(2, gap="small")
                with o2a:
                    st.number_input("월", min_value=1, max_value=12, step=1, key="p_m")
                with o2b:
                    st.number_input("일", min_value=1, max_value=31, step=1, key="p_d")

            with st.container(key="s2opp_r3"):
                o3a, o3b = st.columns(2, gap="small")
                with o3a:
                    st.caption("태어난 시간")
                    _fold_many_choices(
                        state_key="p_time",
                        options=time_options,
                        key_prefix="s2_opp_time",
                    )
                with o3b:
                    st.caption("성별")
                    _fold_two_choices(
                        state_key="p_gender",
                        options=("남자", "여자"),
                        key_prefix="s2_opp_g",
                    )

            with st.container(key="s2opp_r4"):
                o4a, o4b = st.columns(2, gap="small")
                with o4a:
                    _fold_lunar_opp(key_prefix="s2_opp_lun")
                with o4b:
                    _fold_leap_opp(key_prefix="s2_opp_leap")

    with st.form("step2_save_form", clear_on_submit=False):
        st.checkbox(
            "개인정보 수집·이용에 동의합니다. (필수)",
            key="agree",
        )
        with st.expander("재방문 비밀번호 설정 (선택)", expanded=True):
            st.caption(
                "비밀번호를 입력 하시면 다음 방문시 본인 정보로 이동 합니다"
            )
            rp1, rp2 = st.columns(2, gap="small")
            with rp1:
                st.text_input(
                    "재방문 비밀번호",
                    type="password",
                    key="step2_revisit_pin",
                    placeholder="새 비밀번호",
                )
            with rp2:
                st.text_input(
                    "비밀번호 확인",
                    type="password",
                    key="step2_revisit_pin_confirm",
                    placeholder="한 번 더 입력",
                )
        save_submitted = st.form_submit_button(
            "✅ 저장하고 사주 분석 시작",
            type="primary",
            use_container_width=True,
        )

    if save_submitted:
        self_nm = str(st.session_state.get(_SELF_NAME_INPUT_KEY) or "").strip()
        if not self_nm:
            st.error("본인 이름을 입력해 주세요.")
        elif not bool(st.session_state.get("agree", False)):
            st.error("개인정보 수집·이용 동의가 필요합니다.")
        else:
            payload = _collect_step2_payload_from_session()
            payload["u_name"] = self_nm
            payload["revisit_pin"] = str(
                st.session_state.get("step2_revisit_pin") or ""
            ).strip()
            payload["revisit_pin_confirm"] = str(
                st.session_state.get("step2_revisit_pin_confirm") or ""
            ).strip()
            st.session_state._step2_payload = payload
            st.session_state._step2_apply_pending = True
            M.rerun_full_app()
