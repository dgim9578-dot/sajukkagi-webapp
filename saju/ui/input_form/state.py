"""STEP2 정보입력 v4 — 세션·위젯 키 (legacy 미사용)."""

from __future__ import annotations

import streamlit as st

from saju_app.persistence.prefill import clear_step2_prefill_storage
from saju_app.ui import components as M

try:
    from saju.ui.step_02 import STEP2_UI_BUILD as INPUT_FORM_BUILD
except ImportError:
    INPUT_FORM_BUILD = "2026-05-22-md08"

_META_KEY = "_in4_meta"
_SEEDED_KEY = "_in4_seeded_retain"

_OPP_DEFAULTS: dict[str, object] = {
    "name": "",
    "y": 1995,
    "m": 1,
    "d": 1,
    "time": "모름",
    "gender": "여자",
    "lunar": "양력",
    "leap": "평달",
}

# 이전 STEP2 구현에서 쓰이던 모든 접두·키 (입력 v4는 in4_* 만 사용)
_OBSOLETE_PREFIXES = (
    "step2_",
    "_step2_",
    "s2v3_",
    "s2self_",
    "s2opp_",
    "step2_self_name",
    "step2_opp_name",
)

_OBSOLETE_EXACT = (
    "p_name",
    "partner_name_snapshot",
    "p_y",
    "p_m",
    "p_d",
    "p_time",
    "p_gender",
    "p_lunar",
    "p_leap",
    "p_data",
    "p_gapja",
    "_step4_partner_bundle",
    "_s2v3_meta",
    "_s2v3_seeded_retain",
)


def purge_obsolete_input_keys(*, include_current_in4: bool = False) -> None:
    """과거 정보입력 위젯·세션 키 제거."""
    if include_current_in4:
        for key in list(st.session_state.keys()):
            sk = str(key)
            if sk.startswith("in4_"):
                st.session_state.pop(key, None)
            if sk.startswith("_in4_"):
                st.session_state.pop(key, None)
    for key in list(st.session_state.keys()):
        sk = str(key)
        for prefix in _OBSOLETE_PREFIXES:
            if sk.startswith(prefix):
                st.session_state.pop(key, None)
                break
    for key in _OBSOLETE_EXACT:
        st.session_state.pop(key, None)
    M.clear_partner_analysis_state()


def meta() -> dict:
    raw = st.session_state.get(_META_KEY)
    if not isinstance(raw, dict):
        raw = {"gen": 0, "opp_open": False, "opp_gen": 0}
        st.session_state[_META_KEY] = raw
    return raw


def self_key(part: str) -> str:
    g = int(meta().get("gen", 0))
    return f"in4_g{g}_self_{part}"


def opp_key(part: str) -> str:
    m = meta()
    g = int(m.get("gen", 0))
    og = int(m.get("opp_gen", 0))
    return f"in4_g{g}_opp{og}_{part}"


def opp_is_open(*, retain: bool) -> bool:
    if retain and M.step2_retain_form_allowed() and M.partner_is_registered():
        return True
    return bool(meta().get("opp_open"))


def purge_opp_keys() -> None:
    g = int(meta().get("gen", 0))
    prefix = f"in4_g{g}_opp"
    for key in list(st.session_state.keys()):
        if str(key).startswith(prefix):
            st.session_state.pop(key, None)


def fresh_start() -> None:
    clear_step2_prefill_storage()
    purge_obsolete_input_keys(include_current_in4=True)
    for key in list(st.session_state.keys()):
        if str(key).startswith("_in4_widgets_ready_"):
            st.session_state.pop(key, None)
    prev = meta()
    st.session_state[_META_KEY] = {
        "gen": int(prev.get("gen", 0)) + 1,
        "opp_open": False,
        "opp_gen": int(prev.get("opp_gen", 0)) + 1,
    }
    st.session_state.pop(_SEEDED_KEY, None)
    st.session_state.pop("_step2_retain_form_active", None)
    st.session_state.pop("_in4_user_touched", None)
    st.session_state.reset_id = int(st.session_state.get("reset_id", 0)) + 1


def unlock_partner() -> None:
    m = meta()
    m["opp_open"] = True
    m["opp_gen"] = int(m.get("opp_gen", 0)) + 1
    purge_obsolete_input_keys()
    for part, val in _OPP_DEFAULTS.items():
        st.session_state[opp_key(part)] = val


def lock_partner() -> None:
    m = meta()
    m["opp_open"] = False
    m["opp_gen"] = int(m.get("opp_gen", 0)) + 1
    purge_opp_keys()
    purge_obsolete_input_keys()


def on_self_edit() -> None:
    mark_user_touched()
    retain = bool(st.session_state.get("_step2_retain_form_active"))
    if opp_is_open(retain=retain):
        return
    lock_partner()


def seed_self(*, retain: bool) -> None:
    if retain and M.step2_retain_form_allowed():
        ud = st.session_state.get("u_data")
        name = str(st.session_state.get("u_name") or "").strip()
        if ud and len(ud) >= 3:
            y, mo, d = int(ud[0]), int(ud[1]), int(ud[2])
        else:
            y, mo, d = 1995, 1, 1
        t = str(ud[3]) if ud and len(ud) >= 4 else "모름"
        if t not in M.STEP2_TIME_OPTIONS:
            t = "모름"
        lunar = "음력" if (ud and len(ud) >= 5 and bool(ud[4])) else "양력"
        leap = "윤달" if (ud and len(ud) >= 6 and bool(ud[5])) else "평달"
        g = str(st.session_state.get("u_gender") or "남자")
        if g not in ("남자", "여자"):
            g = "남자"
        contact = str(st.session_state.get("contact_value") or "").strip()
        if contact == "미등록":
            contact = ""
    else:
        name, y, mo, d = "", 1995, 1, 1
        t, lunar, leap, g, contact = "모름", "양력", "평달", "남자", ""

    st.session_state[self_key("name")] = name
    st.session_state[self_key("y")] = y
    st.session_state[self_key("m")] = mo
    st.session_state[self_key("d")] = d
    st.session_state[self_key("time")] = t
    st.session_state[self_key("gender")] = g
    st.session_state[self_key("lunar")] = lunar
    st.session_state[self_key("leap")] = leap
    st.session_state[self_key("contact")] = contact


def seed_partner_retain() -> None:
    pn = str(
        st.session_state.get("p_name")
        or st.session_state.get("partner_name_snapshot")
        or ""
    ).strip()
    pd = st.session_state.get("p_data")
    st.session_state[opp_key("name")] = pn
    if isinstance(pd, (list, tuple)) and len(pd) >= 3:
        st.session_state[opp_key("y")] = int(pd[0])
        st.session_state[opp_key("m")] = int(pd[1])
        st.session_state[opp_key("d")] = int(pd[2])
        if len(pd) >= 4:
            pt = str(pd[3] or "모름")
            st.session_state[opp_key("time")] = (
                pt if pt in M.STEP2_TIME_OPTIONS else "모름"
            )
        if len(pd) >= 6:
            st.session_state[opp_key("lunar")] = "음력" if bool(pd[4]) else "양력"
            st.session_state[opp_key("leap")] = "윤달" if bool(pd[5]) else "평달"
    pg = st.session_state.get("p_gender")
    if pg in ("남자", "여자"):
        st.session_state[opp_key("gender")] = pg


def _self_field_keys() -> tuple[str, ...]:
    return tuple(self_key(p) for p in ("name", "y", "m", "d", "time", "gender", "lunar", "leap", "contact"))


def _has_user_self_input() -> bool:
    """이미 입력·선택한 본인 값이 있으면 seed 로 덮어쓰지 않습니다."""
    if st.session_state.get("_in4_user_touched"):
        return True
    return bool(str(st.session_state.get(self_key("name")) or "").strip())


def mark_user_touched() -> None:
    st.session_state["_in4_user_touched"] = True


def ensure_widgets(*, retain: bool) -> None:
    rid = int(st.session_state.get("reset_id", 0))
    mk = f"_in4_widgets_ready_{rid}"
    if st.session_state.get(mk):
        return
    st.session_state[mk] = True
    if _has_user_self_input():
        return
    seed_self(retain=retain)
    if retain and M.step2_retain_form_allowed() and M.partner_is_registered():
        m = meta()
        m["opp_open"] = True
        seed_partner_retain()
    elif not opp_is_open(retain=retain):
        meta()["opp_open"] = False
