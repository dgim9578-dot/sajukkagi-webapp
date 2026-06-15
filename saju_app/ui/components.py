"""공통 UI/세션/헬퍼 모음.

2차 정리: 루트 `app.py` 의존을 끊고, step들이 이 모듈만 바라보게 합니다.

전체 앱 재실행은 Streamlit 1.38+ 호환을 위해 `rerun_full_app()`(`saju_app.ui.execution`)을 사용합니다.
"""

from __future__ import annotations

import calendar
import datetime
import base64
import html
import json
import os
import re
import uuid
from functools import lru_cache
from typing import Any
from zoneinfo import ZoneInfo

import streamlit as st
import streamlit.components.v1 as components

from saju_app.persistence import storage as saju_storage
from saju_app.ui.execution import (
    inject_expander_collapse_once,
    inject_step2_tab_order_once,
    inject_widget_focus_return_once,
    queue_expander_collapse,
    queue_widget_focus,
    rerun_full_app,
    report_exception_to_streamlit,
    schedule_force_scroll_after_nav,
)
from saju_app.utils import (
    hx as _hx,
    html_br as _html_br,
    match_body_html as _match_body_html,
    md_bold_to_html_safe as _md_bold_to_html_safe,
)
from mood_assets import list_mood_slugs, mood_image_data_uri

from saju.core.engine import SajuEngine, STEM_ELEMENT, get_element_scores
from saju_app.core import calculations as C
from saju_app.core.sinsal import calculate_sinsal

get_saju_data = C.get_saju_data
compute_daewoon_schedule = C.compute_daewoon_schedule

# -------------------- 시간/빌드 --------------------
def now_kst() -> datetime.datetime:
    return datetime.datetime.now(tz=ZoneInfo("Asia/Seoul"))


def ensure_session_id() -> str:
    sid = str(st.session_state.get("session_id") or "").strip()
    if sid:
        try:
            normalized = saju_storage.normalize_session_id(sid, required=True)
            if normalized != sid:
                st.session_state.session_id = normalized
            return normalized
        except saju_storage.InvalidSessionIdError:
            pass
    sid = uuid.uuid4().hex
    st.session_state.session_id = sid
    return sid


_DRAFT_SKIP_KEYS_ON_RESTORE = frozenset(
    {
        "session_id",
        "step",
        "step2_opp_name_input",
        "p_y",
        "p_m",
        "p_d",
        "p_time",
        "p_lunar",
        "p_leap",
        "p_gender",
        "p_name",
        "partner_name_snapshot",
        "p_data",
        "p_gapja",
        "_step4_partner_bundle",
        "_partner_registered",
    }
)

_PARTNER_ANALYSIS_STATE_KEYS: tuple[str, ...] = (
    "p_name",
    "partner_name_snapshot",
    "p_data",
    "p_gapja",
    "p_gender",
    "p_y",
    "p_m",
    "p_d",
    "p_time",
    "p_lunar",
    "p_leap",
    "_step4_partner_bundle",
    "_step4_pair_sig",
    "saju_engine__partner",
    "saju_engine_sig__partner",
)


def clear_partner_analysis_state() -> None:
    """상대방 미등록·정보입력 초기화 시 궁합(STEP4)에 쓰이는 모든 상대 세션을 제거합니다."""
    for key in _PARTNER_ANALYSIS_STATE_KEYS:
        st.session_state.pop(key, None)
    st.session_state["_partner_registered"] = False
    st.session_state.pop("_partner_registered_visit", None)
    for key in list(st.session_state.keys()):
        sk = str(key)
        if sk.startswith("step2_opp_name_input") or sk.startswith("step2_p_"):
            st.session_state.pop(key, None)
        elif sk.startswith("_step2_opp_"):
            st.session_state.pop(key, None)
    st.session_state.pop("_step2_opp_unlocked", None)
    st.session_state.pop("_step2_self_snap", None)


def _partner_visit_owner() -> str:
    """상대방 등록 시점 visit — 비어 있으면 본인 정보입력 visit 으로 보정."""
    owner = str(st.session_state.get("_partner_registered_visit") or "").strip()
    if owner:
        return owner
    return str(st.session_state.get("_personal_input_visit_id") or "").strip()


def _partner_session_data_ready() -> bool:
    """이름 + 생년월일(간지·p_data·STEP4 번들)이 세션에 있는지."""
    if not _partner_name_from_session():
        return False
    if _gapja_pillars_valid(st.session_state.get("p_gapja"), min_pillars=3):
        return True
    bundle = st.session_state.get("_step4_partner_bundle")
    if isinstance(bundle, dict):
        gj = bundle.get("gapja")
        if isinstance(gj, (list, tuple)) and _gapja_pillars_valid(gj, min_pillars=3):
            return True
    p_data = st.session_state.get("p_data")
    if p_data and isinstance(p_data, (list, tuple)) and len(p_data) >= 6:
        try:
            py, pm, pd = int(p_data[0]), int(p_data[1]), int(p_data[2])
        except (TypeError, ValueError):
            return False
        if 1900 <= py <= 2100 and 1 <= pm <= 12:
            last_d = calendar.monthrange(py, pm)[1]
            if 1 <= pd <= last_d:
                return True
    return False


def reconcile_partner_registration() -> bool:
    """저장 직후 visit 불일치·플래그 누락 시 상대방 등록 상태를 복구합니다."""
    if not personal_input_owner_matches():
        return False
    if not _partner_session_data_ready():
        return False
    mark_partner_registered(active=True)
    return True


def partner_is_registered() -> bool:
    """STEP2에서 상대방 이름·생년월일을 저장한 경우에만 True."""
    if not _partner_name_from_session():
        return False
    if not bool(st.session_state.get("_partner_registered")):
        return reconcile_partner_registration()
    owner_visit = _partner_visit_owner()
    cur_visit = str(st.session_state.get("visit_id") or "").strip()
    if owner_visit and cur_visit and owner_visit == cur_visit:
        return True
    if personal_input_owner_matches() and _partner_session_data_ready():
        mark_partner_registered(active=True)
        return True
    return False


def personal_input_owner_matches() -> bool:
    """현재 visit_id가 마지막 정보입력 저장 주체와 일치하는지."""
    owner = str(st.session_state.get("_personal_input_visit_id") or "").strip()
    visit = str(st.session_state.get("visit_id") or "").strip()
    return bool(owner and visit and owner == visit)


def mark_partner_registered(*, active: bool) -> None:
    st.session_state["_partner_registered"] = bool(active)
    if active:
        vid = str(st.session_state.get("visit_id") or "").strip()
        if not vid:
            try:
                from saju_app.persistence.prefill import ensure_visit_id

                vid = ensure_visit_id()
            except Exception:
                vid = str(st.session_state.get("visit_id") or "").strip()
        if not vid:
            vid = str(st.session_state.get("_personal_input_visit_id") or "").strip()
        st.session_state["_partner_registered_visit"] = vid
    else:
        st.session_state.pop("_partner_registered_visit", None)

_STEP2_FORM_DRAFT_KEYS = frozenset(
    {
        "step2_self_name_input",
        "u_name",
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
        "p_name",
        "partner_name_snapshot",
    }
)


_STEP2_EPOCH_WIDGET_BASES = ("u_y", "u_m", "u_d", "u_contact", "p_y", "p_m", "p_d")


def _pop_step2_form_keys_from_session() -> None:
    """STEP2 입력 위젯·개인정보 세션 키 제거."""
    for key in list(st.session_state.keys()):
        sk = str(key)
        if sk.startswith("step2_self_name_input") or sk.startswith("step2_opp_name_input"):
            st.session_state.pop(key, None)
        if sk.startswith("_step2_opp_blank_"):
            st.session_state.pop(key, None)
        for base in _STEP2_EPOCH_WIDGET_BASES:
            if sk.startswith(f"step2_{base}_"):
                st.session_state.pop(key, None)
    for key in _STEP2_FORM_DRAFT_KEYS:
        st.session_state.pop(key, None)
    for key in (
        "p_y",
        "p_m",
        "p_d",
        "p_time",
        "p_lunar",
        "p_leap",
        "p_gender",
        "p_data",
        "p_gapja",
        "_step4_partner_bundle",
        "u_data",
        "u_gapja",
        "u_name",
        "user_name_snapshot",
        "p_name",
        "partner_name_snapshot",
        "contact_value",
    ):
        st.session_state.pop(key, None)
    for key in list(st.session_state.keys()):
        sk = str(key)
        if sk.startswith("_step2_opp_privacy_") or sk.startswith("_step2_opp_guard_"):
            st.session_state.pop(key, None)
    st.session_state["_step2_widget_epoch"] = int(st.session_state.get("_step2_widget_epoch", 0)) + 1


_STEP2_INPUT_KEY_PREFIXES: tuple[str, ...] = (
    "in4_",
    "s2v3_",
    "step2_self_name_input",
    "step2_opp_name_input",
    "step2_u_",
    "step2_p_",
    "_step2_tabs_seeded_",
    "_step2_opp_privacy_",
    "_step2_opp_guard_",
    "_step2_opp_blank_",
    "_step2_opp_p_",
    "_step2_opp_",
    "_s2v3_",
    "_in4_",
)


def hard_reset_personal_input_state(*, clear_analysis: bool = False) -> None:
    """정보입력(STEP2) — 타 사용자/이전 입력·서버 prefill·위젯 잔존을 강제 제거."""
    clear_partner_analysis_state()
    for key in list(st.session_state.keys()):
        sk = str(key)
        for prefix in _STEP2_INPUT_KEY_PREFIXES:
            if sk.startswith(prefix):
                st.session_state.pop(key, None)
    _pop_step2_form_keys_from_session()
    for key in (
        "agree",
        "step2_revisit_pin",
        "step2_revisit_pin_confirm",
        "_step2_prefill_payload",
        "_step2_payload",
        "_step2_apply_pending",
        "_step2_apply_error",
        "_personal_input_visit_id",
        "_personal_input_saved",
        "saju_briefing",
        "saju_briefing_fp",
        "_saju_step2_input_privacy_guard",
    ):
        st.session_state.pop(key, None)
    for key in list(st.session_state.keys()):
        sk = str(key)
        if sk.startswith("_step2_names_armed_") or sk.startswith("_step2_name_bound_"):
            st.session_state.pop(key, None)
    st.session_state["_step2_opp_epoch"] = int(st.session_state.get("_step2_opp_epoch", 0)) + 1
    st.session_state.pop("_step2_opp_user_touched", None)
    st.session_state.pop("_step2_opp_unlocked", None)
    st.session_state.pop("_step2_self_snap", None)
    st.session_state.pop("_s2v3_meta", None)
    st.session_state.pop("_s2v3_seeded_retain", None)
    st.session_state.pop("_in4_meta", None)
    st.session_state.pop("_in4_seeded_retain", None)
    st.session_state.pop("_step2_retain_form_active", None)
    st.session_state.reset_id = int(st.session_state.get("reset_id", 0)) + 1
    for key in list(st.session_state.keys()):
        sk = str(key)
        if sk.startswith("_step2_opp_privacy_") or sk.startswith("_saju_step2_input_privacy_guard_"):
            st.session_state.pop(key, None)
        if sk.startswith("_s2v3_widgets_ready_") or sk.startswith("_in4_widgets_ready_"):
            st.session_state.pop(key, None)
        if sk.startswith("_saju_step2_privacy_guard_injected_"):
            st.session_state.pop(key, None)
    st.session_state["_step2_prefill_payload"] = {}
    if clear_analysis:
        for key in (
            "u_data",
            "u_gapja",
            "u_name",
            "user_name_snapshot",
            "contact_value",
            "saju_engine",
            "saju_engine_sig",
            "birth_year",
            "birth_month",
            "birth_day",
            "step2_u_bdate",
            "step2_u_bdate_text",
            "step2_p_bdate_text",
        ):
            st.session_state.pop(key, None)
    try:
        rotate_visit_identity()
    except Exception:
        pass
    try:
        purge_all_step2_prefill_from_server()
    except Exception:
        pass
    try:
        sid = ensure_session_id()
        saju_storage.clear_session_draft(sid)
    except Exception:
        pass


def scrub_personal_input_on_home() -> None:
    """홈(STEP1) 진입 — 정보입력란·이름·상대방 잔존 제거(타 단말 노출 방지)."""
    hard_reset_personal_input_state(clear_analysis=False)
    for key in ("u_name", "user_name_snapshot", "contact_value", "agree"):
        st.session_state.pop(key, None)


def force_step2_privacy_reset(*, clear_session_draft: bool = True) -> None:
    """STEP2 — 타 사용자/이전 입력 잔존 강제 제거(세션·서버 KV·위젯 epoch)."""
    hard_reset_personal_input_state(clear_analysis=False)
    if not clear_session_draft:
        return
    try:
        sid = ensure_session_id()
        saju_storage.clear_session_draft(sid)
    except Exception:
        pass
    try:
        clear_step2_prefill_storage()
        purge_shared_step2_prefill_once()
    except Exception:
        pass

_DRAFT_STATE_KEYS = (
    "step11_chat_room_key",
)


def _jsonable_session_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, datetime.date):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [_jsonable_session_value(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable_session_value(v) for k, v in value.items()}
    return str(value)


def persist_current_session_draft(step: int | None = None) -> None:
    """개인정보·사주 draft 서버 저장 비활성 (타 사용자 교차 노출 방지)."""
    _ = step
    return


_BROWSER_CLIENT_TOKEN_KEY = "_saju_browser_client_token"
_BROWSER_PRIVACY_CHECKED_KEY = "_saju_browser_privacy_checked"
_BROWSER_PRIVACY_PENDING_KEY = "_saju_browser_privacy_pending"


def _session_has_foreign_personal_leak() -> bool:
    """저장 주체와 다른 visit·커밋된 스냅샷 잔존 여부 (입력 중 위젯 값은 제외)."""
    owner = str(st.session_state.get("_personal_input_visit_id") or "").strip()
    visit = str(st.session_state.get("visit_id") or "").strip()
    if owner and visit and owner != visit:
        return True
    if not personal_input_owner_matches():
        if str(st.session_state.get("u_name") or st.session_state.get("user_name_snapshot") or "").strip():
            return True
        if str(st.session_state.get("p_name") or st.session_state.get("partner_name_snapshot") or "").strip():
            return True
    if (
        not partner_is_registered()
        and _partner_session_data_ready()
        and not personal_input_owner_matches()
    ):
        return True
    return False


def enforce_browser_privacy_isolation() -> bool | None:
    """브라우저(localStorage) 단위 격리 — Streamlit 세션에 타 사용자 잔존 시 초기화.

    Returns None: JS 응답 대기 중(첫 rerun).
    """
    if st.session_state.get(_BROWSER_PRIVACY_CHECKED_KEY):
        if _session_has_foreign_personal_leak():
            hard_reset_personal_input_state(clear_analysis=True)
            st.session_state.step = 1
        return True
    try:
        from streamlit_javascript import st_javascript
    except ImportError:
        st.session_state[_BROWSER_PRIVACY_CHECKED_KEY] = True
        return True

    raw = st_javascript(
        """
        (function () {
            var roots = [];
            try { roots.push(window); } catch (e) {}
            try { if (window.parent && window.parent !== window) roots.push(window.parent); } catch (e) {}
            try { if (window.top && window.top !== window) roots.push(window.top); } catch (e) {}
            var k = "saju_privacy_client_v2";
            var t = null;
            for (var i = 0; i < roots.length; i++) {
                try {
                    var ls = roots[i].localStorage;
                    if (!ls) continue;
                    t = ls.getItem(k);
                    if (!t) {
                        t = (roots[i].crypto && roots[i].crypto.randomUUID)
                            ? roots[i].crypto.randomUUID()
                            : String(Date.now()) + "-" + Math.random().toString(16).slice(2);
                        try { ls.setItem(k, t); } catch (e2) {}
                    }
                    if (t) break;
                } catch (e) {}
            }
            if (!t) {
                t = "ephemeral-" + String(Date.now()) + "-" + Math.random().toString(16).slice(2);
            }
            return t;
        })()
        """,
        key="saju_browser_privacy_client_v2",
    )
    if raw is None or raw == "" or raw == 0:
        pending = int(st.session_state.get(_BROWSER_PRIVACY_PENDING_KEY, 0)) + 1
        st.session_state[_BROWSER_PRIVACY_PENDING_KEY] = pending
        if pending >= 2:
            token = f"ephemeral-{pending}"
            st.session_state[_BROWSER_CLIENT_TOKEN_KEY] = token
            st.session_state[_BROWSER_PRIVACY_CHECKED_KEY] = True
            return True
        return None

    st.session_state.pop(_BROWSER_PRIVACY_PENDING_KEY, None)

    token = str(raw).strip()
    prev = str(st.session_state.get(_BROWSER_CLIENT_TOKEN_KEY) or "").strip()
    st.session_state[_BROWSER_CLIENT_TOKEN_KEY] = token
    st.session_state[_BROWSER_PRIVACY_CHECKED_KEY] = True

    foreign = _session_has_foreign_personal_leak()
    if prev and prev != token:
        hard_reset_personal_input_state(clear_analysis=True)
        st.session_state.step = 1
        return True
    if foreign:
        hard_reset_personal_input_state(clear_analysis=True)
        st.session_state.step = 1
        return True
    return True


def scrub_step2_partner_leak_before_widgets(*, retain: bool) -> None:
    """STEP2 렌더 직전 — 상대방 legacy·누수 세션 제거."""
    if retain and step2_retain_form_allowed() and partner_is_registered():
        return
    clear_partner_analysis_state()
    for key in (
        "p_name",
        "partner_name_snapshot",
        "p_data",
        "p_gapja",
        "p_y",
        "p_m",
        "p_d",
        "p_time",
        "p_gender",
        "p_lunar",
        "p_leap",
        "_step4_partner_bundle",
    ):
        st.session_state.pop(key, None)


def step2_retain_form_allowed() -> bool:
    """정보입력 수정 모드 — STEP4 등에서 「정보 입력으로」 버튼으로만 허용."""
    if not personal_input_owner_matches():
        return False
    try:
        return_step = int(st.session_state.get("_return_step_after_input") or 0)
    except (TypeError, ValueError):
        return False
    if return_step < 3:
        return False
    return bool(st.session_state.get("_personal_input_saved"))


def inject_step2_input_privacy_guard() -> None:
    """STEP2 이름 입력란 — 네이버 인앱 WebView 자동완성·bfcache·타 사용자 잔존값 억제."""
    import streamlit.components.v1 as components

    rid = int(st.session_state.get("reset_id", 0))
    mk = f"_saju_step2_privacy_guard_injected_{rid}"
    if st.session_state.get(mk):
        return
    st.session_state[mk] = True

    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;padding:0;height:1px;overflow:hidden;'>"
        f"<script>{_STEP2_INPUT_PRIVACY_GUARD_SCRIPT}</script>"
        f"<script>window.__sajuStep2PrivacyRid={rid};</script>"
        "</body></html>"
    )
    with st.container(key=f"saju_step2_privacy_guard_{rid}"):
        components.html(html, height=1, scrolling=False)
    st.markdown(
        f"<script>{_STEP2_INPUT_PRIVACY_GUARD_SCRIPT}</script>",
        unsafe_allow_html=True,
    )


_STEP2_INPUT_PRIVACY_GUARD_SCRIPT = """
(() => {
  const getWin = () => {
    try {
      if (window.parent && window.parent.document) return window.parent;
    } catch (e) {}
    try {
      if (window.top && window.top.document) return window.top;
    } catch (e) {}
    return window;
  };
  const pw = getWin();
  const doc = pw.document;
  if (!doc) return;

  const roots = [
    ".st-key-in4_stack",
    ".st-key-in4_self",
    ".st-key-in4_opp",
    ".st-key-s2v3_stack",
    ".st-key-s2v3_self",
    ".st-key-s2v3_opp",
    ".st-key-step2_section_stack",
    ".st-key-step2_navertone_self",
    ".st-key-step2_navertone_opp",
  ];
  const partnerRoots = [
    ".st-key-in4_opp",
    ".st-key-s2v3_opp",
    ".st-key-step2_navertone_opp",
    ".st-key-step2_section_stack .st-key-step2_navertone_opp",
  ];

  const clearPartnerAutofill = (el) => {
    if (!el || el.dataset.sajuUserEdited === "1") return;
    if (document.activeElement === el) return;
    try {
      const inOpp = partnerRoots.some((ps) => {
        try { return !!el.closest(ps); } catch (e) { return false; }
      });
      if (!inOpp) return;
      const tag = (el.tagName || "").toLowerCase();
      const isNum = el.type === "number" || (el.closest && el.closest(".stNumberInput"));
      const raw = String(el.value || "").trim();
      if (tag === "select") {
        if (raw && raw !== "모름" && raw !== "양력" && raw !== "여자") {
          try { el.selectedIndex = 0; el.dispatchEvent(new Event("change", { bubbles: true })); } catch (e) {}
        }
        return;
      }
      if (!raw) return;
      if (isNum) {
        el.value = el.getAttribute("data-saju-default") || "1995";
      } else {
        el.value = "";
      }
      el.dispatchEvent(new Event("input", { bubbles: true }));
      el.dispatchEvent(new Event("change", { bubbles: true }));
    } catch (e) {}
  };

  const patchInput = (el, isPartner) => {
    if (!el || el.dataset.sajuStep2Patched === "1") return;
    el.dataset.sajuStep2Patched = "1";
    el.setAttribute("autocomplete", "off");
    el.setAttribute("autocorrect", "off");
    el.setAttribute("autocapitalize", "off");
    el.setAttribute("spellcheck", "false");
    el.setAttribute("data-1p-ignore", "true");
    el.setAttribute("data-lpignore", "true");
    el.setAttribute("data-bwignore", "true");
    el.setAttribute("data-form-type", "other");
    try {
      el.setAttribute("name", "saju-step2-" + (isPartner ? "opp-" : "self-") + Math.random().toString(36).slice(2, 10));
    } catch (e) {}
    if (el.type === "text" || el.type === "number" || !el.type) {
      el.addEventListener("input", () => { el.dataset.sajuUserEdited = "1"; }, { passive: true });
    }
    if (isPartner) {
      clearPartnerAutofill(el);
      [120, 400, 900, 1800, 3200, 6000].forEach((ms) => pw.setTimeout(() => clearPartnerAutofill(el), ms));
    }
  };

  const patchTextInput = (el, isPartner) => patchInput(el, isPartner);

  const patchAll = () => {
    roots.forEach((sel) => {
      try {
        doc.querySelectorAll(sel + " input, " + sel + " select").forEach((el) => {
          const isPartner = partnerRoots.some((ps) => {
            try { return !!el.closest(ps); } catch (e) { return false; }
          });
          patchInput(el, isPartner);
        });
      } catch (e) {}
    });
  };

  const clearPartnerSection = () => {
    partnerRoots.forEach((sel) => {
      try {
        doc.querySelectorAll(sel + " input, " + sel + " select").forEach((el) => clearPartnerAutofill(el));
      } catch (e) {}
    });
  };

  patchAll();
  [80, 200, 480, 1000, 2000, 3500, 5500].forEach((ms) => pw.setTimeout(patchAll, ms));

  try {
    const root = doc.body || doc.documentElement;
    if (root && pw.MutationObserver) {
      new pw.MutationObserver(patchAll).observe(root, { childList: true, subtree: true });
    }
  } catch (e) {}

  try {
    pw.addEventListener("pageshow", (ev) => {
      if (ev && ev.persisted) clearPartnerSection();
      patchAll();
    });
  } catch (e) {}

  try {
    const ua = String((pw.navigator && pw.navigator.userAgent) || "");
    if (/NAVER|NaverApp|KAKAOTALK|Instagram|Line\\/|FBAN|FBAV/i.test(ua)) {
      [600, 1500, 3000].forEach((ms) => pw.setTimeout(clearPartnerSection, ms));
    }
  } catch (e) {}
})();
"""


def collect_session_draft_state() -> dict[str, Any]:
    state: dict[str, Any] = {}
    for key in _DRAFT_STATE_KEYS:
        if key in st.session_state:
            state[key] = _jsonable_session_value(st.session_state.get(key))
    return state


_FEATURE_STEPS: frozenset[int] = frozenset({7, 8, 9, 10, 11, 12})

_FEATURE_EPHEMERAL_KEYS: tuple[str, ...] = (
    "step8_tarot_reading",
    "step8_tarot_signature",
)


def clear_feature_ephemeral_state() -> None:
    for key in _FEATURE_EPHEMERAL_KEYS:
        st.session_state.pop(key, None)


def reset_app_to_home_after_browser_reload() -> None:
    """브라우저 F5/새로고침 후 항상 홈(STEP1). draft STEP 복원은 건너뜁니다."""
    st.session_state.step = 1
    st.session_state[QUICK_MENU_OPEN_KEY] = False
    st.session_state.pop("_explicit_feature_step", None)
    st.session_state.pop("_navigated_to_chat_this_run", None)
    st.session_state.pop("_router_last_step", None)
    st.session_state["_session_draft_restored"] = True
    st.session_state["_saju_skip_draft_step_restore"] = True
    st.session_state.pop("_force_scroll_to_top_after_rerun", None)
    st.session_state.pop("_saju_must_scroll_top", None)
    st.session_state.pop("_saju_pending_scroll_top", None)
    st.session_state["_saju_pending_scroll_top"] = True
    st.session_state["_force_scroll_to_top_after_rerun"] = True
    clear_feature_ephemeral_state()
    hard_reset_personal_input_state(clear_analysis=True)
    try:
        sid = ensure_session_id()
        saju_storage.save_session_draft(
            sid,
            {"step": 1, "state": collect_session_draft_state()},
        )
    except Exception:
        pass


def detect_browser_reload() -> bool | None:
    """브라우저 새로고침(F5) 여부. Streamlit 버튼 rerun 과 구분합니다.

    ``st_javascript`` 가 첫 런에서 ``None`` 을 반환할 수 있어, 그때는 ``None`` 을 돌려
    호출 측에서 STEP draft 복원을 미루고 홈(STEP1)을 유지합니다.

    한 브라우저 세션에서 새로고침 여부는 **1회만** 판정합니다. 실제 F5 새로고침은
    Streamlit 세션 자체를 새로 만들어 이 플래그가 사라지므로, 한번 판정한 뒤에는
    버튼/메뉴 rerun 으로 간주합니다. (매 rerun 마다 ``st_javascript`` 를 재호출하면
    본문 뒤 iframe 이 재마운트되며 추가 rerun 이 발생해 STEP 전환이 멈칫거립니다.)
    """
    if st.session_state.get("_saju_browser_reload_resolved"):
        st.session_state.pop("_saju_reload_check_pending", None)
        return False
    try:
        from streamlit_javascript import st_javascript
    except ImportError:
        st.session_state.pop("_saju_reload_check_pending", None)
        st.session_state["_saju_browser_reload_resolved"] = True
        return False

    raw = st_javascript(
        """
        (function () {
            var w = window.parent !== window ? window.parent : window;
            var nav = w.performance.getEntriesByType("navigation")[0];
            var type = nav && nav.type ? nav.type : "navigate";
            return JSON.stringify({
                reload: type === "reload",
                origin: w.performance.timeOrigin || 0
            });
        })()
        """,
        key="saju_browser_nav_check",
    )
    if raw is None or raw == "" or raw == 0:
        st.session_state["_saju_reload_check_pending"] = True
        return None
    try:
        import json as _json

        data = _json.loads(str(raw))
    except Exception:
        st.session_state["_saju_reload_check_pending"] = True
        return None
    try:
        origin = float(data.get("origin") or 0.0)
    except Exception:
        origin = 0.0
    is_reload = bool(data.get("reload"))
    prev = st.session_state.get("_saju_page_load_origin")
    if prev is not None and abs(float(prev) - origin) < 0.001:
        st.session_state.pop("_saju_reload_check_pending", None)
        st.session_state["_saju_browser_reload_resolved"] = True
        return False
    st.session_state["_saju_page_load_origin"] = origin
    st.session_state.pop("_saju_reload_check_pending", None)
    st.session_state["_saju_browser_reload_resolved"] = True
    return is_reload


def apply_browser_refresh_landing() -> None:
    """브라우저 새로고침(F5) 시 홈(STEP1)으로 되돌립니다 (STEP2~12 전부)."""
    reload = detect_browser_reload()
    if reload is None:
        # st_javascript 첫 응답 전(None) — 버튼·메뉴로 바꾼 step 을 덮어쓰지 않음
        if "step" not in st.session_state:
            st.session_state.step = 1
        return
    if reload:
        reset_app_to_home_after_browser_reload()


def guard_feature_step_without_explicit_nav() -> None:
    """타로·챗봇 등 기능 STEP은 메뉴로 연 경우만 유지(새로고침·재진입 시 홈)."""
    if "goto" in st.query_params:
        return
    # 관리자 패널(STEP12)은 별도 인증으로 보호되므로, '명시적 이동' 플래그가 누락돼도 홈으로 튕기지 않게 합니다.
    # (STEP11에서 '관리자 이동 →' 클릭 시 간헐적으로 _explicit_feature_step 이 누락되면 사용자가 홈으로 돌아가는 문제가 있었음)
    try:
        cur = int(st.session_state.get("step", 1))
    except Exception:
        return
    if cur == 12 and admin_panel_enabled():
        return
    if step11_admin_preview_mode():
        return
    if cur not in _FEATURE_STEPS:
        return
    if st.session_state.get("_explicit_feature_step") == cur:
        return
    st.session_state.step = 1
    clear_feature_ephemeral_state()


def restore_session_draft_if_needed() -> None:
    """앱 재진입 시 draft 복원 — 개인정보(u_data·이름·상대방)는 복원하지 않습니다."""
    if st.session_state.get("_session_draft_restored"):
        return
    if st.session_state.get("_saju_reload_check_pending"):
        return
    st.session_state["_session_draft_restored"] = True
    clear_partner_analysis_state()
    for key in (
        "u_name",
        "user_name_snapshot",
        "contact_value",
        "p_name",
        "partner_name_snapshot",
        "p_data",
        "p_gapja",
        "_step4_partner_bundle",
    ):
        st.session_state.pop(key, None)
    try:
        sid = ensure_session_id()
        draft = saju_storage.load_session_draft(sid)
        if not isinstance(draft, dict):
            return
        state = draft.get("state")
        if not isinstance(state, dict):
            return
        for key, value in state.items():
            if str(key) not in _DRAFT_STATE_KEYS:
                continue
            if key not in st.session_state:
                st.session_state[key] = value
        st.session_state.pop("_saju_skip_draft_step_restore", None)
    except Exception:
        pass


def track_analysis_step_for_draft(step: int | None = None) -> None:
    """분석 STEP(1~10)만 draft 복원 대상으로 기록합니다."""
    try:
        cur = int(step if step is not None else st.session_state.get("step", 1))
    except Exception:
        return
    if STEP_NAV_MIN <= cur <= 10:
        st.session_state["_last_analysis_step"] = cur


_LEGACY_BIRTH_META_KEYS: tuple[str, ...] = (
    "summer_time",
    "summer_time_applied",
    "summer_time_offset_minutes",
    "standard_time_adjustment_minutes",
    "standard_time_datetime",
    "time_standard",
    "standard_meridian_lng",
    "birth_longitude_lng",
    "local_mean_time_adjustment_minutes",
    "natural_time_adjustment_minutes",
    "natural_time_datetime",
    "zi_time_policy",
    "zi_boundary",
    "night_zi_day_change",
    "zi_day_pillar_date_adjusted",
    "zi_effective_day_offset_days",
)


def _clean_birth_record(birth: dict[str, Any]) -> dict[str, Any]:
    base = dict(birth or {})
    for key in _LEGACY_BIRTH_META_KEYS:
        base.pop(key, None)
    return base


def _birth_payload_with_time_meta(birth: dict[str, Any]) -> dict[str, Any]:
    return _clean_birth_record(birth)


def _month_method_from_session() -> str:
    opt = st.session_state.get("saju_options", {}) or {}
    return str(opt.get("month_method", "lichun_lunar"))


def _gapja_from_birth(
    y: int,
    m: int,
    d: int,
    t_str: str,
    *,
    is_lunar: bool,
    is_leap: bool,
) -> list[str]:
    h = C.convert_time_str_to_hour(str(t_str))
    return C.get_saju_data(
        int(y),
        int(m),
        int(d),
        h,
        bool(is_lunar),
        bool(is_leap),
        birth_time_str=str(t_str),
        month_method=_month_method_from_session(),
    )


def render_step_intro_banner(
    text: str,
    *,
    emoji: str = "✨",
    accent: str = "#c4b5fd",
) -> None:
    """STEP 상단 한 줄 안내 — 텍스트만 나열되는 느낌을 줄이기 위한 배너."""
    safe = _hx(str(text or ""))
    safe_emoji = _hx(str(emoji or "✨"))
    safe_accent = _hx(str(accent or "#c4b5fd"))
    st.markdown(
        f"""
<div class="saju-step-intro" style="--intro-accent:{safe_accent};">
  <span class="saju-step-intro-emoji">{safe_emoji}</span>
  <span class="saju-step-intro-text">{safe}</span>
</div>
""",
        unsafe_allow_html=True,
    )


def render_mood_image(
    slug: str,
    *,
    variant: str = "hero",
    alt: str = "",
) -> bool:
    """``static/mood/{slug}.webp|png`` 가 있으면 상·중간 무드 배너로 표시."""
    uri = mood_image_data_uri(str(slug or "").strip())
    if not uri:
        return False
    cls_map = {
        "mid": "saju-mood-mid",
        "step6": "saju-mood-step6-hero",
    }
    cls = cls_map.get(str(variant or "").strip().lower(), "saju-mood-hero")
    safe_alt = _hx(str(alt or slug or "mood"))
    st.markdown(
        f'<figure class="{cls}" aria-hidden="false">'
        f'<img src="{uri}" alt="{safe_alt}" loading="lazy" decoding="async" />'
        f"</figure>",
        unsafe_allow_html=True,
    )
    return True


# -------------------- 조후/적천수 가이드 (STEP3 등에서 사용) --------------------
SEASON_MAP = {
    "寅": "봄",
    "卯": "봄",
    "辰": "봄",
    "巳": "여름",
    "午": "여름",
    "未": "여름",
    "申": "가을",
    "酉": "가을",
    "戌": "가을",
    "亥": "겨울",
    "子": "겨울",
    "丑": "겨울",
}

JOHU_GUIDE = {
    "봄": {
        "need": ["火"],
        "desc": "목이 왕성하므로 화로 기운을 따뜻하게 펼쳐줘야 균형이 맞습니다.",
    },
    "여름": {"need": ["水"], "desc": "화가 과열되기 쉬우므로 수로 열을 식혀야 합니다."},
    "가을": {
        "need": ["火"],
        "desc": "금이 건조하므로 화로 온기를 더해 균형을 잡습니다.",
    },
    "겨울": {"need": ["火"], "desc": "수의 한기를 화로 덥혀야 생기가 살아납니다."},
}


def get_season_from_month_branch(month_branch: str | None) -> str:
    return SEASON_MAP.get(str(month_branch or ""), "미상")


def get_johu_advice(month_branch: str | None) -> dict[str, Any]:
    season = get_season_from_month_branch(month_branch)
    guide = JOHU_GUIDE.get(season, {"need": [], "desc": ""})
    return {
        "season": season,
        "need_elements": list(guide.get("need") or []),
        "desc": str(guide.get("desc") or ""),
    }


def get_jukchunsu_advice(strength: str, yongshin: str) -> str:
    from saju_app.ui.plain_language import simplify_jukchunsu_advice

    return simplify_jukchunsu_advice(strength, yongshin)


def element_to_hanja(el: str) -> str:
    """오행 표기를 한글/한자 혼용 -> 한자(木火土金水)로 정규화"""
    if not el:
        return ""
    m = {"목": "木", "화": "火", "토": "土", "금": "金", "수": "水"}
    return m.get(str(el).strip(), str(el).strip())


# -------------------- STEP4 궁합 보조 (app.py에서 이관) --------------------
LIUHE_PAIRS = {
    ("子", "丑"),
    ("寅", "亥"),
    ("卯", "戌"),
    ("辰", "酉"),
    ("巳", "申"),
    ("午", "未"),
}
CHONG_PAIRS = {
    ("子", "午"),
    ("丑", "未"),
    ("寅", "申"),
    ("卯", "酉"),
    ("辰", "戌"),
    ("巳", "亥"),
}
# 형(刑) · 해(害) — 일지가 합·충이 아닐 때도 조합별 해설을 나누기 위함
PUNISH_PAIRS = {
    ("寅", "巳"),
    ("巳", "寅"),
    ("巳", "申"),
    ("申", "巳"),
    ("申", "寅"),
    ("寅", "申"),
    ("丑", "戌"),
    ("戌", "丑"),
    ("戌", "未"),
    ("未", "戌"),
    ("子", "卯"),
    ("卯", "子"),
}
HARM_PAIRS = {
    ("子", "未"),
    ("未", "子"),
    ("丑", "午"),
    ("午", "丑"),
    ("寅", "巳"),
    ("巳", "寅"),
    ("卯", "辰"),
    ("辰", "卯"),
    ("申", "亥"),
    ("亥", "申"),
    ("酉", "戌"),
    ("戌", "酉"),
}

# 천간합(天干合)
STEM_HE_PAIRS: dict[frozenset[str], str] = {
    frozenset({"甲", "己"}): "甲己",
    frozenset({"乙", "庚"}): "乙庚",
    frozenset({"丙", "辛"}): "丙辛",
    frozenset({"丁", "壬"}): "丁壬",
    frozenset({"戊", "癸"}): "戊癸",
}

YIN_STEMS = frozenset({"乙", "丁", "己", "辛", "癸"})


def is_yin_stem(stem: str | None) -> bool:
    return str(stem or "").strip() in YIN_STEMS


def stem_he_relation(a: str | None, b: str | None) -> str:
    """두 천간의 天干合 여부."""
    aa, bb = str(a or "").strip(), str(b or "").strip()
    if not aa or not bb or aa == bb:
        return "없음"
    label = STEM_HE_PAIRS.get(frozenset({aa, bb}))
    return f"天干合({label})" if label else "없음"


def day_branch_match_label(a: str | None, b: str | None) -> str:
    """일지 우선: 동일 → 속궁합, 이후 합·충·형·해."""
    aa, bb = str(a or "").strip(), str(b or "").strip()
    if aa and bb and aa == bb:
        return "일지 동일(속궁합)"
    return branch_pair_relation(a, b)


def element_i_control(day_el: str) -> str:
    """일간 오행이 극(克)하는 오행(=재성 오행)."""
    return {
        "木": "土",
        "火": "金",
        "土": "水",
        "金": "木",
        "水": "火",
    }.get(day_el, "土")


def element_controls_me(day_el: str) -> str:
    """일간 오행을 극(克)하는 오행(=관성 오행)."""
    return {
        "木": "金",
        "火": "水",
        "土": "木",
        "金": "火",
        "水": "土",
    }.get(day_el, "金")


def branch_pair_relation(a: str | None, b: str | None) -> str:
    """두 지지의 핵심 관계(六合/沖/刑/害/없음)."""
    if not a or not b:
        return "없음"
    aa, bb = str(a).strip(), str(b).strip()
    if (aa, bb) in LIUHE_PAIRS or (bb, aa) in LIUHE_PAIRS:
        return "합(六合)"
    if (aa, bb) in CHONG_PAIRS or (bb, aa) in CHONG_PAIRS:
        return "충(沖)"
    if (aa, bb) in PUNISH_PAIRS or (bb, aa) in PUNISH_PAIRS:
        return "형(刑)"
    if (aa, bb) in HARM_PAIRS or (bb, aa) in HARM_PAIRS:
        return "해(害)"
    return "없음"


def top_elements(elements: dict) -> tuple[str, str]:
    if not elements:
        return ("木", "水")
    max_el = max(elements, key=elements.get)
    min_el = min(elements, key=elements.get)
    return (max_el, min_el)


def calc_simple_match_score(
    *,
    day_branch_rel: str,
    element_balance: int,
    spouse_star_fit: int,
    yongshin_fit: int,
    dae_overlap: int,
    day_branch_same: bool = False,
    day_stem_he: bool = False,
    mutual_sheng: bool = False,
    pillar_harmony: int = 0,
    pillar_conflict: int = 0,
    yin_yang_balanced: bool = False,
) -> int:
    """STEP4 요약 점수 — 일지·천간합·오행·용신·년월 합·충·음양 반영."""
    score = 66
    if day_branch_same:
        score += 12
    elif str(day_branch_rel).startswith("합"):
        score += 10
    elif str(day_branch_rel).startswith("충"):
        score -= 14
    elif str(day_branch_rel).startswith("형"):
        score -= 8
    elif str(day_branch_rel).startswith("해"):
        score -= 6
    if day_stem_he:
        score += 6
    if mutual_sheng:
        score += 5
    if yin_yang_balanced:
        score += 3
    elif not day_branch_same and not str(day_branch_rel).startswith("합"):
        score -= 3
    score += int(element_balance)
    score += int(spouse_star_fit)
    score += int(yongshin_fit)
    score += int(dae_overlap)
    score += min(int(pillar_harmony) * 2, 8)
    score -= min(int(pillar_conflict) * 3, 18)
    return max(38, min(int(score), 99))


def next_daewoon_pillars(
    month_pillar: str,
    n: int = 3,
    *,
    gender: str | None = None,
    year_stem: str | None = None,
) -> list[str]:
    """월주 기준 대운 간지 n개. gender·year_stem이 있으면 순행/역행 반영."""
    forward = True
    if gender is not None and year_stem:
        forward = C.daewoon_is_forward(str(year_stem), str(gender))
    try:
        start_idx = C.JIAZI_60.index(month_pillar)
    except Exception:
        start_idx = 0
    out: list[str] = []
    for k in range(1, n + 1):
        if forward:
            out.append(C.JIAZI_60[(start_idx + k) % 60])
        else:
            out.append(C.JIAZI_60[(start_idx - k) % 60])
    return out


STEP_NAV_MIN = 1
STEP_NAV_MAX = 12

# ====================== STEP 순서 정의 ======================
STEP_ORDER: list[int] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

STEP_NAMES: dict[int, str] = {
    1: "홈",
    2: "정보입력",
    3: "사주분석",
    4: "궁합",
    5: "살풀이",
    6: "오늘의 운세",
    7: "주역",
    8: "AI 타로",
    9: "대운",
    10: "총평",
    11: "AI 챗봇",
    12: "관리자",
}


def get_next_step(current_step: int) -> int:
    """현재 step에서 다음 step으로 이동."""
    try:
        idx = STEP_ORDER.index(int(current_step))
        if idx + 1 < len(STEP_ORDER):
            return STEP_ORDER[idx + 1]
    except ValueError:
        pass
    return int(current_step)


def _columns_compat(n: int):
    """구버전 Streamlit은 columns(..., gap=) 미지원."""
    if n <= 0:
        return []
    try:
        return st.columns(n, gap="small")
    except TypeError:
        return st.columns(n)


# -------------------- 앱 디렉토리/정적 리소스 --------------------
# step 모듈들이 기대하는 상수들(배너/QR 등)
_APP_DIR = str(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# QR 코드 이미지 (base64) — 프로젝트 루트의 qr.jpg
QR_DATA = ""
try:
    _qr_path = os.path.join(_APP_DIR, "qr.jpg")
    if os.path.isfile(_qr_path):
        with open(_qr_path, "rb") as f:
            QR_DATA = base64.b64encode(f.read()).decode()
except Exception:
    QR_DATA = ""


# -------------------- STEP 메뉴/상수 --------------------
# 하단 기능 메뉴(접기) 전용: (이모지, 짧은 명칭, step) — 6+5 그리드 순서(사진2 레이아웃)
STEP_DOCK_ITEMS = (
    ("🧾", "명백", 2),
    ("🔮", "사주", 3),
    ("💞", "궁합", 4),
    ("🧿", "살풀이", 5),
    ("🌤️", "오늘", 6),
    ("☯️", "주역", 7),
    ("🃏", "타로", 8),
    ("📈", "대운", 9),
    ("📋", "총평", 10),
    ("🤖", "챗봇", 11),
    ("⚙️", "관리", 12),
)

# 하단 이전/다음 버튼에 쓰는 창 이름(STEP 번호와 대응, ``STEP_NAMES`` 와 동기)
STEP_WINDOW_TITLE: dict[int, str] = dict(STEP_NAMES)

# 독 버튼 help 툴팁(짧은 라벨 ↔ 전체 메뉴명)
STEP_DOCK_HELP: dict[int, str] = {
    1: "홈(메인)으로 이동합니다.",
    2: "정보 입력(명백)으로 이동합니다.",
    3: "사주 분석으로 이동합니다.",
    4: "궁합·인연으로 이동합니다.",
    5: "12신살(살풀이)로 이동합니다.",
    6: "오늘의 운세로 이동합니다.",
    7: "주역으로 이동합니다.",
    8: "AI 타로 점으로 이동합니다.",
    9: "대운·재물·커리어 운세로 이동합니다.",
    10: "총평으로 이동합니다.",
    11: "AI 상담(챗봇)으로 이동합니다.",
    12: "관리자 메뉴로 이동합니다.",
}


def admin_panel_enabled() -> bool:
    """Google Play 공개 빌드에서는 관리자 화면을 기본 비노출로 둡니다."""
    raw = os.environ.get("SAJU_ADMIN_ENABLED", "")
    if not raw:
        try:
            raw = str(st.secrets.get("SAJU_ADMIN_ENABLED", ""))
        except Exception:
            raw = ""
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def admin_session_authenticated() -> bool:
    return bool(st.session_state.get("saju_admin_authenticated"))


def step11_admin_preview_mode() -> bool:
    """8502 관리자 앱에서 STEP11은 고객 사주 세션 없이 채팅만 확인합니다."""
    return admin_panel_enabled() and admin_session_authenticated()


def _visible_step_dock_items():
    if admin_panel_enabled():
        return STEP_DOCK_ITEMS
    return tuple(item for item in STEP_DOCK_ITEMS if int(item[2]) != 12)


def _step_dock_html_cell(emo: str, cap: str, dest: int, *, unlocked: bool) -> str:
    """HTML 한 칸 — 잠금 시 ``<span>``, 해제 시 ``<a href=?goto=…>``."""
    emo_h = html.escape(str(emo))
    cap_h = html.escape(" ".join(str(cap).replace("\n", " ").split()))
    tip = str(STEP_DOCK_HELP.get(int(dest), ""))
    tip_h = html.escape(tip, quote=True)
    inner = (
        f'<span class="saju-dock-emo" aria-hidden="true">{emo_h}</span>'
        f'<span class="saju-dock-cap">{cap_h}</span>'
    )
    if unlocked:
        # target="_top" 은 iframe/인앱 WebView에서 세션이 끊긴 뒤 ?goto= 만 적용되는 케이스가 있어
        # 같은 browsing context 에서 Streamlit 세션을 유지하도록 생략합니다.
        return (
            f'<a class="saju-dock-a" href="?goto={int(dest)}" rel="noopener" title="{tip_h}" '
            f'aria-label="{tip_h}">{inner}</a>'
        )
    return f'<span class="saju-dock-off" title="{tip_h}" aria-label="{tip_h}">{inner}</span>'


def _step_dock_html_full(*, unlocked: bool) -> str:
    items = _visible_step_dock_items()
    cells = [_step_dock_html_cell(e, c, d, unlocked=unlocked) for e, c, d in items]
    r1 = "".join(cells[:6])
    r2 = "".join(cells[6:])
    return (
        '<div class="saju-step-dock-html" data-layout="grid-6-5">'
        f'<div class="saju-dock-row r1">{r1}</div>'
        f'<div class="saju-dock-row r2">{r2}</div>'
        "</div>"
    )


def analysis_flow_unlocked() -> bool:
    """본인 사주가 저장·계산되었으면 STEP3+·하단 메뉴 이동을 허용합니다.

    ``u_name`` 은 STEP2 위젯 키와 묶여 다른 STEP에서 비어 있을 수 있어,
    ``u_gapja``·``u_data``·``_personal_input_saved``·``saju_engine`` 을 함께 봅니다.
    """
    if _gapja_pillars_valid(st.session_state.get("u_gapja"), min_pillars=3):
        return True
    if st.session_state.get("_personal_input_saved") and st.session_state.get("u_data"):
        _resync_user_gapja_from_u_data()
        if _gapja_pillars_valid(st.session_state.get("u_gapja"), min_pillars=3):
            return True
    if _engine_dict_coherent(st.session_state.get("saju_engine")):
        return True
    return False


def session_user_display_name() -> str:
    """표시용 본인 이름: ``u_name`` 이 비면 저장 시점 스냅샷(``user_name_snapshot``)을 사용합니다."""
    u = str(st.session_state.get("u_name") or "").strip()
    if u:
        return u
    return str(st.session_state.get("user_name_snapshot") or "").strip()


STEP2_TIME_OPTIONS = (
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
    """태어난 시간 selectbox — 깨진·축약·인덱스 라벨을 정식 옵션으로 복원."""
    opts = STEP2_TIME_OPTIONS
    if isinstance(raw, bool):
        return "모름"
    if isinstance(raw, int):
        if 0 <= raw < len(opts):
            return opts[raw]
        return "모름"
    if isinstance(raw, float) and raw == int(raw):
        idx = int(raw)
        if 0 <= idx < len(opts):
            return opts[idx]
        return "모름"
    val = str(raw or "").strip()
    if val in opts:
        return val
    if not val:
        return "모름"
    if val.isdigit():
        idx = int(val)
        if 0 <= idx < len(opts):
            return opts[idx]
    for opt in opts:
        if opt.startswith(val):
            return opt
        if len(val) >= 2 and val in opt:
            return opt
        head = opt.split("(")[0]
        if head and (val.startswith(head) or head.startswith(val)):
            return opt
    # 달력 월 패치가 "5월" / "5." 로 바꾼 값 — 시간 옵션이 아님
    if re.match(r"^\d{1,2}\s*월\.?$", val):
        return "모름"
    branch = re.match(r"^([자축인묘진사오미신유술해])", val)
    if branch:
        b = branch.group(1)
        for opt in opts[1:]:
            if opt.startswith(f"{b}("):
                return opt
    return "모름"


def step2_time_option_index(raw: object) -> int:
    """``u_time`` / ``p_time`` 문자열 또는 인덱스 → selectbox용 0~12."""
    if isinstance(raw, int):
        return max(0, min(len(STEP2_TIME_OPTIONS) - 1, raw))
    if isinstance(raw, str) and raw.strip().isdigit():
        return max(0, min(len(STEP2_TIME_OPTIONS) - 1, int(raw.strip())))
    label = coerce_step2_time_option(raw)
    try:
        return STEP2_TIME_OPTIONS.index(label)
    except ValueError:
        return 0


# -------------------- STEP2 prefill persistence (persistence로 위임) --------------------
from saju_app.persistence.prefill import (  # noqa: E402
    clear_step2_prefill_storage,
    ensure_fresh_client_identity,
    purge_all_step2_prefill_from_server,
    purge_shared_step2_prefill_once,
    rotate_visit_identity,
)


# -------------------- input helpers --------------------
# Chrome/Edge는 autocomplete=off 를 무시하는 경우가 많아 one-time-code 사용
_AUTOCOMPLETE_TEXT = "one-time-code"
_AUTOCOMPLETE_OFF = "one-time-code"
_AUTOCOMPLETE_PASSWORD = "new-password"
_AUTOCOMPLETE_REVISIT_PIN = "one-time-code"
_AUTOFILL_GUARD_VERSION = "v11"
_REVISIT_PIN_RULE_TEXT = "비밀번호는 숫자 특수문자 포함 6자 이상 설정 하세요"
_REVISIT_PIN_RULE_TEXT_HOME = "비밀번호는 특수문자 포함 6자 이상 설정 하세요"

_GLOBAL_AUTOFILL_GUARD_SCRIPT = """
<script>
(() => {{
    const GUARD_VER = "v11";
    const pw = window.parent !== window ? window.parent : window;
    const doc = pw.document;
    if (!doc) return;
    if (pw.__sajuAutofillGuardVer === GUARD_VER) return;
    pw.__sajuAutofillGuardVer = GUARD_VER;
    let queued = false;
    const randSuffix = () => Math.random().toString(36).slice(2, 10);
    const isMaskedSecretField = (el) => {{
        if (!el) return false;
        try {{
            return !!el.closest(
                ".st-key-step1_cta_row_main, .st-key-step1_revisit_pin_in, " +
                    "[class*='st-key-step2_revisit_pin'], " +
                    ".st-key-step2_revisit_pin, .st-key-step2_revisit_pin_confirm, " +
                    ".st-key-step12_admin_login_panel, .st-key-step12_admin_pwd_input"
            );
        }} catch (_) {{
            return false;
        }}
    }};
    const isBirthDateTextField = (el) => {{
        if (!el) return false;
        try {{
            return !!el.closest(
                "[class*='step2_u_bdate_text'], [class*='step2_p_bdate_text'], " +
                    "[class*='st-key-step2_u_bdate'], [class*='st-key-step2_p_bdate']"
            );
        }} catch (_) {{
            return false;
        }}
    }};
    const isCredentialSensitiveText = (el) => {{
        if (!el) return false;
        try {{
            if (
                el.closest(
                    "[class*='st-key-step2_u_bdate'], [class*='st-key-step2_p_bdate'], " +
                        "[class*='step2_u_bdate_text'], [class*='step2_p_bdate_text']"
                )
            ) {{
                return true;
            }}
            const ph = String(el.getAttribute("placeholder") || "");
            if (/\\d{{4}}\\/\\d{{2}}\\/\\d{{2}}/.test(ph)) return true;
            const keyCls = String(el.closest("[class*='st-key-']")?.className || "");
            if (/bdate|contact|revisit|password|pin|admin_pwd/i.test(keyCls)) return true;
        }} catch (_) {{}}
        return false;
    }};
    const ensureDecoyFields = () => {{
        if (doc.getElementById("saju-autofill-decoy")) return;
        try {{
            const box = doc.createElement("div");
            box.id = "saju-autofill-decoy";
            box.setAttribute("aria-hidden", "true");
            box.style.cssText =
                "position:fixed;left:-10000px;top:0;width:1px;height:1px;overflow:hidden;opacity:0;pointer-events:none;";
            box.innerHTML =
                '<input type="text" tabindex="-1" autocomplete="username" name="saju-decoy-user">' +
                '<input type="password" tabindex="-1" autocomplete="current-password" name="saju-decoy-pass">';
            (doc.body || doc.documentElement).appendChild(box);
        }} catch (_) {{}}
    }};
    const stripEnterApplyHint = (el) => {{
        if (!el) return;
        try {{
            const ph = String(el.getAttribute("placeholder") || "");
            if (/엔터|신청|Press Enter|Enter to/i.test(ph)) {{
                el.removeAttribute("placeholder");
            }}
            const aria = String(el.getAttribute("aria-label") || "");
            if (/엔터|신청|Press Enter|Enter to/i.test(aria)) {{
                el.removeAttribute("aria-label");
            }}
        }} catch (_) {{}}
    }};
    const bindReadonlyUnlock = (el) => {{
        if (!el || el.dataset.sajuReadonlyUnlock === "1") return;
        el.dataset.sajuReadonlyUnlock = "1";
        const unlock = () => {{
            try {{ el.removeAttribute("readonly"); }} catch (_) {{}}
        }};
        try {{ el.setAttribute("readonly", "readonly"); }} catch (_) {{}}
        el.addEventListener("focus", unlock, {{ passive: true }});
        el.addEventListener("pointerdown", unlock, {{ passive: true }});
        el.addEventListener("click", unlock, {{ passive: true }});
    }};
    const patchBirthDateOnly = (el) => {{
        if (!el || el.nodeType !== 1) return;
        stripEnterApplyHint(el);
        el.setAttribute("autocomplete", "one-time-code");
        el.setAttribute("autocorrect", "off");
        el.setAttribute("autocapitalize", "off");
        el.setAttribute("spellcheck", "false");
        el.setAttribute("aria-autocomplete", "none");
        el.setAttribute("data-1p-ignore", "true");
        el.setAttribute("data-lpignore", "true");
        el.setAttribute("data-form-type", "other");
        el.setAttribute("data-saju-no-credential", "1");
        el.setAttribute("data-saju-bdate-field", "1");
        try {{ el.removeAttribute("readonly"); }} catch (_) {{}}
    }};
    const patchOne = (el) => {{
        if (!el || el.nodeType !== 1) return;
        const tag = String(el.tagName || "").toLowerCase();
        if (tag !== "input" && tag !== "textarea") return;
        stripEnterApplyHint(el);
        if (isBirthDateTextField(el)) {{
            if (doc.activeElement === el) return;
            patchBirthDateOnly(el);
            return;
        }}
        const type = String(el.type || "text").toLowerCase();
        if (
            type === "hidden" ||
            type === "checkbox" ||
            type === "radio" ||
            type === "submit" ||
            type === "button" ||
            type === "file"
        ) {{
            return;
        }}
        const revisit = isMaskedSecretField(el);
        if (revisit && type === "password") {{
            try {{ el.type = "text"; }} catch (_) {{}}
            type = "text";
            el.dataset.sajuRevisitPin = "1";
            try {{
                el.style.setProperty("-webkit-text-security", "disc");
                el.style.setProperty("text-security", "disc");
            }} catch (_) {{}}
        }}
        const sensitiveText =
            type !== "password" && (isCredentialSensitiveText(el) || revisit);
        let ac = "one-time-code";
        if (type === "password") {{
            ac = revisit ? "one-time-code" : "new-password";
        }}
        el.setAttribute("autocomplete", ac);
        el.setAttribute("autocorrect", "off");
        el.setAttribute("autocapitalize", "off");
        el.setAttribute("spellcheck", "false");
        el.setAttribute("aria-autocomplete", "none");
        el.setAttribute("data-1p-ignore", "true");
        el.setAttribute("data-lpignore", "true");
        el.setAttribute("data-form-type", "other");
        el.setAttribute("data-saju-no-credential", "1");
        if (type === "password" || revisit) {{
            el.setAttribute("data-bwignore", "true");
        }}
        if (!el.dataset.sajuFieldName) {{
            el.dataset.sajuFieldName = "1";
            try {{
                el.setAttribute("name", "saju-field-" + randSuffix());
            }} catch (_) {{}}
        }}
        if (sensitiveText || revisit) {{
            if (!isBirthDateTextField(el)) {{
                bindReadonlyUnlock(el);
            }}
        }}
    }};
    const patchForms = () => {{
        try {{
            doc.querySelectorAll("form").forEach((form) => {{
                form.setAttribute("autocomplete", "off");
            }});
        }} catch (_) {{}}
    }};
    const hideInputInstructions = () => {{
        try {{
            doc.querySelectorAll('[data-testid="InputInstructions"]').forEach((node) => {{
                const inStep2 = node.closest(
                    ".st-key-step2_navertone_self, .st-key-step2_navertone_opp, .st-key-step2_save_actions"
                );
                if (inStep2) node.remove();
            }});
        }} catch (_) {{}}
    }};
    const patchAll = () => {{
        queued = false;
        ensureDecoyFields();
        patchForms();
        try {{
            doc.querySelectorAll("input, textarea").forEach(patchOne);
        }} catch (_) {{}}
        hideInputInstructions();
    }};
    let debounceTimer = null;
    const schedule = () => {{
        if (debounceTimer) {{
            try {{ clearTimeout(debounceTimer); }} catch (_) {{}}
        }}
        debounceTimer = pw.setTimeout(function () {{
            debounceTimer = null;
            if (pw.__sajuBdateFocusLock) return;
            if (queued) return;
            queued = true;
            try {{ pw.requestAnimationFrame(patchAll); }} catch (_) {{ patchAll(); }}
        }}, 220);
    }};
    schedule();
    [120, 480].forEach((ms) => pw.setTimeout(schedule, ms));
    try {{
        const root = doc.body || doc.documentElement;
        if (root && pw.MutationObserver) {{
            new pw.MutationObserver(schedule).observe(root, {{
                childList: true,
                subtree: true,
            }});
        }}
    }} catch (_) {{}}
}})();
</script>
"""

_REVISIT_PIN_AUTOFILL_SCRIPT = """
<script>
(() => {{
    const pw = window.parent !== window ? window.parent : window;
    const doc = pw.document;
    if (!doc) return;
    const GUARD_VER = "v11";
    if (pw.__sajuRevisitPinGuardVer === GUARD_VER) return;
    pw.__sajuRevisitPinGuardVer = GUARD_VER;
    const roots = [
        ".st-key-step1_cta_row_main",
        ".st-key-step1_revisit_pin_in",
        ".st-key-step2_revisit_pin",
        ".st-key-step2_revisit_pin_confirm",
        '[class*="st-key-step2_revisit_pin"]',
        ".st-key-step12_admin_login_panel",
        ".st-key-step12_admin_pwd_input",
    ];
    const isSecretMaskInput = (el) => {{
        if (!el) return false;
        try {{
            return roots.some((sel) => !!el.closest(sel));
        }} catch (_) {{
            return false;
        }}
    }};
    const patchSecretMaskInput = (el) => {{
        if (!el || el.nodeType !== 1 || !isSecretMaskInput(el)) return;
        const tag = String(el.tagName || "").toLowerCase();
        if (tag !== "input") return;
        let type = String(el.type || "text").toLowerCase();
        if (type === "password") {{
            try {{ el.type = "text"; }} catch (_) {{}}
            type = "text";
        }}
        if (type !== "text" && type !== "search") return;
        el.dataset.sajuRevisitPin = "1";
        el.setAttribute("autocomplete", "one-time-code");
        el.setAttribute("autocorrect", "off");
        el.setAttribute("autocapitalize", "off");
        el.setAttribute("spellcheck", "false");
        el.setAttribute("aria-autocomplete", "none");
        el.setAttribute("data-1p-ignore", "true");
        el.setAttribute("data-lpignore", "true");
        el.setAttribute("data-bwignore", "true");
        el.setAttribute("data-form-type", "other");
        el.setAttribute("data-saju-no-credential", "1");
        el.setAttribute("inputmode", "text");
        try {{
            el.style.setProperty("-webkit-text-security", "disc");
            el.style.setProperty("text-security", "disc");
        }} catch (_) {{}}
        if (!el.dataset.sajuFieldName) {{
            el.dataset.sajuFieldName = "1";
            try {{
                el.setAttribute(
                    "name",
                    "saju-secret-" + Math.random().toString(36).slice(2, 10)
                );
            }} catch (_) {{}}
        }}
        if (el.dataset.sajuRevisitPatched === "1") return;
        el.dataset.sajuRevisitPatched = "1";
        el.setAttribute("readonly", "readonly");
        const unlock = () => {{
            try {{ el.removeAttribute("readonly"); }} catch (_) {{}}
        }};
        el.addEventListener("mousedown", unlock, {{ capture: true, passive: true }});
        el.addEventListener("touchstart", unlock, {{ capture: true, passive: true }});
        el.addEventListener("focus", unlock, {{ passive: true }});
    }};
    const patchForms = () => {{
        try {{
            doc.querySelectorAll("form").forEach((form) => {{
                const hasSecret = roots.some((sel) => {{
                    try {{ return !!form.querySelector(sel); }} catch (_) {{ return false; }}
                }});
                if (!hasSecret) return;
                form.setAttribute("autocomplete", "off");
                form.setAttribute("data-saju-secret-form", "1");
            }});
        }} catch (_) {{}}
    }};
    const run = () => {{
        patchForms();
        roots.forEach((sel) => {{
            try {{
                doc.querySelectorAll(sel + " input").forEach(patchSecretMaskInput);
            }} catch (_) {{}}
        }});
    }};
    run();
    [0, 80, 220, 520, 1100].forEach((ms) => pw.setTimeout(run, ms));
    try {{
        const root = doc.body || doc.documentElement;
        if (root && pw.MutationObserver) {{
            new pw.MutationObserver(run).observe(root, {{ childList: true, subtree: true }});
        }}
    }} catch (_) {{}}
}})();
</script>
"""


def _with_autocomplete_kwargs(kwargs: dict[str, Any], *, password: bool = False) -> dict[str, Any]:
    out = dict(kwargs)
    if "autocomplete" not in out:
        out["autocomplete"] = _AUTOCOMPLETE_PASSWORD if password else _AUTOCOMPLETE_OFF
    return out


def text_input_no_autofill(*args, **kwargs):
    """브라우저 저장 정보(자동완성) 팝업 억제."""
    inject_global_input_autofill_guard()
    password = kwargs.get("type") == "password"
    kwargs = _with_autocomplete_kwargs(kwargs, password=password)
    try:
        return st.text_input(*args, **kwargs)
    except TypeError:
        kwargs.pop("autocomplete", None)
        return st.text_input(*args, **kwargs)


def password_input_no_autofill(*args, **kwargs):
    """비밀번호 입력 — 저장된 암호 제안 억제."""
    inject_global_input_autofill_guard()
    kwargs["type"] = "password"
    kwargs = _with_autocomplete_kwargs(kwargs, password=True)
    try:
        return st.text_input(*args, **kwargs)
    except TypeError:
        kwargs.pop("autocomplete", None)
        return st.text_input(*args, **kwargs)


def render_revisit_pin_rule_hint(*, compact: bool = False, home: bool = False) -> None:
    """재방문 비밀번호 입력란 위 규칙 안내."""
    cls = "saju-revisit-pin-rule saju-revisit-pin-rule--compact" if compact else "saju-revisit-pin-rule"
    text = _REVISIT_PIN_RULE_TEXT_HOME if home else _REVISIT_PIN_RULE_TEXT
    st.markdown(
        f'<p class="{cls}">{_hx(text)}</p>',
        unsafe_allow_html=True,
    )


def inject_secret_mask_autofill_guard_once() -> None:
    """재방문·관리자 등 — Chrome/Edge 「저장된 암호」 팝업 억제."""
    rid = int(st.session_state.get("reset_id", 0))
    guard_key = f"_saju_secret_mask_autofill_guard_{_AUTOFILL_GUARD_VERSION}_{rid}"
    if st.session_state.get(guard_key):
        return
    st.session_state[guard_key] = True
    inject_global_input_autofill_guard()
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;padding:0;height:1px;overflow:hidden;'>"
        f"{_REVISIT_PIN_AUTOFILL_SCRIPT}</body></html>"
    )
    with st.container(key=f"saju_secret_mask_guard_{_AUTOFILL_GUARD_VERSION}_{rid}"):
        components.html(html, height=1, scrolling=False)
    st.markdown(_REVISIT_PIN_AUTOFILL_SCRIPT, unsafe_allow_html=True)


def inject_revisit_pin_autofill_guard_once() -> None:
    """재방문 PIN — Chrome/Edge 「저장된 암호」 팝업 추가 억제."""
    inject_secret_mask_autofill_guard_once()


def revisit_pin_input_no_autofill(*args, **kwargs):
    """재방문 비밀번호 — 브라우저 저장 암호 팝업 강력 억제."""
    inject_secret_mask_autofill_guard_once()
    out = dict(kwargs)
    # type=password 는 Chrome「저장된 암호」 팝업을 유발 → text + JS/CSS 마스킹
    out.pop("type", None)
    out["autocomplete"] = _AUTOCOMPLETE_REVISIT_PIN
    try:
        return st.text_input(*args, **out)
    except TypeError:
        out.pop("autocomplete", None)
        return st.text_input(*args, **out)


def admin_password_input_no_autofill(*args, **kwargs):
    """관리자 비밀번호 — 브라우저 저장 암호 팝업 강력 억제."""
    inject_secret_mask_autofill_guard_once()
    out = dict(kwargs)
    out.pop("type", None)
    out["autocomplete"] = _AUTOCOMPLETE_REVISIT_PIN
    try:
        return st.text_input(*args, **out)
    except TypeError:
        out.pop("autocomplete", None)
        return st.text_input(*args, **out)


def text_area_no_autofill(*args, **kwargs):
    """여러 줄 입력 — Streamlit textarea는 autocomplete 미지원, 전역 JS가 보완."""
    inject_global_input_autofill_guard()
    out = dict(kwargs)
    if "autocomplete" not in out:
        out["autocomplete"] = _AUTOCOMPLETE_TEXT
    try:
        return st.text_area(*args, **out)
    except TypeError:
        out.pop("autocomplete", None)
        return st.text_area(*args, **out)


def inject_global_input_autofill_guard() -> None:
    """앱 전체 input/textarea — 브라우저 저장 암호·번호 자동완성 억제."""
    guard_key = f"_saju_autofill_guard_{_AUTOFILL_GUARD_VERSION}"
    if st.session_state.get(guard_key):
        return
    st.session_state[guard_key] = True
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;padding:0;height:1px;overflow:hidden;'>"
        f"{_GLOBAL_AUTOFILL_GUARD_SCRIPT}</body></html>"
    )
    with st.container(key=f"saju_autofill_guard_{_AUTOFILL_GUARD_VERSION}"):
        components.html(html, height=1, scrolling=False)


def number_input_optimized(label: str, value: int, min_value: int, max_value: int, key: str, suffix: str):
    unique_key = f"{key}_{st.session_state.get('reset_id', 0)}"
    try:
        return int(
            st.number_input(
                label,
                min_value=int(min_value),
                max_value=int(max_value),
                value=int(value),
                step=1,
                key=unique_key,
                label_visibility="collapsed",
                help=f"{suffix} 입력",
            )
        )
    except Exception:
        return int(st.number_input(label, min_value=int(min_value), max_value=int(max_value), value=int(value), step=1, key=unique_key))


def _step2_lbl(text: str) -> None:
    st.caption(str(text))


def premium_analysis_shell(step: int):
    """STEP 3~10 분석 본문용 통일 `.card` 스킨 래퍼.

    스타일은 ``saju/bootstrap.py`` 의 ``:is(... st-key-saju_analysis_card ...)`` 규칙과 동일합니다.
    """
    return st.container(key=f"saju_analysis_card_step{int(step)}")


# -------------------- query param cleanup --------------------
def clear_goto_query_and_reset_nav_tracking():
    try:
        qp = st.query_params
        if "goto" in qp:
            del qp["goto"]
    except Exception:
        pass


def try_restore_step2_from_disk_prefill_if_needed() -> None:
    """비활성 — STEP2 개인정보는 서버 prefill/draft에 저장·복원하지 않습니다."""
    return


_STEPS_NEED_PROFILE_FOR_NAV = frozenset({3, 4, 5, 6, 7, 8, 9, 10, 11})

QUICK_MENU_OPEN_KEY = "saju_quick_menu_open"
QUICK_MENU_NAV_EPOCH_KEY = "saju_nav_epoch"


def prepare_step_change_ui(*, dest: int | None = None) -> None:
    """STEP 전환 직전: 하단 「기능 바로가기」 접기 + (선택) 최상단 스크롤."""
    st.session_state.pop("_saju_scroll_armed_epoch", None)
    st.session_state.pop("_saju_scroll_widgets_fired", None)
    st.session_state.pop("_saju_scroll_phase_fired", None)
    st.session_state[QUICK_MENU_OPEN_KEY] = False
    st.session_state[QUICK_MENU_NAV_EPOCH_KEY] = int(
        st.session_state.get(QUICK_MENU_NAV_EPOCH_KEY, 0)
    ) + 1
    st.session_state.pop("_saju_nav_scroll_tail_epoch", None)
    st.session_state.pop("_saju_nav_scroll_followup_epoch", None)
    st.session_state.pop("_saju_router_mount_css_step", None)
    st.session_state.pop("_saju_nav_pending_flag_epoch", None)
    try:
        st.session_state["_saju_nav_from_step"] = int(st.session_state.get("step", 1))
    except (TypeError, ValueError):
        st.session_state["_saju_nav_from_step"] = 1

    preserve_scroll = bool(st.session_state.get("_saju_nav_preserve_scroll"))
    st.session_state.pop("_saju_scroll_phase_fired", None)
    st.session_state.pop("_saju_hero_pin_slots", None)
    st.session_state.pop("_saju_scroll_top_tag", None)
    st.session_state.pop("_saju_scrolled_nav_epoch", None)
    st.session_state["_saju_scroll_fired_slots"] = []
    for key in list(st.session_state.keys()):
        if isinstance(key, str) and key.startswith("_saju_scroll_engine_injected_"):
            st.session_state.pop(key, None)
    if preserve_scroll:
        st.session_state.pop("_saju_pending_scroll_top", None)
        st.session_state.pop("_force_scroll_to_top_after_rerun", None)
        st.session_state.pop("_saju_must_scroll_top", None)
    else:
        st.session_state["_saju_pending_scroll_top"] = True
        st.session_state["_force_scroll_to_top_after_rerun"] = True
        st.session_state["_saju_must_scroll_top"] = True
    st.session_state["_saju_nav_from_prepare"] = True
    if not preserve_scroll:
        try:
            from saju_app.ui.execution import arm_step_navigation_scroll

            arm_step_navigation_scroll(
                step=int(dest) if dest is not None else int(st.session_state.get("step", 1))
            )
        except Exception:
            pass
    legacy = "saju_bottom_quick_menu_expander"
    st.session_state.pop(legacy, None)
    for key in list(st.session_state.keys()):
        if not isinstance(key, str):
            continue
        if key.startswith("saju_bottom_quick_menu_expander"):
            st.session_state.pop(key, None)


def queue_step2_save_and_analyze() -> None:
    """STEP2 하단 「다음 →」 — 저장·검증 후 STEP3(사주분석)으로 이동."""
    from saju.ui.step_02 import try_step2_save_from_session

    if not try_step2_save_from_session():
        st.session_state["_step2_clear_nav_pending"] = True


def assign_step_and_rerun(
    dest: int,
    *,
    delay_ms: int = 150,
    strength: str = "strong",
) -> None:
    """``on_click`` 이 아닌 버튼/로직에서 STEP 이동 + 최상단 스크롤 예약 + rerun.

    예시::

        assign_step_and_rerun(3)
        # 내부: navigate_to_step → rerun_full_app → finalize_scroll_to_top_if_needed
    """
    d = max(STEP_NAV_MIN, min(STEP_NAV_MAX, int(dest)))
    try:
        cur = int(st.session_state.get("step", 1))
    except Exception:
        cur = 1
    if d == cur:
        st.session_state[QUICK_MENU_OPEN_KEY] = False
        return
    navigate_to_step(d)
    rerun_full_app()


def navigate_to_step(dest: int) -> None:
    """STEP 이동(``on_click`` 콜백용). Streamlit 이 이후 자동 rerun 하므로 ``rerun`` 은 호출하지 않습니다.

    최상단 스크롤·포커스는 rerun 다음 run 의 ``finalize_scroll_to_top_if_needed`` 에서
    1회만 실행됩니다.

    수동 rerun 이 필요하면::

        navigate_to_step(3)
        rerun_full_app()
    """
    d = max(STEP_NAV_MIN, min(STEP_NAV_MAX, int(dest)))
    st.session_state.pop("_saju_nav_preserve_scroll", None)
    try:
        cur = int(st.session_state.get("step", 1))
    except Exception:
        cur = 1
    if d == cur:
        st.session_state[QUICK_MENU_OPEN_KEY] = False
        return
    prepare_step_change_ui(dest=d)
    clear_goto_query_and_reset_nav_tracking()
    if d in _FEATURE_STEPS and 1 <= cur <= 10:
        st.session_state["_last_analysis_step"] = cur
    if d in _FEATURE_STEPS:
        st.session_state["_explicit_feature_step"] = d
    else:
        st.session_state.pop("_explicit_feature_step", None)
    if d in (11, 12):
        st.session_state["_navigated_to_chat_this_run"] = True
    if d == 2:
        st.session_state.pop("_step2_retain_form", None)
        st.session_state.pop("_step2_opp_unlocked", None)
        st.session_state.pop("_step2_opp_user_touched", None)
        if st.session_state.get("_return_step_after_input") is None:
            st.session_state["_step2_need_fresh_form"] = True
    st.session_state.step = int(d)
    if d in _STEPS_NEED_PROFILE_FOR_NAV and not analysis_flow_unlocked():
        st.session_state._return_step_after_input = int(d)
    elif d != 2:
        st.session_state.pop("_return_step_after_input", None)
    track_analysis_step_for_draft(st.session_state.step)


def _quick_menu_nav_epoch() -> int:
    try:
        return int(st.session_state.get(QUICK_MENU_NAV_EPOCH_KEY, 0))
    except Exception:
        return 0


def _toggle_quick_menu() -> None:
    st.session_state[QUICK_MENU_OPEN_KEY] = not bool(
        st.session_state.get(QUICK_MENU_OPEN_KEY, False)
    )


def render_step11_inline_step_nav() -> None:
    """STEP11 챗봇 본문 하단 — 상담 연결 아래 ``← 총평`` / ``관리자 이동 →``."""
    reset_id = int(st.session_state.get("reset_id", 0))
    # ``saju_bottom_prev_next_row`` 키 — 모바일 WebView 가로 2열 CSS 재사용
    with st.container(key="saju_bottom_prev_next_row"):
        try:
            nav_cols = st.columns([1, 1], gap="small")
        except TypeError:
            nav_cols = st.columns([1, 1])
        with nav_cols[0]:
            st.button(
                "← 총평",
                use_container_width=True,
                key=f"step11_inline_prev_{reset_id}",
                on_click=navigate_to_step,
                args=(10,),
            )
        with nav_cols[1]:
            if admin_panel_enabled():
                st.button(
                    "관리자 이동 →",
                    type="primary",
                    use_container_width=True,
                    key=f"step11_inline_next_{reset_id}",
                    on_click=navigate_to_step,
                    args=(12,),
                )
            else:
                st.empty()


def render_bottom_step_nav(*, current_step: int | None = None) -> None:
    """모바일 인앱 하단 네비: (STEP2~) ``← 이전`` / ``다음 →`` , 그 아래 접이식 ``st.expander`` 안에 12단계 그리드.

    - **STEP1(홈)**: 이전/다음 행 없음 — ``기능 바로가기`` expander 만 표시합니다.
    - **STEP2~10**: ``← 이전`` / ``다음 →`` 2열 · **STEP11**: 본문 inline(``render_step11_inline_step_nav``) · **STEP12**: 생략.

    하단 크롬에서는 ``st.divider``/``---`` 를 쓰지 않습니다(CSS 여백으로 본문과 구분). 인앱 WebView에서
    이중 실선·이전/다음 행이 두 번 보이는 현상을 줄입니다.
    """
    if current_step is None:
        step = int(st.session_state.get("step", 1))
    else:
        step = int(current_step)
    step = max(STEP_NAV_MIN, min(STEP_NAV_MAX, step))
    reset_id = int(st.session_state.get("reset_id", 0))

    # STEP12(관리자): 상단 UI로 이동 — 하단 이전/다음 생략
    if step > STEP_NAV_MIN and step not in (11, 12):
        # 모바일 인앱 WebView: 가운데 빈 열(1·2·1) 대신 2열 동일 비율이 세로 스택을 덜 유발합니다.
        with st.container(key="saju_bottom_prev_next_row"):
            try:
                nav_cols = st.columns([1, 1], gap="small")
            except TypeError:
                nav_cols = st.columns([1, 1])

            with nav_cols[0]:
                st.button(
                    "← 이전",
                    use_container_width=True,
                    key=f"saju_bottom_prev_btn_{reset_id}",
                    on_click=navigate_to_step,
                    args=(max(STEP_NAV_MIN, step - 1),),
                )
            with nav_cols[1]:
                if step < STEP_NAV_MAX:
                    if step == 2:
                        st.button(
                            "다음 →",
                            type="primary",
                            use_container_width=True,
                            key=f"saju_bottom_next_btn_{reset_id}",
                            on_click=queue_step2_save_and_analyze,
                        )
                    else:
                        st.button(
                            "다음 →",
                            type="primary",
                            use_container_width=True,
                            key=f"saju_bottom_next_btn_{reset_id}",
                            on_click=navigate_to_step,
                            args=(min(STEP_NAV_MAX, step + 1),),
                        )
                else:
                    st.empty()

    nav_items = (
        ("🏠", "홈", 1),
        ("📋", "정보입력", 2),
        ("📊", "사주분석", 3),
        ("❤️", "궁합", 4),
        ("🧿", "살풀이", 5),
        ("☀️", "오늘의 운세", 6),
        ("☯️", "주역점", 7),
        ("🃏", "타로", 8),
        ("📈", "대운", 9),
        ("📋", "총평", 10),
        ("💬", "AI챗봇", 11),
    )
    if admin_panel_enabled():
        nav_items = (*nav_items, ("🛠", "관리자", 12))

    qm_epoch = _quick_menu_nav_epoch()
    quick_open = bool(st.session_state.get(QUICK_MENU_OPEN_KEY, False))
    toggle_label = (
        "📂 기능 바로가기 · 접기"
        if quick_open
        else "📂 기능 바로가기 · 펼치기"
    )
    with st.container(key="saju_bottom_quick_menu_panel"):
        st.button(
            toggle_label,
            use_container_width=True,
            key=f"saju_quick_menu_toggle_{qm_epoch}",
            on_click=_toggle_quick_menu,
        )
        if quick_open:
            if not analysis_flow_unlocked():
                st.caption(
                    "본인 사주가 아직 저장되지 않았습니다. **정보입력(STEP2)**에서 저장하면 "
                    "나머지 단계로 이동할 수 있습니다."
                )

            with st.container(key="saju_bottom_quick_grid_2col"):
                cols = _columns_compat(2)
                for idx, (emoji, label, target_step) in enumerate(nav_items):
                    col_idx = idx % 2
                    ts = int(target_step)
                    with cols[col_idx]:
                        is_current = step == ts
                        btn_label = f"{emoji} {label}"
                        tip = str(STEP_DOCK_HELP.get(ts, STEP_NAMES.get(ts, label)))
                        st.button(
                            btn_label,
                            use_container_width=True,
                            key=f"saju_bottom_nav_{ts}_{qm_epoch}",
                            type="primary" if is_current else "secondary",
                            help=tip,
                            on_click=navigate_to_step,
                            args=(ts,),
                        )


def _render_step_dock_streamlit() -> None:
    """STEP 6+5 바로가기 — ``st.button`` 만 사용. ``key`` 는 ``saju_dock_nav_<STEP>`` 고정."""
    items = _visible_step_dock_items()
    r1 = items[:6]
    r2 = items[6:]
    cols1 = _columns_compat(6)
    for col, (emo, cap, dest) in zip(cols1, r1, strict=True):
        with col:
            label = f"{emo} {cap}"
            st.button(
                label,
                key=f"saju_dock_nav_{int(dest)}",
                help=str(STEP_DOCK_HELP.get(int(dest), "")),
                use_container_width=True,
                on_click=navigate_to_step,
                args=(int(dest),),
            )
    cols2 = _columns_compat(5)
    for col, (emo, cap, dest) in zip(cols2, r2):
        with col:
            label = f"{emo} {cap}"
            st.button(
                label,
                key=f"saju_dock_nav_{int(dest)}",
                help=str(STEP_DOCK_HELP.get(int(dest), "")),
                use_container_width=True,
                on_click=navigate_to_step,
                args=(int(dest),),
            )


def _render_feature_menu_expander_content() -> None:
    """``기능 메뉴`` 펼침 영역 — 스텝 바로가기만(이전·다음은 expander 밖)."""
    with st.container(key="saju_feature_menu_accordion_inner"):
        if not analysis_flow_unlocked():
            st.info(
                "아직 **본인 사주 입력이 완료되지 않았습니다.** "
                "「명백·사주·궁합」 등은 정보 입력(STEP2)에서 저장한 뒤 아래 버튼이 활성화됩니다."
            )
        st.caption("스텝 바로가기")
        if analysis_flow_unlocked():
            _render_step_dock_streamlit()
        else:
            st.markdown(_step_dock_html_full(unlocked=False), unsafe_allow_html=True)


def render_global_bottom_chrome(*, current_step: int) -> None:
    """하단 크롬: 본문(STEP) 아래 → **이전·다음** + **기능 바로가기**(expander).

    STEP1(홈)에서는 이전/다음 없이 expander 만 표시합니다.
    STEP2~ 에서는 본문과의 구분은 CSS 여백으로만 두고 ``render_bottom_step_nav`` 를 호출합니다.
    (``st.divider``/``---`` 를 겹쳐 쓰면 인앱 WebView에서 실선·이전/다음이 이중으로 보일 수 있어 제거했습니다.)

    STEP 이동은 ``navigate_to_step``(``on_click``) / ``prepare_step_change_ui`` 를 사용합니다.
    """
    s = max(STEP_NAV_MIN, min(STEP_NAV_MAX, int(current_step)))
    with st.container(key="saju_global_bottom_chrome"):
        render_bottom_step_nav(current_step=s)


# -------------------- storage helpers --------------------
def _persist_shared_chat_bus(room_key: str, messages: list, label: dict | None = None) -> None:
    """공유 채팅 방을 저장소에 반영합니다(`saju_storage.upsert_shared_chat_room`)."""
    from saju_app.ui.chat_messages import dedupe_chat_messages

    messages = dedupe_chat_messages(list(messages or []))
    # 저장소가 순간적으로 실패해도 사용자가 보낸 채팅은 현재 화면에 먼저 남깁니다.
    try:
        st.session_state.shared_chat = list(messages or [])
    except Exception:
        pass
    try:
        saju_storage.upsert_shared_chat_room(str(room_key), list(messages or []), label)
    except Exception as e:
        try:
            st.session_state["_shared_chat_persist_error"] = str(e)[:800]
        except Exception:
            pass
        return
    try:
        st.session_state.pop("_shared_chat_persist_error", None)
    except Exception:
        pass
    rk = str(room_key or "").strip()
    if rk:
        try:
            sync_shared_chat_room_into_session(rk)
        except Exception:
            pass


def sync_shared_chat_room_into_session(room_key: str) -> None:
    """저장소(SAJU_STORAGE)의 채팅을 `st.session_state.shared_chat`에 반영.

    저장소를 기준으로 동기화합니다. 원격 메시지가 짧아진 경우(삭제·롤백 등)에도 세션이 남지 않도록
    길이 비교로 스킵하지 않고, 역할·본문·수동 여부 시그니처가 다르면 항상 원본 목록으로 덮어씁니다.
    """
    rk = str(room_key or "").strip()
    if not rk:
        return
    try:
        remote_raw, _ = saju_storage.get_shared_chat_room(rk)
    except Exception:
        return
    from saju_app.ui.chat_messages import dedupe_chat_messages

    remote = dedupe_chat_messages(list(remote_raw or []))
    local = dedupe_chat_messages(list(st.session_state.get("shared_chat") or []))
    if not remote and local:
        # 저장소 장애 직후에는 원격이 비어 보여도 현재 화면의 대화를 보존합니다.
        return

    def _sig(msgs: list) -> tuple[tuple[str, str, bool], ...]:
        return tuple(
            (str(m.get("role")), str(m.get("msg")), bool(m.get("is_manual")))
            for m in (msgs or [])
        )

    if _sig(remote) == _sig(local):
        return
    st.session_state.shared_chat = remote


# -------------------- engine/core caching --------------------
def _birth_year_from_record(u_data) -> int:
    if isinstance(u_data, (list, tuple)) and u_data:
        try:
            return int(u_data[0])
        except Exception:
            return 2000
    return 2000


def _session_birth_year() -> int:
    return _birth_year_from_record(st.session_state.get("u_data"))


def _birth_records_equal(a: Any, b: Any) -> bool:
    """u_data / p_data 등 생년월일시 원본 동등(참조 또는 앞 6필드)."""
    if a is None or b is None:
        return False
    if a is b:
        return True
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)) and len(a) >= 6 and len(b) >= 6:
        return tuple(a[:6]) == tuple(b[:6])
    return False


def _infer_engine_cache_role(birth_record: Any, *, cache_role: str | None) -> str:
    """세션 엔진 캐시 슬롯: 본인(`user`)과 상대(`partner`)가 서로 덮어쓰지 않도록."""
    if cache_role in ("user", "partner"):
        return str(cache_role)
    if birth_record is None:
        return "user"
    p_data = st.session_state.get("p_data")
    if _birth_records_equal(birth_record, p_data):
        return "partner"
    return "user"


def _engine_cache_keys(role: str) -> tuple[str, str]:
    r = str(role).strip() or "user"
    if r == "user":
        return "saju_engine", "saju_engine_sig"
    if r == "partner":
        return "saju_engine__partner", "saju_engine_sig__partner"
    safe = "".join(c if c.isalnum() or c in "_-" else "_" for c in r)[:48] or "x"
    return f"saju_engine__{safe}", f"saju_engine_sig__{safe}"


def _solar_tuple_for_strength(birth_record: Any) -> tuple[int, int, int] | None:
    if not (isinstance(birth_record, (list, tuple)) and len(birth_record) >= 6):
        return None
    try:
        return C.solar_ymd_for_birth(
            int(birth_record[0]),
            int(birth_record[1]),
            int(birth_record[2]),
            bool(birth_record[4]),
            bool(birth_record[5]),
        )
    except Exception:
        return None


def _engine_cache_signature_json(
    *,
    role: str,
    gapja_t: tuple[Any, ...],
    by: int,
    gen: str,
    month_method: str,
    dae_start: int,
    dae_forward: bool,
    solar: tuple[int, int, int] | None,
) -> str:
    """tuple 대신 JSON 직렬화 문자열로 캐시 키를 만듭니다.

    mutable 객체가 시그니처에 섞이거나 참조 동등에 의존하는 문제를 피합니다.
    """
    gapja_list = [str(p) for p in gapja_t]
    payload: dict[str, Any] = {
        "birth_year": int(by),
        "dae_forward": bool(dae_forward),
        "dae_start": int(dae_start),
        "gapja": gapja_list,
        "gender": str(gen),
        "month_method": str(month_method),
        "role": str(role),
        "solar": [int(solar[0]), int(solar[1]), int(solar[2])] if solar is not None else None,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def ensure_engine_and_core(
    u_gapja: list[str],
    *,
    birth_year: int | None = None,
    birth_record=None,
    gender: str | None = None,
    cache_role: str | None = None,
) -> tuple[dict, dict]:
    """간지·출생기록·옵션 기준으로 `SajuEngine`을 만들고 세션에 캐시합니다.

    - 시그니처가 같으면 **재빌드하지 않고** 캐시를 반환합니다.
    - 상대(p_data)용 호출은 ``saju_engine__partner`` 슬롯에만 저장해 본인 ``saju_engine``과 충돌하지 않습니다.
    """
    by = _session_birth_year() if birth_year is None else int(birth_year)
    gapja_t = tuple(u_gapja) if u_gapja else ()

    rec = st.session_state.get("u_data") if birth_record is None else birth_record
    gen = st.session_state.get("u_gender", "남자") if gender is None else str(gender)
    role = _infer_engine_cache_role(rec, cache_role=cache_role)

    opt = st.session_state.get("saju_options", {}) or {}
    if not isinstance(opt, dict):
        opt = {}
    month_method = str(opt.get("month_method", "lichun_lunar"))

    dae = C.compute_daewoon_schedule(u_gapja, rec, str(gen), by, n_terms=10)
    solar = _solar_tuple_for_strength(rec)

    sig_json = _engine_cache_signature_json(
        role=role,
        gapja_t=gapja_t,
        by=by,
        gen=str(gen),
        month_method=month_method,
        dae_start=int(dae.get("start_age", 0)),
        dae_forward=bool(dae.get("forward", True)),
        solar=solar,
    )

    eng_key, sig_key = _engine_cache_keys(role)

    cached = st.session_state.get(eng_key)
    if st.session_state.get(sig_key) == sig_json and _engine_dict_coherent(cached):
        eng = cached
    else:
        with st.spinner("사주 엔진을 준비하는 중…"):
            eng = SajuEngine(
                birth_year=by,
                now=now_kst,
                birth_solar=solar,
                daewoon_first_start_age=int(dae.get("start_age", 0)),
                daewoon_forward=bool(dae.get("forward", True)),
            ).build(u_gapja, gender=str(gen))
        st.session_state[eng_key] = eng
        st.session_state[sig_key] = sig_json

    zi_boundary = str(opt.get("zi_boundary", "23:30") or "23:30")
    try:
        from saju_app.ui.saju_interpretation_core import build_step3_core

        core = build_step3_core(
            list(gapja_t),
            eng,
            gender=str(gen or ""),
            birth_record=rec if isinstance(rec, (list, tuple)) else None,
            birth_year=int(by),
            zi_boundary=zi_boundary,
        )
    except Exception:
        try:
            from saju_app.ui.ilju_data import build_ilju_db

            ilju_key = str(gapja_t[2] if len(gapja_t) > 2 else "").strip()
            entry = build_ilju_db().get(ilju_key) if ilju_key else None
            if isinstance(entry, dict):
                core = {
                    "ok": True,
                    "ilju": ilju_key,
                    "personality": str(entry.get("personality") or ""),
                    "career": str(entry.get("career") or ""),
                    "relationship": str(entry.get("relationship") or ""),
                    "interpretation_200": "",
                }
            else:
                core = {"ok": True}
        except Exception:
            core = {"ok": True}
    return eng, core


def _gapja_pillars_valid(g: object, *, min_pillars: int) -> bool:
    """u_gapja가 리스트/튜플이고, 앞쪽 기둥들이 유효 간지(갑자 형)인지 검사."""
    from saju.core.gapja_utils import is_valid_pillar

    mp = max(1, min(4, int(min_pillars)))
    if not isinstance(g, (list, tuple)) or len(g) < mp:
        return False
    for i in range(mp):
        if not is_valid_pillar(g[i]):
            return False
    return True


def _engine_dict_coherent(eng: object) -> bool:
    """세션에 남은 saju_engine이 dict이고 최소 필드가 채워져 있는지."""
    if not isinstance(eng, dict) or not eng:
        return False
    if not str(eng.get("day_stem") or "").strip():
        return False
    el = eng.get("elements")
    if not isinstance(el, dict) or not el:
        return False
    return True


def _require_u_gapja_or_halt(
    *,
    min_pillars: int = 3,
    message: str = "사주 정보가 없습니다.",
    show_home_button: bool = True,
    show_input_button: bool = True,
    home_step: int = 1,
    input_step: int = 2,
    button_label: str = "← 처음으로",
    input_button_label: str = "← 정보 입력으로",
    resync_first: bool = True,
) -> list[str]:
    mp = max(1, min(4, int(min_pillars)))
    hs = max(STEP_NAV_MIN, min(STEP_NAV_MAX, int(home_step)))
    inp = max(STEP_NAV_MIN, min(STEP_NAV_MAX, int(input_step)))

    if resync_first:
        _resync_user_gapja_from_u_data()

    g = st.session_state.get("u_gapja")
    if _gapja_pillars_valid(g, min_pillars=mp):
        return list(g)

    st.error(message)
    if show_home_button and show_input_button:
        c1, c2 = st.columns(2)
        with c1:
            if st.button(button_label, use_container_width=True):
                prepare_step_change_ui()
                st.session_state.step = hs
                rerun_full_app()
        with c2:
            if st.button(input_button_label, use_container_width=True):
                prepare_step_change_ui()
                st.session_state.step = inp
                rerun_full_app()
    elif show_home_button:
        if st.button(button_label, use_container_width=True):
            prepare_step_change_ui()
            st.session_state.step = hs
            rerun_full_app()
    elif show_input_button:
        if st.button(input_button_label, use_container_width=True):
            prepare_step_change_ui()
            st.session_state.step = inp
            rerun_full_app()
    st.stop()
    return []


def _require_saju_engine_or_build() -> dict:
    _resync_user_gapja_from_u_data()
    eng = st.session_state.get("saju_engine")
    if _engine_dict_coherent(eng):
        return eng
    g = st.session_state.get("u_gapja")
    if _gapja_pillars_valid(g, min_pillars=3):
        built, _ = ensure_engine_and_core(list(g))
        st.session_state.saju_engine = built
        return built
    st.error("사주 데이터가 유실되었습니다. 처음부터 다시 진행해주세요.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← 처음으로", use_container_width=True):
            prepare_step_change_ui()
            st.session_state.step = 1
            rerun_full_app()
    with c2:
        if st.button("← 정보 입력으로", use_container_width=True):
            prepare_step_change_ui()
            st.session_state.step = 2
            rerun_full_app()
    st.stop()
    return {}


# -------------------- STEP2 submit handler --------------------
def _step2_fail(msg: str) -> bool:
    st.session_state["_step2_apply_error"] = str(msg)
    st.session_state["_step2_top_alert"] = str(msg)
    return False


def apply_step2_next_from_payload() -> bool:
    payload = st.session_state.get("_step2_payload") or {}
    try:
        u_name = str(payload.get("u_name", "")).strip()
        if not u_name:
            return _step2_fail("본인 성함을 입력해 주세요.")
        if not bool(payload.get("agree")):
            return _step2_fail("개인정보 수집·이용 동의가 필요합니다.")

        u_y = int(payload.get("u_y", 1995))
        u_m = int(payload.get("u_m", 1))
        u_d = int(payload.get("u_d", 1))
        if not (1900 <= u_y <= 2100):
            return _step2_fail("년도는 1900~2100 범위로 입력해 주세요.")
        if not (1 <= u_m <= 12):
            return _step2_fail("월은 1~12 범위로 입력해 주세요.")
        last_d = calendar.monthrange(u_y, u_m)[1]
        if not (1 <= u_d <= last_d):
            return _step2_fail(f"일은 1~{last_d} 범위로 입력해 주세요.")

        # 상대방 이름은 STEP2 위젯 입력값만 사용(세션 p_name 폴백 금지 — 타 사용자 잔존 방지).
        opponent_name = str(payload.get("opponent_name", "")).strip()
        opponent_year = int(payload.get("opponent_year", 1995))
        opponent_month = int(payload.get("opponent_month", 1))
        opponent_day = int(payload.get("opponent_day", 1))
        if opponent_name:
            if not (1900 <= opponent_year <= 2100):
                return _step2_fail("상대방 년도는 1900~2100 범위로 입력해 주세요.")
            if not (1 <= opponent_month <= 12):
                return _step2_fail("상대방 월은 1~12 범위로 입력해 주세요.")
            last_d_opp = calendar.monthrange(opponent_year, opponent_month)[1]
            if not (1 <= opponent_day <= last_d_opp):
                return _step2_fail(f"상대방 일은 1~{last_d_opp} 범위로 입력해 주세요.")

        u_t_str = str(payload.get("u_t_str", "모름"))
        _u_lun = str(payload.get("u_lunar", "양력")) == "음력"
        _u_lp = str(payload.get("u_leap", "평달")) == "윤달"
        u_gapja = _gapja_from_birth(u_y, u_m, u_d, u_t_str, is_lunar=_u_lun, is_leap=_u_lp)

        p_gapja = None
        p_name = opponent_name
        p_t_str = "모름"
        _p_lun = False
        _p_lp = False
        if p_name:
            p_t_str = str(payload.get("opponent_time", "모름"))
            _p_lun = str(payload.get("opponent_lunar", "양력")) == "음력"
            _p_lp = str(payload.get("opponent_leap", "평달")) == "윤달"
            p_gapja = _gapja_from_birth(
                opponent_year,
                opponent_month,
                opponent_day,
                p_t_str,
                is_lunar=_p_lun,
                is_leap=_p_lp,
            )

        st.session_state.u_name = u_name
        st.session_state.user_name_snapshot = str(u_name).strip()
        st.session_state.u_gender = payload.get("u_gender", "남자")
        st.session_state.u_data = (u_y, u_m, u_d, u_t_str, _u_lun, _u_lp)
        st.session_state.u_gapja = u_gapja
        st.session_state.contact_value = str(payload.get("contact_num") or "").strip() or "미등록"

        if p_name and p_gapja and len(p_gapja) >= 3:
            st.session_state.p_gender = payload.get("p_gender", "여자")
            p_birth = (
                int(opponent_year),
                int(opponent_month),
                int(opponent_day),
                str(p_t_str),
                bool(_p_lun),
                bool(_p_lp),
            )
            fresh_p = _apply_partner_birth_to_session(p_birth, p_name=p_name)
            if fresh_p:
                store_step4_partner_bundle(
                    p_name=p_name,
                    birth=p_birth,
                    p_gapja=fresh_p,
                )
                mark_partner_registered(active=True)
            else:
                clear_partner_analysis_state()
            st.session_state.pop("_step4_pair_sig", None)
            st.session_state.pop("saju_engine__partner", None)
            st.session_state.pop("saju_engine_sig__partner", None)
        else:
            clear_partner_analysis_state()

        # 개인정보 입력값은 새로고침/재접속 시 이전 사용자에게 노출되지 않도록 디스크에 저장하지 않습니다.

        birth_u = _birth_payload_with_time_meta(
            {
                "year": int(u_y),
                "month": int(u_m),
                "day": int(u_d),
                "time_str": str(u_t_str),
                "lunar": bool(_u_lun),
                "leap_month": bool(_u_lp),
            }
        )
        gj_u = [str(x) for x in (u_gapja or [])]

        rp = saju_storage.normalize_revisit_pin(str(payload.get("revisit_pin") or ""))
        rp2 = saju_storage.normalize_revisit_pin(
            str(payload.get("revisit_pin_confirm") or "")
        )
        pin_both = bool(rp) and bool(rp2)
        pin_partial = bool(rp) != bool(rp2)

        u_fp: str | None = None
        if len(gj_u) >= 3:
            try:
                u_fp = saju_storage.upsert_user_profile(
                    display_name=u_name,
                    birth=birth_u,
                    gapja=gj_u,
                )
            except Exception as e:
                report_exception_to_streamlit(e, prefix="사주 프로필 저장")
        else:
            return _step2_fail(
                "사주 간지를 만들지 못했습니다. 생년월일·시간·음력/윤달을 확인한 뒤 다시 저장해 주세요."
            )

        if pin_partial:
            st.warning(
                "재방문 비밀번호는 「비밀번호」와 「확인」을 모두 입력하거나, "
                "둘 다 비워 두세요. 사주 분석은 계속 진행합니다."
            )
        elif pin_both:
            if rp != rp2:
                st.warning(
                    "재방문 비밀번호 확인이 일치하지 않습니다. "
                    "사주 분석은 시작하며, 비밀번호는 설정되지 않습니다."
                )
                st.session_state.revisit_pin_ready = False
            else:
                try:
                    u_fp, ok_pin, msg_pin = saju_storage.save_user_profile_with_revisit_pin(
                        display_name=u_name,
                        birth=birth_u,
                        gapja=gj_u,
                        pin=rp,
                    )
                except Exception as e:
                    u_fp, ok_pin, msg_pin = (
                        u_fp,
                        False,
                        "재방문 비밀번호 저장 중 오류가 발생했습니다.",
                    )
                    report_exception_to_streamlit(e, prefix="재방문 비밀번호")
                if ok_pin:
                    st.session_state.revisit_pin_ready = True
                    st.success(msg_pin)
                else:
                    st.session_state.revisit_pin_ready = False
                    st.warning(f"{msg_pin} (사주 분석은 계속 진행합니다.)")

        if p_name and p_gapja and len(list(p_gapja)) >= 3:
            try:
                birth_p = _birth_payload_with_time_meta(
                    {
                        "year": int(opponent_year),
                        "month": int(opponent_month),
                        "day": int(opponent_day),
                        "time_str": str(p_t_str),
                        "lunar": bool(_p_lun),
                        "leap_month": bool(_p_lp),
                    }
                )
                gj_p = [str(x) for x in list(p_gapja)]
                saju_storage.upsert_user_profile(
                    display_name=str(p_name).strip(),
                    birth=birth_p,
                    gapja=gj_p,
                )
            except Exception as e:
                report_exception_to_streamlit(e, prefix="상대방 프로필 저장")

        ensure_engine_and_core(u_gapja, birth_year=int(u_y), birth_record=st.session_state.u_data, gender=st.session_state.u_gender)

        st.session_state.reset_id = int(st.session_state.get("reset_id", 0)) + 1
        st.session_state.pop("_return_step_after_input", None)
        st.session_state.pop("_step2_payload", None)
        try:
            from saju_app.persistence.prefill import ensure_visit_id

            visit_id = ensure_visit_id()
            st.session_state["_personal_input_visit_id"] = visit_id
        except Exception:
            visit_id = str(st.session_state.get("visit_id") or "").strip()
            st.session_state["_personal_input_visit_id"] = visit_id
        if bool(st.session_state.get("_partner_registered")):
            st.session_state["_partner_registered_visit"] = str(
                st.session_state.get("_personal_input_visit_id") or visit_id or ""
            ).strip()
        st.session_state["_personal_input_saved"] = True
        # 저장 직후 STEP3(사주분석)으로 이동 — prepare_step_change_ui 가 스크롤 플래그를 설정합니다.
        navigate_to_step(3)
        return True
    except Exception as e:
        report_exception_to_streamlit(e, prefix="처리 중 오류")
        return False


def apply_user_profile_record_to_session(
    record: dict[str, Any],
    *,
    dest_step: int = 3,
) -> bool:
    """``user_profiles`` 한 건을 세션에 반영하고 분석 단계로 이동합니다."""
    try:
        name = str(record.get("display_name") or "").strip()
        birth = record.get("birth")
        gapja = record.get("gapja")
        if not name or not isinstance(birth, dict) or not isinstance(gapja, list):
            return False
        if len(gapja) < 3:
            return False
        fp = str(record.get("fingerprint") or "").strip()
        y = int(birth.get("year", 0) or 0)
        m = int(birth.get("month", 0) or 0)
        d = int(birth.get("day", 0) or 0)
        if not (1900 <= y <= 2100 and 1 <= m <= 12 and 1 <= d <= 31):
            return False
        t_str = str(birth.get("time_str") or "모름")
        lunar = bool(birth.get("lunar", False))
        leap = bool(birth.get("leap_month", False))
        st.session_state.u_name = name
        st.session_state.user_name_snapshot = str(name).strip()
        st.session_state.u_data = (y, m, d, t_str, lunar, leap)
        st.session_state.u_gapja = [str(x) for x in gapja if x is not None]
        if fp:
            try:
                saju_storage.touch_user_profile(fp)
            except Exception:
                pass
        if not str(st.session_state.get("u_gender") or "").strip():
            st.session_state.u_gender = "남자"
        clear_partner_analysis_state()
        st.session_state["_personal_input_saved"] = True
        st.session_state["_personal_input_visit_id"] = str(
            st.session_state.get("visit_id") or ""
        ).strip()
        st.session_state.reset_id = int(st.session_state.get("reset_id", 0)) + 1
        clear_goto_query_and_reset_nav_tracking()
        assign_step_and_rerun(int(dest_step))
        return True
    except Exception as e:
        report_exception_to_streamlit(e, prefix="프로필 불러오기")
        return False


def apply_user_profile_by_fingerprint(fingerprint: str, *, dest_step: int = 3) -> bool:
    """fingerprint로 프로필을 읽어 세션에 적용합니다."""
    rec = saju_storage.get_user_profile(str(fingerprint or "").strip())
    if not rec:
        return False
    return apply_user_profile_record_to_session(rec, dest_step=dest_step)


# -------------------- session resync helpers --------------------
def _resync_user_gapja_from_u_data() -> None:
    """u_data(생년월일·시·음양) 원본으로 u_gapja를 세션에 재동기화."""
    u_data = st.session_state.get("u_data")
    if not (u_data and isinstance(u_data, (list, tuple)) and len(u_data) >= 6):
        return
    try:
        y, m, d, t_str, is_lunar, is_leap = u_data[:6]
        fresh_gapja = _gapja_from_birth(
            int(y), int(m), int(d), str(t_str), is_lunar=bool(is_lunar), is_leap=bool(is_leap)
        )
        if fresh_gapja and len(fresh_gapja) >= 3:
            st.session_state.u_gapja = list(fresh_gapja)
    except Exception:
        return


def _partner_birth_from_widgets() -> tuple[int, int, int, str, bool, bool] | None:
    """STEP2 위젯 세션(p_y 등)에서 상대 생년월일·시·음양."""
    if not _partner_name_from_session():
        return None
    try:
        py = int(st.session_state.get("p_y", 0))
        pm = int(st.session_state.get("p_m", 0))
        pd = int(st.session_state.get("p_d", 0))
    except (TypeError, ValueError):
        return None
    if not (1900 <= py <= 2100 and 1 <= pm <= 12):
        return None
    last_d = calendar.monthrange(py, pm)[1]
    if not (1 <= pd <= last_d):
        return None
    pt_str = str(st.session_state.get("p_time") or "모름")
    if pt_str not in STEP2_TIME_OPTIONS:
        pt_str = "모름"
    pl = str(st.session_state.get("p_lunar") or "양력")
    p_is_lunar = pl == "음력"
    p_is_leap = (
        str(st.session_state.get("p_leap") or "평달") == "윤달" if p_is_lunar else False
    )
    return py, pm, pd, pt_str, p_is_lunar, p_is_leap


def _partner_birth_from_p_data() -> tuple[int, int, int, str, bool, bool] | None:
    if not partner_is_registered():
        return None
    p_data = st.session_state.get("p_data")
    if not (p_data and isinstance(p_data, (list, tuple)) and len(p_data) >= 6):
        return None
    try:
        py, pm, pd, pt_str, p_is_lunar, p_is_leap = p_data[:6]
        return (
            int(py),
            int(pm),
            int(pd),
            str(pt_str),
            bool(p_is_lunar),
            bool(p_is_leap),
        )
    except (TypeError, ValueError):
        return None


def _partner_birth_tuple_from_session() -> tuple[int, int, int, str, bool, bool] | None:
    """상대 생년월일·시·음양 — STEP2 저장(p_data) 우선, 수정 모드에서만 위젯 우선."""
    saved = _partner_birth_from_p_data()
    widgets = _partner_birth_from_widgets()
    if saved and widgets:
        w_key = (widgets[0], widgets[1], widgets[2], widgets[3], widgets[4], widgets[5])
        s_key = (saved[0], saved[1], saved[2], str(saved[3]), bool(saved[4]), bool(saved[5]))
        if w_key != s_key and step2_retain_form_allowed():
            return widgets
        return saved
    if saved:
        return saved
    if widgets:
        return widgets
    return None


def _gapja_tuple_key(gapja: object, *, max_pillars: int = 4) -> tuple[str, ...]:
    if not gapja or not isinstance(gapja, (list, tuple)):
        return ()
    return tuple(str(x) for x in gapja[:max_pillars])


def _apply_partner_birth_to_session(
    birth: tuple[int, int, int, str, bool, bool],
    *,
    p_name: str | None = None,
) -> list[str] | None:
    """생년월일·시·음양 → p_data·p_gapja·STEP2 위젯 키를 한꺼번에 맞춥니다."""
    py, pm, pd, pt_str, p_is_lunar, p_is_leap = birth
    try:
        fresh = _gapja_from_birth(
            int(py),
            int(pm),
            int(pd),
            str(pt_str),
            is_lunar=bool(p_is_lunar),
            is_leap=bool(p_is_leap),
        )
    except Exception:
        return None
    if not _gapja_pillars_valid(fresh, min_pillars=3):
        return None
    st.session_state.p_data = (
        int(py),
        int(pm),
        int(pd),
        str(pt_str),
        bool(p_is_lunar),
        bool(p_is_leap),
    )
    st.session_state.p_gapja = list(fresh)
    if p_name:
        pn = str(p_name).strip()
        if pn:
            st.session_state.p_name = pn
            st.session_state.partner_name_snapshot = pn
    return list(fresh)


def store_step4_partner_bundle(
    *,
    p_name: str,
    birth: tuple[int, int, int, str, bool, bool],
    p_gapja: list[str],
) -> None:
    """STEP2 저장 직후: STEP4가 반드시 이 상대 사주만 쓰도록 번들을 고정합니다."""
    pn = str(p_name or "").strip()
    gj = [str(x) for x in (p_gapja or []) if x is not None]
    if not pn or len(gj) < 3:
        st.session_state.pop("_step4_partner_bundle", None)
        return
    st.session_state["_step4_partner_bundle"] = {
        "name": pn,
        "birth": tuple(birth),
        "gapja": gj,
    }


def _partner_birth_for_step4() -> tuple[int, int, int, str, bool, bool] | None:
    """STEP4 전용: p_data(최신 저장) → 번들(이름 일치) → 위젯 순."""
    if not partner_is_registered():
        return None
    pn = _partner_name_from_session()
    if not pn:
        return None
    saved = _partner_birth_from_p_data()
    if saved:
        return saved
    bundle = st.session_state.get("_step4_partner_bundle")
    if isinstance(bundle, dict):
        b_name = str(bundle.get("name") or "").strip()
        raw_birth = bundle.get("birth")
        if b_name == pn and isinstance(raw_birth, (list, tuple)) and len(raw_birth) >= 6:
            try:
                py, pm, pd, pt_str, p_is_lunar, p_is_leap = raw_birth[:6]
                return (
                    int(py),
                    int(pm),
                    int(pd),
                    str(pt_str),
                    bool(p_is_lunar),
                    bool(p_is_leap),
                )
            except (TypeError, ValueError):
                pass
    return _partner_birth_from_widgets()


def partner_gapja_same_as_user() -> bool:
    """본인·상대 네 기둥이 동일한지(잘못된 복사 여부)."""
    u_key = _gapja_tuple_key(st.session_state.get("u_gapja"))
    p_key = _gapja_tuple_key(st.session_state.get("p_gapja"))
    return bool(u_key) and u_key == p_key


def _invalidate_step4_partner_engine(u_gapja: object, p_gapja: object, p_name: str) -> None:
    u_key = _gapja_tuple_key(u_gapja)
    p_key = _gapja_tuple_key(p_gapja)
    sig = f"{u_key}|{p_key}|{str(p_name or '').strip()}"
    if st.session_state.get("_step4_pair_sig") != sig:
        st.session_state.pop("saju_engine__partner", None)
        st.session_state.pop("saju_engine_sig__partner", None)
        st.session_state["_step4_pair_sig"] = sig


def sync_partner_gapja_for_match_analysis() -> bool:
    """STEP4: 저장된 상대 생년월일로 p_gapja를 재계산하고 엔진 캐시를 갱신합니다."""
    from saju.core.gapja_utils import day_pillar_from_gapja, is_valid_pillar

    if not partner_is_registered():
        clear_partner_analysis_state()
        return False
    pn = _partner_name_from_session()
    if not pn:
        clear_partner_analysis_state()
        return False
    birth = _partner_birth_for_step4()
    if not birth:
        ok = ensure_partner_session_from_state()
        if ok and day_pillar_from_gapja(st.session_state.get("p_gapja")):
            return True
        return ok
    fresh = _apply_partner_birth_to_session(birth, p_name=pn)
    if not fresh or not is_valid_pillar(fresh[2] if len(fresh) > 2 else None):
        bundle = st.session_state.get("_step4_partner_bundle")
        if isinstance(bundle, dict):
            b_name = str(bundle.get("name") or "").strip()
            gj = bundle.get("gapja")
            if (
                b_name == pn
                and isinstance(gj, (list, tuple))
                and _gapja_pillars_valid(gj, min_pillars=3)
                and is_valid_pillar(gj[2])
            ):
                st.session_state.p_gapja = [str(x) for x in gj]
                fresh = list(st.session_state.p_gapja)
            else:
                fresh = None
        if not fresh:
            return ensure_partner_session_from_state()
    store_step4_partner_bundle(p_name=pn, birth=birth, p_gapja=list(fresh))
    _invalidate_step4_partner_engine(st.session_state.get("u_gapja"), fresh, pn)
    return True


def _resync_partner_gapja_from_p_data() -> None:
    """상대 생년월일·시·음양으로 p_gapja·p_data·위젯 키를 재동기화."""
    if not partner_is_registered():
        return
    birth = _partner_birth_tuple_from_session()
    if not birth:
        return
    _apply_partner_birth_to_session(birth, p_name=_partner_name_from_session() or None)


def _partner_name_from_session() -> str:
    return str(
        st.session_state.get("partner_name_snapshot")
        or st.session_state.get("p_name")
        or ""
    ).strip()


def ensure_partner_session_from_state() -> bool:
    """STEP4 등: STEP2에서 등록한 상대방만 p_gapja·p_data를 복구합니다."""
    if not partner_is_registered():
        clear_partner_analysis_state()
        return False
    _resync_partner_gapja_from_p_data()
    if _gapja_pillars_valid(st.session_state.get("p_gapja"), min_pillars=3):
        pn = _partner_name_from_session()
        if pn:
            st.session_state.p_name = pn
            st.session_state.partner_name_snapshot = pn
            return True
        clear_partner_analysis_state()
        return False

    pn = _partner_name_from_session()
    if not pn:
        clear_partner_analysis_state()
        return False

    p_data = st.session_state.get("p_data")
    try:
        if p_data and isinstance(p_data, (list, tuple)) and len(p_data) >= 6:
            py, pm, pd, pt_str, p_is_lunar, p_is_leap = p_data[:6]
            py, pm, pd = int(py), int(pm), int(pd)
        else:
            py = int(st.session_state.get("p_y", 0))
            pm = int(st.session_state.get("p_m", 0))
            pd = int(st.session_state.get("p_d", 0))
            pt_str = str(st.session_state.get("p_time") or "모름")
            pl = str(st.session_state.get("p_lunar") or "양력")
            p_is_lunar = pl == "음력"
            p_is_leap = (
                str(st.session_state.get("p_leap") or "평달") == "윤달" if p_is_lunar else False
            )
    except (TypeError, ValueError):
        return False

    if pt_str not in STEP2_TIME_OPTIONS:
        pt_str = "모름"
    if not (1900 <= py <= 2100 and 1 <= pm <= 12):
        return False
    last_d = calendar.monthrange(py, pm)[1]
    if not (1 <= pd <= last_d):
        return False

    try:
        p_gapja = _gapja_from_birth(
            py,
            pm,
            pd,
            pt_str,
            is_lunar=bool(p_is_lunar),
            is_leap=bool(p_is_leap),
        )
    except Exception:
        return False
    if not _gapja_pillars_valid(p_gapja, min_pillars=3):
        return False

    st.session_state.p_name = pn
    st.session_state.partner_name_snapshot = pn
    st.session_state.p_gapja = list(p_gapja)
    st.session_state.p_data = (py, pm, pd, pt_str, bool(p_is_lunar), bool(p_is_leap))
    pg = str(st.session_state.get("p_gender") or "여자")
    st.session_state.p_gender = pg if pg in ("남자", "여자") else "여자"
    return True


# -------------------- misc used by steps --------------------
def get_detailed_ten_stem(user_stem: str, target_stem: str) -> str:
    u_el = STEM_ELEMENT.get(user_stem, "木")
    t_el = STEM_ELEMENT.get(target_stem, "木")
    u_yin = user_stem in ("乙", "丁", "己", "辛", "癸")
    t_yin = target_stem in ("乙", "丁", "己", "辛", "癸")
    if u_el == t_el:
        return "비견" if u_yin == t_yin else "겁재"
    if (u_el, t_el) in [("木", "火"), ("火", "土"), ("土", "金"), ("金", "水"), ("水", "木")]:
        return "식신" if u_yin == t_yin else "상관"
    if (u_el, t_el) in [("木", "土"), ("火", "金"), ("土", "水"), ("金", "木"), ("水", "火")]:
        return "정재" if u_yin != t_yin else "편재"
    if (u_el, t_el) in [("木", "金"), ("火", "水"), ("土", "木"), ("金", "火"), ("水", "土")]:
        return "정관" if u_yin != t_yin else "편관"
    return "정인" if u_yin != t_yin else "편인"


def _step10_exec_point_texts(max_el: str, min_el: str, yongshin: str) -> tuple[str, str, str]:
    """총평(STEP10) 실행 포인트 본문 — 각 50자 이상."""
    t1 = (
        f"**{max_el}** 기운은 팔자 안에서 눈에 띄게 비중이 큰 축이라, 일과 관계에서 **반복되는 성과 패턴의 출발점**이 됩니다. "
        "강점을 과시하기보다 한두 가지 핵심 영역에 집중해 ‘주무기’로 쓰면 같은 힘으로도 결과의 질이 달라집니다. "
        "우선순위를 정하고 실행 속도를 조절하면 피로 대비 효율이 크게 좋아집니다."
    )
    t2 = (
        f"**{min_el}** 기운은 상대적으로 약해 **체력·집중력·판단 흔들림**으로 드러나기 쉽습니다. "
        "부족함을 숨기기보다 수면·식습관·공간·색·소리처럼 일상 레이어에서 꾸준히 채우면 위기 순간에도 회복 탄력이 생깁니다. "
        "작은 루틴이 쌓일수록 심리적 안전판이 두터워지고, 무리한 도전을 줄일 수 있습니다."
    )
    t3 = (
        f"**{yongshin}** 용신은 선택과 방향의 **북극성**에 해당합니다. 이직·계약·연애·투자처럼 결과가 크게 갈리는 결정일수록, "
        "용신이 살아나는 환경·시간대·관계를 고르는지를 먼저 점검하세요. "
        "용신 쪽으로 에너지가 모이면 노력 대비 성과가 따라붙기 쉽고, 역행할 때는 일부러 속도를 늦추는 것이 이득입니다."
    )
    return t1, t2, t3


def step10_oheng_blend_markdown(
    el_percents: dict[str, Any], max_el: str | None, min_el: str | None
) -> str:
    """구 STEP8 오행 해석·처방을 총평 본문에 자연스럽게 이어 붙이는 마크다운."""
    if not el_percents:
        return ""
    try:
        max_e = str(max_el or max(el_percents, key=lambda k: float(el_percents.get(k, 0) or 0)))
        min_e = str(min_el or min(el_percents, key=lambda k: float(el_percents.get(k, 0) or 0)))
    except Exception:
        return ""
    desc_map = {
        "木": "성장·확장·추진력",
        "火": "열정·표현력·에너지",
        "土": "안정·중심·신뢰",
        "金": "결단·통제·정확성",
        "水": "지혜·유연·적응력",
    }
    p_max = float(el_percents.get(max_e, 0) or 0)
    p_min = float(el_percents.get(min_e, 0) or 0)
    lines: list[str] = [
        "**오행 밸런스와 생활 리듬**",
        f"팔자 기운을 한 번 더 짚으면 **{max_e}**이(가) 상대적으로 두텁게 쌓여(**약 {p_max:.0f}%** 근처) 겉으로 드러나기 쉽고, "
        f"**{min_e}**이(가) 비어 있으면(**약 {p_min:.0f}%** 근처) 피로·집중·관계에서 흔들리기 쉬운 구간이 됩니다. "
        "아래는 다섯 기운 각각의 성격입니다.",
        "",
    ]
    for el in ["木", "火", "土", "金", "水"]:
        pct = float(el_percents.get(el, 0) or 0)
        dm = desc_map.get(el, "")
        lines.append(f"- **{el}** ({pct:.0f}%) — {dm}")
    lines.extend(
        [
            "",
            f"**기운 보강**: 부족한 **{min_e}** 쪽을 색·물건·환경으로 살짝 채워 주세요(녹·적·황·백·청 톤을 생활에 섞기). "
            f"이미 강한 **{max_e}** 은(는) 과열이 되지 않도록 호흡·휴식·우선순위로 분출 채널을 만들면, 위 총평의 실행력이 한층 매끄럽게 이어집니다.",
        ]
    )
    return "\n".join(lines)


DAEWON_TEN_INTERP = {
    "비견": "⚔️ 자기주도, 독립심 강화",
    "겁재": "⚔️ 경쟁, 협력과 갈등 공존",
    "식신": "✨ 창의력, 표현력, 예술적 성과",
    "상관": "✨ 자유로운 생각, 혁신, 반항 기질",
    "정재": "💰 안정적 재물, 정재운",
    "편재": "💰 투기적 재물, 사업운",
    "정관": "📊 안정적 지위, 책임, 승진",
    "편관": "📊 권력, 도전, 카리스마",
    "정인": "📚 안정적 학습, 보호, 지식",
    "편인": "📚 창의적 학습, 예술, 독창성",
}


