"""STEP 12 — 관리자 전용 공간 (완성형 · 상담 방 저장소 연동)."""

from __future__ import annotations

import hashlib
import html
import os
from pathlib import Path

import streamlit as st

from saju_app.persistence import storage as saju_storage
from saju_app.ui import components as M
from saju_app.ui.execution import report_exception_to_streamlit
from saju.ui.step_11 import filter_conversation_messages
from saju_app.ui.chat_messages import conversation_html, dedupe_chat_messages

_ADMIN_REPLY_SENT_FP_KEY = "admin_step12_last_sent_fp"


def _room_btn_key(prefix: str, room_key: str) -> str:
    return f"{prefix}_{hashlib.md5(room_key.encode('utf-8')).hexdigest()}"


def _admin_render_msg(msg: dict, *, customer_name: str) -> None:
    role = str(msg.get("role") or "assistant")
    body = str(msg.get("msg") or "")
    is_manual = bool(msg.get("is_manual", False))
    if role == "user":
        safe = html.escape(body).replace("\n", "<br>")
        st.markdown(
            f"""
<div style="background:#1e3a8a; padding:18px; border-radius:14px; margin:12px 0;
            border-left:6px solid #60a5fa; color:white;">
  <strong style="color:#93c5fd;">👤 고객님 질문:</strong><br>
  {safe}
</div>
""",
            unsafe_allow_html=True,
        )
        return
    if is_manual:
        safe = html.escape(body).replace("\n", "<br>")
        st.markdown(
            f"""
<div class="saju-chat-msg">
  <div class="saju-chat-bubble saju-chat-bubble--expert" style="background:#4c1d95;padding:14px 18px;
            border-radius:14px;border-left:6px solid #c4b5fd;color:white;max-width:100%;box-sizing:border-box;">
    <strong style="color:#ddd6fe;">⭐ 사주까기 전문가 답변:</strong><br>
    {safe}
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        return
    else:
        st.markdown(
            f"""
<div class="saju-chat-msg">
  <div class="saju-chat-bubble saju-chat-bubble--ai" style="background:#1f2937;padding:16px 18px;
            border-radius:14px;border-left:6px solid #facc15;color:#e2e8f0;line-height:1.65;
            max-width:100%;box-sizing:border-box;">
  <strong style="color:#fcd34d;">🤖 AI 자동 분석 내용:</strong><br><br>
  {body}
  </div>
</div>
""",
            unsafe_allow_html=True,
        )


_ADMIN_AUTH_SESSION_KEY = "saju_admin_authenticated"


def _admin_append_manual_reply(room_key: str, txt: str) -> bool:
    """관리자 수동 답변을 저장소에 한 번만 추가합니다. 이미 반영된 경우 False."""
    rk = str(room_key or "").strip()
    if not rk or not txt:
        return False
    fp = (rk, txt)
    if st.session_state.get(_ADMIN_REPLY_SENT_FP_KEY) == fp:
        return False
    try:
        raw_msgs, lab = saju_storage.get_shared_chat_room(rk)
    except Exception:
        raw_msgs, lab = [], None
    msgs = dedupe_chat_messages(list(raw_msgs or []))
    tail = msgs[-1] if msgs else None
    if (
        isinstance(tail, dict)
        and str(tail.get("role") or "") == "assistant"
        and bool(tail.get("is_manual", False))
        and str(tail.get("msg") or "").strip() == txt
    ):
        st.session_state[_ADMIN_REPLY_SENT_FP_KEY] = fp
        return False
    msgs.append({"role": "assistant", "msg": txt, "is_manual": True})
    lab_out = dict(lab) if isinstance(lab, dict) else {}
    lab_out["admin_touch_ts"] = M.now_kst().isoformat(timespec="seconds")
    M._persist_shared_chat_bus(rk, msgs, lab_out)
    st.session_state[_ADMIN_REPLY_SENT_FP_KEY] = fp
    return True


def _normalize_admin_secret(value: object) -> str:
    return str(value or "").strip().strip('"').strip("'")


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_admin_password() -> tuple[str, str]:
    """관리자 비밀번호와 출처 라벨을 반환합니다."""
    pwd = ""
    source = ""
    try:
        pwd = _normalize_admin_secret(st.secrets.get("SAJU_ADMIN_PASSWORD", ""))
        if pwd:
            source = "Streamlit secrets"
    except Exception:
        pwd = ""
    if not pwd:
        pwd = _normalize_admin_secret(os.environ.get("SAJU_ADMIN_PASSWORD", ""))
        if pwd:
            source = "환경변수 SAJU_ADMIN_PASSWORD"
    if not pwd:
        secrets_path = _project_root() / ".streamlit" / "secrets.toml"
        if secrets_path.is_file():
            try:
                import tomllib

                data = tomllib.loads(
                    secrets_path.read_text(encoding="utf-8-sig")
                )
                pwd = _normalize_admin_secret(data.get("SAJU_ADMIN_PASSWORD", ""))
                if pwd:
                    source = str(secrets_path)
            except Exception:
                pwd = ""
    return pwd, source


def _render_step12_room_messages() -> None:
    """관리자 모니터: 방 키는 세션 `admin_selected_room`에서 읽어 저장소와 표시합니다.

    ``@st.fragment``·``st.chat_input`` 조합은 동일 메시지가 두 번 그려지거나 저장될 수 있어 사용하지 않습니다.
    """
    rk = str(st.session_state.get("admin_selected_room") or "").strip()
    if not rk:
        return
    _cn = ""
    try:
        msgs, lab = saju_storage.get_shared_chat_room(rk)
        if isinstance(lab, dict):
            _cn = str(lab.get("u_name") or "")
    except Exception:
        msgs = []
    conv = dedupe_chat_messages(filter_conversation_messages(list(msgs or [])))
    try:
        chat_container = st.container(border=True, key="step12_hanji_chat")
    except TypeError:
        chat_container = st.container(border=True)
    with chat_container:
        empty = (
            '<p style="margin:0;color:#6b7280;">현재 수신된 고객 메시지가 없습니다.</p>'
            if not conv
            else ""
        )
        st.markdown(
            conversation_html(conv, empty_html=empty, customer_label=_cn or "고객"),
            unsafe_allow_html=True,
        )


def render() -> None:
    st.title("🛠️ 관리자 전용 공간")
    st.markdown("### Administrator Exclusive Panel")

    if not M.admin_panel_enabled():
        st.warning("관리자 기능은 공개 앱 빌드에서 비활성화되어 있습니다.")
        return

    if "all_customers" not in st.session_state:
        st.session_state.all_customers = []

    admin_password, pwd_source = _load_admin_password()
    if not admin_password:
        st.error(
            "관리자 비밀번호가 설정되지 않았습니다. "
            "프로젝트 폴더에 `.streamlit/secrets.toml` 을 만들고 "
            "`SAJU_ADMIN_PASSWORD = \"본인비밀번호\"` 를 넣어 주세요."
        )
        st.code(
            "# .streamlit/secrets.toml\n"
            'SAJU_ADMIN_PASSWORD = "saju-admin-local"\n'
            'SAJU_ADMIN_ENABLED = "true"\n\n'
            "# 또는 PowerShell:\n"
            "#   .\\scripts\\setup-streamlit-secrets.bat",
            language="toml",
        )
        st.caption(
            "설정 후 **SajuPro-Admin** 창을 Ctrl+C로 종료했다가 다시 실행하세요. "
            "환경변수로도 가능: `$env:SAJU_ADMIN_PASSWORD = '비밀번호'`"
        )
        return

    if not st.session_state.get(_ADMIN_AUTH_SESSION_KEY):
        st.caption(
            f"비밀번호는 `{pwd_source}` 에 설정된 값과 **완전히 동일**해야 합니다. "
            "앞뒤 공백 없이 입력하세요."
        )
        st.caption(
            "`setup-streamlit-secrets` 로 만든 로컬 기본값은 **`saju-admin-local`** 입니다. "
            "이미 바꿨다면 `secrets.toml` 에 적어 둔 문자열을 그대로 입력하세요."
        )
        with st.form("step12_admin_login", clear_on_submit=False):
            admin_pwd_input = M.password_input_no_autofill(
                "🔑 관리자 비밀번호",
                help="관리자 비밀번호는 `.streamlit/secrets.toml` 또는 환경변수에서 읽습니다.",
            )
            submitted = st.form_submit_button("로그인", type="primary", use_container_width=True)

        if not submitted:
            return
        if _normalize_admin_secret(admin_pwd_input) != admin_password:
            st.error("❌ 관리자 비밀번호가 일치하지 않습니다.")
            st.caption(
                f"현재 앱이 읽은 설정: **{pwd_source}** · **{len(admin_password)}자**. "
                "다른 터미널(8501 일반 앱)만 켜 두었거나 `secrets.toml` 수정 후 재시작하지 않았을 수 있습니다."
            )
            return
        st.session_state[_ADMIN_AUTH_SESSION_KEY] = True
        st.rerun()

    st.success("✅ 관리자 인증 완료")
    st.divider()

    try:
        cfg = saju_storage.get_config()
        st.caption(
            f"동기화 백엔드: **{html.escape(str(cfg.get('storage', '?')))}** · "
            f"Redis 방 TTL: **{html.escape(str(cfg.get('redis_ttl_human', '?')))}** · "
            "고객(STEP11)과 **다른 PC**에서 보려면 Redis 또는 동일 `SAJU_SQLITE_PATH`가 필요합니다."
        )
    except Exception:
        pass

    with st.expander("📊 Redis TTL 모니터링", expanded=False):
        try:
            mon = saju_storage.redis_room_ttl_monitor(sample_limit=50)
        except Exception as e:
            mon = {"error": str(e)}
        if not mon.get("redis_enabled"):
            st.info("Redis 모드가 아닙니다(`SAJU_STORAGE=redis`). SQLite만 사용 중이면 TTL은 해당 없습니다.")
        elif not mon.get("redis_connected"):
            st.warning("Redis에 연결되지 않았습니다. `REDIS_URL`·네트워크를 확인하세요.")
        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("설정 TTL", str(mon.get("configured_ttl_human") or "?"))
            c2.metric("인덱스 방 수", int(mon.get("room_index_size") or 0))
            c3.metric("TTL 적용 방", int(mon.get("rooms_with_ttl") or 0))
            c4.metric("TTL 없음(영구)", int(mon.get("rooms_without_ttl") or 0))
            if mon.get("permanent_storage"):
                st.error(
                    "`SAJU_REDIS_ROOM_TTL_SEC=0` 으로 **영구 보관** 중입니다. "
                    "메모리 증가 위험이 있으니 7~30일(예: 604800~2592000) 설정을 권장합니다."
                )
            mem = str(mon.get("redis_used_memory_human") or "").strip()
            if mem:
                st.caption(f"Redis 메모리 사용량(참고): **{html.escape(mem)}**")
            missing = int(mon.get("rooms_missing_keys") or 0)
            if missing:
                st.caption(f"메시지 키가 없는 방(인덱스만 남음): **{missing}**건")
            sample = mon.get("sample")
            if isinstance(sample, list) and sample:
                st.markdown("**방별 남은 TTL (최근 샘플)**")
                rows = []
                for row in sample:
                    if not isinstance(row, dict):
                        continue
                    rk = str(row.get("room_key") or "")
                    rows.append(
                        {
                            "방": rk[:20] + ("…" if len(rk) > 20 else ""),
                            "메시지 TTL": str(row.get("msg_ttl_human") or row.get("msg_ttl_sec")),
                            "라벨 TTL(초)": row.get("label_ttl_sec"),
                        }
                    )
                if rows:
                    st.dataframe(rows, use_container_width=True, hide_index=True)
            elif int(mon.get("room_index_size") or 0) == 0:
                st.caption("등록된 Redis 채팅 방이 없습니다.")
        if mon.get("error"):
            st.caption(f"모니터 오류: {html.escape(str(mon.get('error'))[:200])}")

    _legacy = st.session_state.get("admin_monitor_room_key")
    if _legacy and not st.session_state.get("admin_selected_room"):
        st.session_state.admin_selected_room = str(_legacy).strip()
        st.session_state.pop("admin_monitor_room_key", None)

    # ---------- 상담 방 선택 ----------
    st.subheader("📋 상담 방 선택")
    try:
        rooms = list(saju_storage.list_chat_room_summaries(200))
    except Exception:
        rooms = []

    room_options: list[str] = []
    room_labels: dict[str, str] = {}
    for room in rooms:
        rk = str(room.get("room_key") or "").strip()
        if not rk:
            continue
        u_nm = str(room.get("u_name") or "이름 없음")
        ilju = str(room.get("user_gapja") or "")
        ctype = str(room.get("consultation_type") or "미분류")
        mc = int(room.get("msg_count") or 0)
        room_options.append(rk)
        meta = " · ".join(x for x in (ilju, ctype) if x)
        room_labels[rk] = f"{u_nm} · {meta} · {rk[:10]}… · 💬{mc}" if meta else f"{u_nm} · {rk[:10]}… · 💬{mc}"

    if not room_options:
        st.session_state.pop("admin_selected_room", None)
        st.info("진행 중인 상담 방이 없습니다. STEP11에서 대화를 시작하면 목록에 나타납니다.")
        selected = ""
    else:
        cur = str(st.session_state.get("admin_selected_room") or "").strip()
        idx0 = room_options.index(cur) if cur in room_options else 0
        pick = st.selectbox(
            "모니터링할 방",
            options=room_options,
            format_func=lambda rk: room_labels.get(rk, rk),
            index=idx0,
            key="admin_room_pickbox",
        )
        selected = str(pick or "").strip()
        st.session_state.admin_selected_room = selected

        col_o1, col_o2, col_o3 = st.columns([1, 1, 1])
        with col_o1:
            if st.button("STEP11로 이 방 열기", use_container_width=True, key="admin_open_step11_room"):
                st.session_state.step11_chat_room_key = selected
                st.session_state["_navigated_to_chat_this_run"] = True
                M.assign_step_and_rerun(11)
        with col_o2:
            if st.button(
                "이 방 기록 삭제",
                use_container_width=True,
                key="admin_del_one_room",
                help="선택한 방의 채팅만 삭제합니다.",
            ):
                try:
                    saju_storage.clear_shared_chat_room(selected)
                except Exception as e:
                    report_exception_to_streamlit(e, prefix="방 삭제")
                st.session_state.pop("admin_selected_room", None)
                M.rerun_full_app()
        with col_o3:
            if st.button("목록 새로고침", use_container_width=True, key="admin_room_list_refresh"):
                M.rerun_full_app()

    st.divider()

    # ---------- 실시간 고객 채팅 모니터링 ----------
    st.subheader("💬 실시간 고객 채팅 모니터링")

    selected_room = str(st.session_state.get("admin_selected_room") or "").strip()
    _peek_lab: dict | None = None
    if selected_room:
        try:
            _, _peek_lab = saju_storage.get_shared_chat_room(selected_room)
        except Exception:
            _peek_lab = None

        if _peek_lab and isinstance(_peek_lab, dict):
            st.caption(
                f"고객: **{html.escape(str(_peek_lab.get('u_name', '') or ''))}** · "
                f"일주: **{html.escape(str(_peek_lab.get('user_gapja') or _peek_lab.get('user_ilju') or '-'))}** · "
                f"고민유형: **{html.escape(str(_peek_lab.get('consultation_type') or '미분류'))}** · "
                f"연락처: {html.escape(str(_peek_lab.get('contact', '-') or '-'))}"
            )

        _frag_col, _refresh_col = st.columns([4, 1])
        with _refresh_col:
            if st.button("채팅 새로고침", use_container_width=True, key="admin_chat_refresh"):
                M.rerun_full_app()
        with _frag_col:
            _render_step12_room_messages()

        st.divider()
        current_name = str(_peek_lab.get("u_name") or "").strip() if isinstance(_peek_lab, dict) else ""
        if current_name and st.button("📥 현재 상담 고객 정보 DB에 저장", key="admin_save_customer_db"):
            u_data = st.session_state.get("u_data", (0, 0, 0, ""))
            contact = str(_peek_lab.get("contact") or "미등록") if isinstance(_peek_lab, dict) else "미등록"
            if not isinstance(u_data, (list, tuple)) or len(u_data) < 3:
                st.warning("세션에 본인 생년월일(u_data)이 없어 저장할 수 없습니다.")
            else:
                birth_str = f"{u_data[0]}년 {u_data[1]}월 {u_data[2]}일"
                time_str = str(u_data[3]) if len(u_data) > 3 else "미입력"
                new_cust = {
                    "name": current_name,
                    "birth": birth_str,
                    "time": time_str,
                    "contact": contact,
                    "room_key": selected_room,
                    "timestamp": M.now_kst().strftime("%Y-%m-%d %H:%M"),
                }
                ac: list[dict] = list(st.session_state.all_customers or [])
                if not any(
                    str(c.get("name")) == current_name and str(c.get("birth")) == birth_str for c in ac
                ):
                    ac.append(new_cust)
                    st.session_state.all_customers = ac
                    st.success(f"✅ {html.escape(current_name)} 고객 정보가 등록되었습니다.")
                    M.rerun_full_app()
                else:
                    st.info("이미 등록된 고객입니다.")

        admin_reply = st.chat_input(
            "관리자 답변을 입력하세요…",
            key="admin_step12_chat_reply",
        )
        if admin_reply and str(admin_reply).strip():
            txt = str(admin_reply).strip()
            if _admin_append_manual_reply(selected_room, txt):
                M.rerun_full_app()

        err = st.session_state.pop("_shared_chat_persist_error", None)
        if err:
            st.warning(f"답변 저장 실패: {html.escape(str(err)[:400])}")
    else:
        st.info("상담 방을 선택하면 채팅이 표시됩니다.")

    st.divider()
    st.markdown("##### 등록된 고객 DB")
    if st.session_state.all_customers:

        def _cust_uid(c: dict) -> str:
            return f"{c.get('name')}|{c.get('birth')}|{c.get('timestamp')}|{c.get('room_key', '')}"

        for cust in list(st.session_state.all_customers):
            nm = str(cust.get("name") or "")
            ts = str(cust.get("timestamp") or "")
            uid = _cust_uid(cust)
            with st.expander(f"👤 {html.escape(nm)} ({html.escape(ts)})"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"📅 **생년월일**: {cust.get('birth', '')}")
                    st.write(f"⏰ **태어난 시간**: {cust.get('time', '')}")
                with c2:
                    st.write(f"📞 **연락처**: {cust.get('contact', '')}")
                    st.caption(f"방: `{html.escape(str(cust.get('room_key', ''))[:16])}…`")
                if st.button(
                    "🗑️ 삭제",
                    key=f"admin_del_cust_{_room_btn_key('dc', uid)}",
                ):
                    st.session_state.all_customers = [
                        c
                        for c in list(st.session_state.all_customers or [])
                        if _cust_uid(c) != uid
                    ]
                    M.rerun_full_app()
    else:
        st.info("등록된 고객 데이터가 없습니다.")

    st.divider()
    st.subheader("⚠️ 시스템 초기화")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧹 전체 채팅 기록 삭제(선택 방)", use_container_width=True, key="admin_clear_sel_room"):
            rk = str(st.session_state.get("admin_selected_room") or "").strip()
            if rk:
                try:
                    saju_storage.clear_shared_chat_room(rk)
                except Exception as e:
                    report_exception_to_streamlit(e, prefix="채팅 비우기")
                st.success("선택한 방의 채팅 기록을 비웠습니다.")
            else:
                st.warning("선택된 방이 없습니다.")
            M.rerun_full_app()
    with col2:
        confirm = st.checkbox("모든 고객 DB 삭제 승인", key="admin_wipe_customers_ack")
        if st.button(
            "🗑️ 모든 고객 DB 삭제",
            type="primary",
            use_container_width=True,
            disabled=not confirm,
            key="admin_wipe_all_customers",
        ):
            st.session_state.all_customers = []
            st.success("모든 고객 데이터가 삭제되었습니다.")
            M.rerun_full_app()
