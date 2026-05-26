"""STEP 2 — 정보 입력 (본인·상대방 탭, 간소화 UI)."""

from __future__ import annotations

import calendar
import re
from datetime import date

import streamlit as st

from saju_app.ui import components as M

_SELF_NAME_INPUT_KEY = "step2_self_name_input"
_OPP_NAME_INPUT_KEY = "step2_opp_name_input"
_SELF_BDATE_KEY = "step2_u_bdate"
_OPP_BDATE_KEY = "step2_p_bdate"
_SELF_BDATE_TEXT_KEY = "step2_u_bdate_text"
_OPP_BDATE_TEXT_KEY = "step2_p_bdate_text"
_BDATE_TEXT_RE = re.compile(
    r"^\s*(\d{4})\s*[/\-.]\s*(\d{1,2})\s*[/\-.]\s*(\d{1,2})\s*$"
)
_BDATE_COMPACT_RE = re.compile(r"^\s*(\d{4})(\d{2})(\d{2})\s*$")

_STEP2_PERSONAL_STATE_KEYS = (
    "u_name",
    _SELF_NAME_INPUT_KEY,
    "user_name_snapshot",
    "u_gender",
    "u_y",
    "u_m",
    "u_d",
    _SELF_BDATE_KEY,
    _SELF_BDATE_TEXT_KEY,
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
    _OPP_BDATE_KEY,
    _OPP_BDATE_TEXT_KEY,
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
        if str(key).startswith("_step2_opp_blank_"):
            st.session_state.pop(key, None)
    st.session_state.pop(_OPP_NAME_INPUT_KEY, None)
    st.session_state._step2_prefill_payload = {}
    st.session_state.reset_id = int(st.session_state.get("reset_id", 0)) + 1


def _safe_date(y: int, m: int, d: int) -> date:
    last = calendar.monthrange(int(y), int(m))[1]
    return date(int(y), int(m), min(int(d), last))


def _bdate_text_key(bdate_key: str) -> str:
    if bdate_key == _SELF_BDATE_KEY:
        return _SELF_BDATE_TEXT_KEY
    if bdate_key == _OPP_BDATE_KEY:
        return _OPP_BDATE_TEXT_KEY
    return f"{bdate_key}_text"


def _format_bdate_str(y: int, m: int, d: int) -> str:
    return f"{int(y):04d}/{int(m):02d}/{int(d):02d}"


def _parse_bdate_text(raw: object) -> date | None:
    s = str(raw or "").strip()
    if not s:
        return None
    for pattern in (_BDATE_TEXT_RE, _BDATE_COMPACT_RE):
        m = pattern.match(s)
        if not m:
            continue
        y, mo, da = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if not (1900 <= y <= 2100 and 1 <= mo <= 12 and 1 <= da <= 31):
            continue
        try:
            return _safe_date(y, mo, da)
        except (TypeError, ValueError):
            continue
    return None


def _read_clamped_ymd(*, y_key: str, m_key: str, d_key: str) -> tuple[int, int, int]:
    """위젯 키를 쓰지 않고 읽기만 — 저장·payload용."""
    try:
        y = int(st.session_state.get(y_key, 1995))
        m = int(st.session_state.get(m_key, 1))
        d = int(st.session_state.get(d_key, 1))
    except (TypeError, ValueError):
        y, m, d = 1995, 1, 1
    safe = _safe_date(y, m, d)
    return int(safe.year), int(safe.month), int(safe.day)


def _read_ymd_for_payload(
    *, bdate_key: str, y_key: str, m_key: str, d_key: str
) -> tuple[int, int, int]:
    """저장·분석용 — 생년월일 텍스트(YYYY/MM/DD) 우선, 없으면 y/m/d 세션."""
    text_key = _bdate_text_key(bdate_key)
    parsed = _parse_bdate_text(st.session_state.get(text_key))
    if parsed is not None:
        return int(parsed.year), int(parsed.month), int(parsed.day)
    picked = st.session_state.get(bdate_key)
    if isinstance(picked, date):
        safe = _safe_date(int(picked.year), int(picked.month), int(picked.day))
        return int(safe.year), int(safe.month), int(safe.day)
    return _read_clamped_ymd(y_key=y_key, m_key=m_key, d_key=d_key)


def _ensure_bdate_text_from_ymd(
    *, y_key: str, m_key: str, d_key: str, bdate_key: str
) -> None:
    """text_input 위젯 생성 전에만 호출."""
    text_key = _bdate_text_key(bdate_key)
    cur = st.session_state.get(text_key)
    parsed = _parse_bdate_text(cur)
    if parsed is not None:
        st.session_state[y_key] = int(parsed.year)
        st.session_state[m_key] = int(parsed.month)
        st.session_state[d_key] = int(parsed.day)
        st.session_state[text_key] = _format_bdate_str(
            parsed.year, parsed.month, parsed.day
        )
        return
    legacy = st.session_state.get(bdate_key)
    if isinstance(legacy, date):
        st.session_state[y_key] = int(legacy.year)
        st.session_state[m_key] = int(legacy.month)
        st.session_state[d_key] = int(legacy.day)
        st.session_state[text_key] = _format_bdate_str(
            legacy.year, legacy.month, legacy.day
        )
        return
    y, m, d = _read_clamped_ymd(y_key=y_key, m_key=m_key, d_key=d_key)
    st.session_state[text_key] = _format_bdate_str(y, m, d)


def _pull_ymd_from_bdate_text(
    *, bdate_key: str, y_key: str, m_key: str, d_key: str
) -> bool:
    """생년월일 텍스트 → y/m/d 동기화. 성공 시 True."""
    text_key = _bdate_text_key(bdate_key)
    parsed = _parse_bdate_text(st.session_state.get(text_key))
    if parsed is None:
        return False
    st.session_state[y_key] = int(parsed.year)
    st.session_state[m_key] = int(parsed.month)
    st.session_state[d_key] = int(parsed.day)
    st.session_state[text_key] = _format_bdate_str(
        parsed.year, parsed.month, parsed.day
    )
    st.session_state.pop(bdate_key, None)
    return True


def _bdate_text_change_callback(*, y_key: str, m_key: str, d_key: str, bdate_key: str):
    def _cb() -> None:
        _pull_ymd_from_bdate_text(
            bdate_key=bdate_key, y_key=y_key, m_key=m_key, d_key=d_key
        )

    return _cb


def _default_self_ymd() -> tuple[int, int, int]:
    ud = st.session_state.get("u_data")
    if ud and len(ud) >= 3:
        return int(ud[0]), int(ud[1]), int(ud[2])
    parsed = _parse_bdate_text(st.session_state.get(_SELF_BDATE_TEXT_KEY))
    if parsed is not None:
        return int(parsed.year), int(parsed.month), int(parsed.day)
    cur = st.session_state.get(_SELF_BDATE_KEY)
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
    return str(st.session_state.get("u_name") or "").strip()


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


def _blank_opp_name_input_once_per_reset() -> None:
    rid = int(st.session_state.get("reset_id", 0))
    mk = f"_step2_opp_blank_{rid}"
    if st.session_state.get(mk):
        return
    st.session_state[_OPP_NAME_INPUT_KEY] = ""
    st.session_state[mk] = True


def _seed_step2_tab_widgets_if_needed() -> None:
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
    st.session_state[_SELF_BDATE_TEXT_KEY] = _format_bdate_str(cy, cm, cd)
    st.session_state.pop(_SELF_BDATE_KEY, None)
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
    if pd and len(pd) >= 6:
        st.session_state[_OPP_NAME_INPUT_KEY] = ""
        st.session_state.p_y = int(pd[0])
        st.session_state.p_m = int(pd[1])
        st.session_state.p_d = int(pd[2])
        st.session_state[_OPP_BDATE_TEXT_KEY] = _format_bdate_str(
            int(pd[0]), int(pd[1]), int(pd[2])
        )
        st.session_state.pop(_OPP_BDATE_KEY, None)
        pt = str(pd[3] or "모름")
        st.session_state.p_time = pt if pt in M.STEP2_TIME_OPTIONS else "모름"
        st.session_state.p_lunar = "음력" if bool(pd[4]) else "양력"
        st.session_state.p_leap = "윤달" if bool(pd[5]) else "평달"
        st.session_state.p_gender = _default_opp_gender()
    else:
        pn = ""
        st.session_state.p_name = pn
        st.session_state[_OPP_NAME_INPUT_KEY] = pn
        oy, om, od = _default_opp_ymd()
        ol, olp = _default_opp_cal_leap()
        st.session_state.setdefault("p_y", oy)
        st.session_state.setdefault("p_m", om)
        st.session_state.setdefault("p_d", od)
        st.session_state.setdefault(
            _OPP_BDATE_TEXT_KEY, _format_bdate_str(oy, om, od)
        )
        st.session_state.pop(_OPP_BDATE_KEY, None)
        st.session_state.setdefault("p_lunar", ol)
        st.session_state.setdefault("p_leap", olp)
        st.session_state.setdefault("p_time", "모름")
        st.session_state.setdefault("p_gender", _default_opp_gender())


def _collect_step2_payload_from_session() -> dict[str, object]:
    u_y, u_m, u_d = _read_ymd_for_payload(
        bdate_key=_SELF_BDATE_KEY, y_key="u_y", m_key="u_m", d_key="u_d"
    )
    py, pm, pd_ = _read_ymd_for_payload(
        bdate_key=_OPP_BDATE_KEY, y_key="p_y", m_key="p_m", d_key="p_d"
    )

    lunar_s = str(st.session_state.get("u_lunar") or "양력")
    if lunar_s not in ("양력", "음력"):
        lunar_s = "양력"
    leap_s = "평달" if lunar_s == "양력" else str(st.session_state.get("u_leap") or "평달")
    if leap_s not in ("평달", "윤달"):
        leap_s = "평달"

    u_t_str = str(st.session_state.get("u_time") or "모름")
    if u_t_str not in M.STEP2_TIME_OPTIONS:
        u_t_str = "모름"

    self_name = str(
        st.session_state.get(_SELF_NAME_INPUT_KEY)
        or st.session_state.get("u_name")
        or ""
    ).strip()
    opp_name = str(st.session_state.get(_OPP_NAME_INPUT_KEY) or "").strip()
    pl = str(st.session_state.get("p_lunar") or "양력")
    if pl not in ("양력", "음력"):
        pl = "양력"
    plp = "평달" if pl == "양력" else str(st.session_state.get("p_leap") or "평달")
    if plp not in ("평달", "윤달"):
        plp = "평달"
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


def _try_begin_step2_save() -> None:
    self_nm = str(st.session_state.get(_SELF_NAME_INPUT_KEY) or "").strip()
    if not self_nm:
        st.error("본인 이름을 입력해 주세요.")
        return
    if not _pull_ymd_from_bdate_text(
        bdate_key=_SELF_BDATE_KEY, y_key="u_y", m_key="u_m", d_key="u_d"
    ):
        st.error(
            "본인 생년월일을 **YYYY/MM/DD** 형식으로 입력해 주세요. (예: 1995/01/01)"
        )
        return
    if not bool(st.session_state.get("agree", False)):
        st.error("개인정보 수집·이용 동의가 필요합니다.")
        return
    payload = _collect_step2_payload_from_session()
    payload["u_name"] = self_nm
    payload["revisit_pin"] = str(st.session_state.get("step2_revisit_pin") or "").strip()
    payload["revisit_pin_confirm"] = str(
        st.session_state.get("step2_revisit_pin_confirm") or ""
    ).strip()
    st.session_state._step2_payload = payload
    st.session_state._step2_apply_pending = True
    M.rerun_full_app()


def _on_lunar_change_self() -> None:
    if str(st.session_state.get("u_lunar") or "양력") == "양력":
        st.session_state.u_leap = "평달"
    _pull_ymd_from_bdate_text(
        bdate_key=_SELF_BDATE_KEY, y_key="u_y", m_key="u_m", d_key="u_d"
    )


def _on_lunar_change_opp() -> None:
    if str(st.session_state.get("p_lunar") or "양력") == "양력":
        st.session_state.p_leap = "평달"
    _pull_ymd_from_bdate_text(
        bdate_key=_OPP_BDATE_KEY, y_key="p_y", m_key="p_m", d_key="p_d"
    )


def _render_birth_date(
    *,
    y_key: str,
    m_key: str,
    d_key: str,
    bdate_key: str,
) -> None:
    """생년월일 — 달력 없이 직접 입력(YYYY/MM/DD)."""
    text_key = _bdate_text_key(bdate_key)
    _ensure_bdate_text_from_ymd(
        y_key=y_key, m_key=m_key, d_key=d_key, bdate_key=bdate_key
    )
    bdate_cb = _bdate_text_change_callback(
        y_key=y_key, m_key=m_key, d_key=d_key, bdate_key=bdate_key
    )
    with st.container(key=f"{bdate_key}_wrap"):
        M.text_input_no_autofill(
            "생년월일",
            placeholder="1995/01/01",
            key=text_key,
            on_change=bdate_cb,
            help="숫자만 입력 · 연/월/일은 슬래시(/)로 구분 (예: 1995/01/01)",
        )
        raw = str(st.session_state.get(text_key) or "").strip()
        if raw and _parse_bdate_text(raw) is None:
            st.caption("⚠️ 형식: **YYYY/MM/DD** (예: 1995/01/01)")


def _render_person_form(
    *,
    name_label: str,
    name_key: str,
    lunar_key: str,
    leap_key: str,
    y_key: str,
    m_key: str,
    d_key: str,
    bdate_key: str,
    time_key: str,
    gender_key: str,
    container_key: str,
    on_lunar_change,
    show_contact: bool = False,
    contact_key: str = "u_contact",
) -> None:
    time_options = list(M.STEP2_TIME_OPTIONS)
    if str(st.session_state.get(time_key) or "모름") not in time_options:
        st.session_state[time_key] = "모름"

    row_key = "self" if show_contact else "opp"
    with st.container(key=container_key):
        with st.container(key=f"step2_{row_key}_row1_name_gender"):
            name_c, gender_c = st.columns(2, gap="small")
            with name_c:
                name_kwargs: dict[str, object] = {
                    "label": name_label,
                    "placeholder": "이름",
                    "key": name_key,
                }
                if name_key == _OPP_NAME_INPUT_KEY:
                    name_kwargs["autocomplete"] = "one-time-code"
                M.text_input_no_autofill(**name_kwargs)
            with gender_c:
                st.selectbox("성별", ("남자", "여자"), key=gender_key)

        with st.container(key=f"step2_{row_key}_row2_bdate_cal"):
            bdate_c, cal_c = st.columns(2, gap="small")
            with bdate_c:
                _render_birth_date(
                    y_key=y_key,
                    m_key=m_key,
                    d_key=d_key,
                    bdate_key=bdate_key,
                )
            with cal_c:
                st.selectbox(
                    "달력",
                    ("양력", "음력"),
                    key=lunar_key,
                    on_change=on_lunar_change,
                )
                if str(st.session_state.get(lunar_key) or "양력") == "음력":
                    st.selectbox("윤달", ("평달", "윤달"), key=leap_key)
                else:
                    st.session_state[leap_key] = "평달"
                    st.caption("평달 (양력)")

        with st.container(key=f"step2_{row_key}_row3_time_contact"):
            time_c, contact_c = st.columns(2, gap="small")
            with time_c:
                with st.container(key=f"step2_{time_key}_wrap"):
                    st.selectbox(
                        "태어난 시간",
                        time_options,
                        key=time_key,
                    )
            with contact_c:
                if show_contact:
                    M.text_input_no_autofill(
                        "연락처 (선택)",
                        placeholder="010-0000-0000",
                        key=contact_key,
                    )
                else:
                    st.empty()


def render() -> None:
    if "_step2_prefill_payload" not in st.session_state:
        st.session_state._step2_prefill_payload = {}
    if "reset_id" not in st.session_state:
        st.session_state.reset_id = 0

    if st.session_state.pop("_step2_queue_save", False):
        _try_begin_step2_save()

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

    _blank_opp_name_input_once_per_reset()
    _seed_step2_tab_widgets_if_needed()

    st.markdown(
        """
    <h2 style='text-align:center; color:#D4AF37; margin-bottom:1rem;'>
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
                f"**STEP{rs}**으로 이어가려면 아래 정보를 입력한 뒤 "
                f"**저장하고 사주 분석 시작**을 눌러 주세요."
            )

    st.markdown(
        """
<div class="saju-privacy-disclosure">
  <b>개인정보 수집·이용 안내</b><br>
  입력 정보는 사주·상담 제공에만 사용합니다.
</div>
""",
        unsafe_allow_html=True,
    )

    tab_main, tab_opp = st.tabs(["본인정보", "상대방정보"])

    with tab_main:
        st.caption(
            "이름 · 생년월일(YYYY/MM/DD) · 달력 · 시간 · 성별 · 연락처(선택) 순으로 입력하세요."
        )
        _render_person_form(
            name_label="성함",
            name_key=_SELF_NAME_INPUT_KEY,
            lunar_key="u_lunar",
            leap_key="u_leap",
            y_key="u_y",
            m_key="u_m",
            d_key="u_d",
            bdate_key=_SELF_BDATE_KEY,
            time_key="u_time",
            gender_key="u_gender",
            container_key="step2_navertone_self",
            on_lunar_change=_on_lunar_change_self,
            show_contact=True,
        )

    with tab_opp:
        st.caption("궁합·상대 분석 시에만 입력하세요. (선택)")
        _render_person_form(
            name_label="상대방 이름",
            name_key=_OPP_NAME_INPUT_KEY,
            lunar_key="p_lunar",
            leap_key="p_leap",
            y_key="p_y",
            m_key="p_m",
            d_key="p_d",
            bdate_key=_OPP_BDATE_KEY,
            time_key="p_time",
            gender_key="p_gender",
            container_key="step2_navertone_opp",
            on_lunar_change=_on_lunar_change_opp,
        )

    with st.container(key="step2_save_actions"):
        st.checkbox(
            "개인정보 수집·이용에 동의합니다. (필수)",
            key="agree",
        )
        with st.expander("재방문 비밀번호 설정 (선택)", expanded=False):
            st.caption("다음 방문 시 본인 정보로 바로 이동합니다.")
            rp1, rp2 = st.columns(2, gap="small")
            with rp1:
                M.password_input_no_autofill(
                    "재방문 비밀번호",
                    key="step2_revisit_pin",
                    placeholder="새 비밀번호",
                )
            with rp2:
                M.password_input_no_autofill(
                    "비밀번호 확인",
                    key="step2_revisit_pin_confirm",
                    placeholder="한 번 더 입력",
                )
        if st.button(
            "✅ 저장하고 사주 분석 시작",
            type="primary",
            use_container_width=True,
            key="step2_save_and_analyze_btn",
        ):
            _try_begin_step2_save()

    M.inject_step2_tab_order_once()
    M.inject_widget_focus_return_once()
