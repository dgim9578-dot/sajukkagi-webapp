"""STEP 2 — 정보 입력 (본인·상대방 탭, 간소화 UI)."""

from __future__ import annotations

import calendar
import re
from datetime import date

import streamlit as st
import streamlit.components.v1 as components

from saju_app.ui import components as M
from saju_app.ui import execution as saju_execution

STEP2_UI_BUILD = "2026-05-31-step2-deferred-save-v9"

_STEP2_TIME_OPTIONS_FALLBACK: tuple[str, ...] = (
    "모름",
    "자(23:30~01:29)",
    "축(01:30~03:29)",
    "인(03:30~05:29)",
    "묘(05:30~07:29)",
    "진(07:30~09:29)",
    "사(09:30~11:29)",
    "오(11:30~13:29)",
    "미(13:30~15:29)",
    "신(15:30~17:29)",
    "유(17:30~19:29)",
    "술(19:30~21:29)",
    "해(21:30~23:29)",
)


def coerce_step2_time_option(raw: object) -> str:
    """태어난 시간 select — 깨진·축약 라벨을 정식 옵션으로 복원."""
    fn = getattr(M, "coerce_step2_time_option", None)
    if callable(fn):
        return fn(raw)
    opts = tuple(getattr(M, "STEP2_TIME_OPTIONS", _STEP2_TIME_OPTIONS_FALLBACK))
    val = str(raw or "").strip()
    if val in opts:
        return val
    if not val:
        return "모름"
    for opt in opts:
        if opt.startswith(val) or val.startswith(opt.split("(")[0]):
            return opt
    if re.match(r"^\d{1,2}\s*월\.?$", val):
        return "모름"
    branch = re.match(r"^([자축인묘진사오미신유술해])", val)
    if branch:
        b = branch.group(1)
        for opt in opts[1:]:
            if opt.startswith(f"{b}("):
                return opt
    return "모름"


def protect_step2_birth_time_selects() -> None:
    """STEP2 태어난 시간 — 달력 월 패치가 시간 select를 망가뜨리지 않도록."""
    saju_execution.protect_step2_birth_time_selects()

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
    "u_time_idx",
    "u_time_select_idx",
    "u_time_widget",  # 레거시(문자열 select) — 마이그레이션 후 제거
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
    "p_time_idx",
    "p_time_select_idx",
    "p_time_widget",
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
    for key in (
        _time_last_selected_key("u_time"),
        _time_last_selected_key("p_time"),
        _time_rerun_checkpoint_key("u_time"),
        _time_rerun_checkpoint_key("p_time"),
    ):
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
        # text_key 를 매 rerun 정규화하면 커서·선택 영역이 초기화된다 — y/m/d 만 동기화
        return
    # 입력 중(미완성)·의도적 비움("") 포함 — text 를 ymd 기본값으로 덮어쓰지 않음
    if cur is not None:
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


def _sync_ymd_from_bdate_text(
    *,
    bdate_key: str,
    y_key: str,
    m_key: str,
    d_key: str,
) -> bool:
    """생년월일 텍스트 → y/m/d 만 동기화(저장·달력 변경·버튼 콜백용).

    ``text_input`` 위젯 키는 건드리지 않습니다 (렌더 후 수정 시 StreamlitAPIException).
    """
    text_key = _bdate_text_key(bdate_key)
    parsed = _parse_bdate_text(st.session_state.get(text_key))
    if parsed is None:
        return False
    st.session_state[y_key] = int(parsed.year)
    st.session_state[m_key] = int(parsed.month)
    st.session_state[d_key] = int(parsed.day)
    st.session_state.pop(bdate_key, None)
    return True


def _normalize_bdate_text_on_change(
    *,
    bdate_key: str,
    y_key: str,
    m_key: str,
    d_key: str,
) -> None:
    """``text_input`` ``on_change`` 전용 — 슬래시 형식 정규화."""
    if not _sync_ymd_from_bdate_text(
        bdate_key=bdate_key, y_key=y_key, m_key=m_key, d_key=d_key
    ):
        return
    text_key = _bdate_text_key(bdate_key)
    parsed = _parse_bdate_text(st.session_state.get(text_key))
    if parsed is None:
        return
    st.session_state[text_key] = _format_bdate_str(
        parsed.year, parsed.month, parsed.day
    )


def _bdate_text_change_callback(*, y_key: str, m_key: str, d_key: str, bdate_key: str):
    text_key = _bdate_text_key(bdate_key)

    def _cb() -> None:
        _normalize_bdate_text_on_change(
            bdate_key=bdate_key,
            y_key=y_key,
            m_key=m_key,
            d_key=d_key,
        )

    return _cb


def _time_index_key(time_key: str) -> str:
    return f"{time_key}_idx"


def _time_widget_index_key(time_key: str) -> str:
    """selectbox 위젯 전용 키(정수 인덱스) — DOM 라벨 변조와 분리."""
    return f"{time_key}_select_idx"


def _time_last_selected_key(time_key: str) -> str:
    return f"_{time_key}_last_selected"


def _time_rerun_checkpoint_key(time_key: str) -> str:
    return f"_{time_key}_rerun_checkpoint"


def _time_option_index(raw: object, *, time_options: list[str]) -> int:
    label = coerce_step2_time_option(raw)
    try:
        return time_options.index(label)
    except ValueError:
        return 0


def _read_canonical_birth_time(time_key: str) -> str:
    """저장·검증용 — 위젯 인덱스·canonical 문자열·checkpoint 순으로 복구."""
    opts = list(M.STEP2_TIME_OPTIONS)
    idx_key = _time_widget_index_key(time_key)

    if idx_key in st.session_state:
        try:
            from_idx = _time_label_from_index(
                st.session_state.get(idx_key, 0),
                time_options=opts,
                time_key=time_key,
            )
            if from_idx in opts:
                return from_idx
        except Exception:
            pass

    raw = st.session_state.get(time_key)
    if isinstance(raw, str) and raw in opts:
        return raw
    picked = coerce_step2_time_option(raw)
    if picked in opts and picked != "모름":
        return picked
    if picked in opts and picked == "모름":
        for recovery_key in (
            _time_rerun_checkpoint_key(time_key),
            _time_last_selected_key(time_key),
        ):
            last = coerce_step2_time_option(st.session_state.get(recovery_key))
            if last in opts and last != "모름":
                return last
        return "모름"
    checkpoint = coerce_step2_time_option(
        st.session_state.get(_time_rerun_checkpoint_key(time_key))
    )
    if checkpoint in opts:
        return checkpoint
    last = coerce_step2_time_option(st.session_state.get(_time_last_selected_key(time_key)))
    if last in opts:
        return last
    return "모름"


def _migrate_legacy_time_widget_key(*, time_key: str, time_options: list[str]) -> None:
    """모바일 레거시 u_time_widget(문자열) → u_time_select_idx(정수) 마이그레이션."""
    legacy = f"{time_key}_widget"
    if legacy not in st.session_state:
        return
    opts = list(time_options)
    coerced = coerce_step2_time_option(st.session_state.get(legacy))
    if coerced != "모름":
        st.session_state[time_key] = coerced
        st.session_state[_time_last_selected_key(time_key)] = coerced
    st.session_state.pop(legacy, None)


def _time_label_from_index(
    idx: int, *, time_options: list[str], time_key: str
) -> str:
    opts = list(time_options)
    try:
        i = int(idx)
    except (TypeError, ValueError):
        i = 0
    i = max(0, min(len(opts) - 1, i))
    return coerce_step2_time_option(opts[i])


def _prepare_birth_time_select_state(*, time_key: str, time_options: list[str]) -> None:
    """태어난 시간 — canonical 문자열(u_time) 동기화."""
    opts = list(time_options)
    _sanitize_time_session_before_widget(time_key=time_key, time_options=opts)
    picked = _read_canonical_birth_time(time_key)
    st.session_state[time_key] = picked
    if picked != "모름":
        st.session_state[_time_last_selected_key(time_key)] = picked
        st.session_state[_time_rerun_checkpoint_key(time_key)] = picked


def _sync_canonical_from_time_index(*, time_key: str, time_options: list[str]) -> str:
    """selectbox 인덱스 → canonical 문자열(u_time). 위젯 key(idx)는 건드리지 않음."""
    opts = list(time_options)
    idx_key = _time_widget_index_key(time_key)
    picked = "모름"
    if idx_key in st.session_state:
        try:
            picked = opts[int(st.session_state[idx_key])]
        except (TypeError, ValueError, IndexError):
            picked = _read_canonical_birth_time(time_key)
    else:
        picked = _read_canonical_birth_time(time_key)
    if picked not in opts:
        picked = "모름"
    st.session_state[time_key] = picked
    if picked != "모름":
        st.session_state[_time_last_selected_key(time_key)] = picked
        st.session_state[_time_rerun_checkpoint_key(time_key)] = picked
    return picked


def _sync_birth_time_from_widget(*, time_key: str, time_options: list[str]) -> None:
    _sync_canonical_from_time_index(time_key=time_key, time_options=time_options)


def _birth_time_change_callback(*, time_key: str, time_options: list[str]):
    """태어난 시간 — 선택 직후 canonical·checkpoint 기록."""

    def _cb() -> None:
        _sync_canonical_from_time_index(time_key=time_key, time_options=time_options)

    return _cb


def _resolve_birth_time_label(*, time_key: str, time_options: list[str]) -> str:
    """표시·저장용 canonical 태어난 시간 라벨."""
    return _read_canonical_birth_time(time_key)


def _import_legacy_time_index_to_label(*, time_key: str, time_options: list[str]) -> None:
    """레거시 인덱스 키 → 문자열 time_key 로 1회 이전."""
    opts = list(time_options)
    if isinstance(st.session_state.get(time_key), str) and st.session_state.get(time_key) in opts:
        return
    idx_key = _time_widget_index_key(time_key)
    if idx_key not in st.session_state:
        return
    label = _time_label_from_index(
        st.session_state.get(idx_key, 0),
        time_options=opts,
        time_key=time_key,
    )
    if label != "모름":
        st.session_state[time_key] = label
    st.session_state.pop(idx_key, None)


def _sanitize_time_session_before_widget(*, time_key: str, time_options: list[str]) -> None:
    """selectbox 렌더 직전 — 깨진 값만 복구(유효 선택은 덮어쓰지 않음)."""
    opts = list(time_options)
    _migrate_legacy_time_widget_key(time_key=time_key, time_options=opts)
    _import_legacy_time_index_to_label(time_key=time_key, time_options=opts)

    idx_key = _time_widget_index_key(time_key)
    if idx_key in st.session_state:
        try:
            from_idx = opts[int(st.session_state[idx_key])]
            if from_idx in opts:
                st.session_state[time_key] = from_idx
                return
        except (TypeError, ValueError, IndexError):
            pass

    raw = st.session_state.get(time_key)
    if isinstance(raw, str) and raw in opts:
        return

    coerced = coerce_step2_time_option(raw)
    if coerced in opts and coerced != "모름":
        st.session_state[time_key] = coerced
        return

    for recovery_key in (
        _time_rerun_checkpoint_key(time_key),
        _time_last_selected_key(time_key),
    ):
        last = coerce_step2_time_option(st.session_state.get(recovery_key))
        if last in opts and last != "모름":
            st.session_state[time_key] = last
            st.session_state[idx_key] = opts.index(last)
            return

    if time_key not in st.session_state:
        cur = _read_canonical_birth_time(time_key)
        st.session_state[time_key] = cur if cur in opts else "모름"


def _render_birth_time_select(*, time_key: str, time_options: list[str]) -> None:
    opts = list(time_options)
    idx_key = _time_widget_index_key(time_key)
    st.session_state.pop(_time_index_key(time_key), None)

    _sanitize_time_session_before_widget(time_key=time_key, time_options=opts)

    # 위젯 key는 rerun마다 덮어쓰지 않음 — 모바일 선택 직후 「모름」으로 되돌아가는 원인
    if idx_key not in st.session_state:
        canonical = _read_canonical_birth_time(time_key)
        st.session_state[time_key] = canonical if canonical in opts else "모름"
        st.session_state[idx_key] = _time_option_index(
            st.session_state[time_key], time_options=opts
        )

    st.selectbox(
        "태어난 시간",
        options=list(range(len(opts))),
        format_func=lambda i: opts[int(i)],
        key=idx_key,
        on_change=_birth_time_change_callback(
            time_key=time_key, time_options=time_options
        ),
    )

    _sync_canonical_from_time_index(time_key=time_key, time_options=opts)


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
    st.session_state.u_time = coerce_step2_time_option(_default_self_time())
    st.session_state.u_time_select_idx = _time_option_index(
        st.session_state.u_time, time_options=list(M.STEP2_TIME_OPTIONS)
    )
    st.session_state.pop("u_time_idx", None)
    st.session_state.pop("u_time_widget", None)
    if st.session_state.u_time != "모름":
        st.session_state[_time_last_selected_key("u_time")] = st.session_state.u_time
    self_name = _default_self_name()
    st.session_state.u_name = self_name
    st.session_state[_SELF_NAME_INPUT_KEY] = self_name
    st.session_state.u_gender = _default_self_gender()
    st.session_state.u_contact = _default_contact()
    st.session_state.agree = True

    pd = st.session_state.get("p_data")
    if pd and len(pd) >= 6:
        pn = str(
            st.session_state.get("partner_name_snapshot")
            or st.session_state.get("p_name")
            or ""
        ).strip()
        st.session_state[_OPP_NAME_INPUT_KEY] = pn
        if pn:
            st.session_state.p_name = pn
        st.session_state.p_y = int(pd[0])
        st.session_state.p_m = int(pd[1])
        st.session_state.p_d = int(pd[2])
        st.session_state[_OPP_BDATE_TEXT_KEY] = _format_bdate_str(
            int(pd[0]), int(pd[1]), int(pd[2])
        )
        st.session_state.pop(_OPP_BDATE_KEY, None)
        pt = str(pd[3] or "모름")
        st.session_state.p_time = coerce_step2_time_option(pt)
        st.session_state.p_time_select_idx = _time_option_index(
            st.session_state.p_time, time_options=list(M.STEP2_TIME_OPTIONS)
        )
        st.session_state.pop("p_time_idx", None)
        st.session_state.pop("p_time_widget", None)
        if st.session_state.p_time != "모름":
            st.session_state[_time_last_selected_key("p_time")] = st.session_state.p_time
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
        st.session_state.pop("p_time_idx", None)
        st.session_state.pop("p_time_widget", None)
        st.session_state.pop("p_time_select_idx", None)
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

    u_t_str = _read_canonical_birth_time("u_time")

    self_name = str(
        st.session_state.get(_SELF_NAME_INPUT_KEY)
        or st.session_state.get("u_name")
        or ""
    ).strip()
    opp_name = _resolve_opponent_name_for_save()
    pl = str(st.session_state.get("p_lunar") or "양력")
    if pl not in ("양력", "음력"):
        pl = "양력"
    plp = "평달" if pl == "양력" else str(st.session_state.get("p_leap") or "평달")
    if plp not in ("평달", "윤달"):
        plp = "평달"
    p_t = _read_canonical_birth_time("p_time")
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


def _resolve_self_name_for_save() -> str:
    return str(
        st.session_state.get(_SELF_NAME_INPUT_KEY)
        or st.session_state.get("u_name")
        or ""
    ).strip()


def _resolve_opponent_name_for_save() -> str:
    """상대방 이름 — fragment 입력 직후 저장 시 위젯 키·스냅샷 모두 확인."""
    return str(
        st.session_state.get(_OPP_NAME_INPUT_KEY)
        or st.session_state.get("p_name")
        or st.session_state.get("partner_name_snapshot")
        or ""
    ).strip()


def _step2_show_validation_error(msg: str) -> None:
    st.session_state["_step2_top_alert"] = str(msg)
    st.session_state["_step2_scroll_to_alert"] = True


def try_step2_save_from_session() -> bool:
    """STEP2 입력 검증·저장 후 STEP3 이동. 하단 「다음 →」 on_click 에서 호출."""
    self_nm = _resolve_self_name_for_save()
    if not self_nm:
        _step2_show_validation_error("본인 이름을 입력해 주세요.")
        return False
    if _parse_bdate_text(st.session_state.get(_SELF_BDATE_TEXT_KEY)) is None:
        _step2_show_validation_error(
            "본인 생년월일을 **YYYY/MM/DD** 형식으로 입력해 주세요. (예: 1995/01/01)"
        )
        return False
    _sync_ymd_from_bdate_text(
        bdate_key=_SELF_BDATE_KEY, y_key="u_y", m_key="u_m", d_key="u_d"
    )
    _opp_bdate_raw = str(st.session_state.get(_OPP_BDATE_TEXT_KEY) or "").strip()
    if _opp_bdate_raw and _parse_bdate_text(_opp_bdate_raw) is not None:
        _sync_ymd_from_bdate_text(
            bdate_key=_OPP_BDATE_KEY, y_key="p_y", m_key="p_m", d_key="p_d"
        )
    opp_nm = _resolve_opponent_name_for_save()
    if opp_nm:
        st.session_state[_OPP_NAME_INPUT_KEY] = opp_nm
        st.session_state.p_name = opp_nm
        st.session_state.partner_name_snapshot = opp_nm
    if opp_nm and _parse_bdate_text(
        st.session_state.get(_OPP_BDATE_TEXT_KEY)
        or _format_bdate_str(
            int(st.session_state.get("p_y", 0) or 0),
            int(st.session_state.get("p_m", 0) or 0),
            int(st.session_state.get("p_d", 0) or 0),
        )
    ) is None:
        _step2_show_validation_error(
            "상대방 생년월일을 **YYYY/MM/DD** 형식으로 입력해 주세요. (예: 1990/05/15)"
        )
        return False
    if opp_nm:
        _sync_ymd_from_bdate_text(
            bdate_key=_OPP_BDATE_KEY, y_key="p_y", m_key="p_m", d_key="p_d"
        )
    _sync_birth_time_from_widget(time_key="u_time", time_options=list(M.STEP2_TIME_OPTIONS))
    _sync_birth_time_from_widget(time_key="p_time", time_options=list(M.STEP2_TIME_OPTIONS))
    if not bool(st.session_state.get("agree", False)):
        _step2_show_validation_error(
            "개인정보 수집·이용에 **동의 체크**가 필요합니다. "
            "아래 필수 항목을 체크한 뒤 「다음 →」를 눌러 주세요."
        )
        return False
    payload = _collect_step2_payload_from_session()
    payload["u_name"] = self_nm
    payload["revisit_pin"] = str(st.session_state.get("step2_revisit_pin") or "").strip()
    payload["revisit_pin_confirm"] = str(
        st.session_state.get("step2_revisit_pin_confirm") or ""
    ).strip()
    st.session_state._step2_payload = payload
    st.session_state.pop("_step2_apply_error", None)
    if not M.apply_step2_next_from_payload():
        return False
    return int(st.session_state.get("step", 2)) != 2


def _try_begin_step2_save() -> None:
    try_step2_save_from_session()


def _queue_step2_focus(widget_key: str, *, kind: str = "input") -> None:
    M.queue_widget_focus(widget_key, kind=kind)


def _focus_after_widget(widget_key: str, *, kind: str = "input"):
    def _cb() -> None:
        _queue_step2_focus(widget_key, kind=kind)

    return _cb


def _on_lunar_change_self() -> None:
    if str(st.session_state.get("u_lunar") or "양력") == "양력":
        st.session_state.u_leap = "평달"
    _sync_ymd_from_bdate_text(
        bdate_key=_SELF_BDATE_KEY, y_key="u_y", m_key="u_m", d_key="u_d"
    )


def _on_lunar_change_opp() -> None:
    if str(st.session_state.get("p_lunar") or "양력") == "양력":
        st.session_state.p_leap = "평달"
    _sync_ymd_from_bdate_text(
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
                st.selectbox(
                    "성별",
                    ("남자", "여자"),
                    key=gender_key,
                )

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
                    _render_birth_time_select(
                        time_key=time_key, time_options=time_options
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


def _render_step2_inline_nav_row() -> None:
    """재방문 설정 아래 — 이전·다음 2열(고정 하단 아님)."""
    with st.container(key="step2_inline_nav_row"):
        prev_c, next_c = st.columns(2, gap="small")
        with prev_c:
            st.button(
                "← 이전",
                use_container_width=True,
                key="step2_inline_prev_btn",
                on_click=M.queue_step2_nav_prev,
            )
        with next_c:
            st.button(
                "다음 → 사주 분석",
                type="primary",
                use_container_width=True,
                key="step2_save_and_analyze_btn",
                on_click=M.queue_step2_save_and_analyze,
            )


@st.fragment
def _render_step2_input_fragment() -> None:
    """입력란·탭 — fragment rerun 만 사용해 클릭 시 스크롤이 위로 튕기지 않게."""
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

    with st.container(key="step2_revisit_expander_wrap"):
        with st.expander("재방문 비밀번호 설정 (선택)", expanded=False):
            st.caption("다음 방문 시 본인 정보로 바로 이동합니다.")
            rp1, rp2 = st.columns(2, gap="small")
            with rp1:
                M.revisit_pin_input_no_autofill(
                    "재방문 비밀번호",
                    key="step2_revisit_pin",
                    placeholder="새 비밀번호",
                )
            with rp2:
                M.revisit_pin_input_no_autofill(
                    "비밀번호 확인",
                    key="step2_revisit_pin_confirm",
                    placeholder="한 번 더 입력",
                )


def render() -> None:
    if "_step2_prefill_payload" not in st.session_state:
        st.session_state._step2_prefill_payload = {}
    if "reset_id" not in st.session_state:
        st.session_state.reset_id = 0

    if st.session_state.pop("_step2_clear_nav_pending", False):
        saju_execution.clear_step_nav_pending_now()

    if st.session_state.pop("_step2_apply_pending", False):
        M.apply_step2_next_from_payload()

    apply_err = st.session_state.pop("_step2_apply_error", None)
    top_alert = st.session_state.pop("_step2_top_alert", None)

    if st.session_state.pop("_step2_force_blank", False) or not st.session_state.get(
        "_step2_privacy_clear_applied_v1"
    ):
        _clear_step2_personal_state()
        st.session_state._step2_privacy_clear_applied_v1 = True

    _blank_opp_name_input_once_per_reset()
    _seed_step2_tab_widgets_if_needed()

    if top_alert or apply_err:
        with st.container(key="step2_validation_alert"):
            if top_alert:
                st.error(str(top_alert))
            elif apply_err:
                st.error(str(apply_err))
        saju_execution.inject_step2_validation_alert_scroll_once()

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
                f"**다음 →**을 눌러 주세요."
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

    saju_execution.ensure_calendar_locale_on_step2()
    _render_step2_input_fragment()

    with st.container(key="step2_action_block"):
        if top_alert or apply_err:
            st.warning(
                "⚠️ 위 안내를 확인해 주세요. "
                "**개인정보 동의(필수)** 체크 후 **다음 → 사주 분석**을 눌러 주세요."
            )
        st.checkbox(
            "개인정보 수집·이용에 동의합니다. (필수)",
            key="agree",
        )
        _render_step2_inline_nav_row()

    if st.session_state.pop("_step2_queue_save", False):
        ok = try_step2_save_from_session()
        if ok and int(st.session_state.get("step", 2)) != 2:
            M.rerun_full_app()
        elif not ok:
            st.session_state["_step2_clear_nav_pending"] = True
            saju_execution.clear_step_nav_pending_now()
            M.rerun_full_app()

    M.inject_step2_tab_order_once()
    saju_execution.inject_step2_bdate_input_focus_guard_once()
    saju_execution.inject_step2_scroll_preserve_once()
    protect_step2_birth_time_selects()
