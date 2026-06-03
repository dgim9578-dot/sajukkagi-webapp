"""분석 화면(STEP 3~10)용 즐겨찾기(⭐) + 메모 — ``st.session_state`` 에만 저장됩니다."""

from __future__ import annotations

import hashlib

import streamlit as st

from saju_app.ui import components as M

MEMO_DOWNLOAD_GUIDE = "여기에 메모 하시고 AI 쳇봇에서 내려 받기 하세요"

_STEP_LABELS: dict[int, str] = {
    3: "STEP 3 사주 원국",
    4: "STEP 4 궁합",
    5: "STEP 5 신살",
    6: "STEP 6 오늘운",
    7: "STEP 7 주역",
    8: "STEP 8 타로",
    9: "STEP 9 라이프 로드맵",
    10: "STEP 10 종합 리포트",
}


def _gapja_key(gapja: object, *, max_pillars: int = 4) -> str:
    if not gapja or not isinstance(gapja, (list, tuple)):
        return ""
    return "/".join(str(x) for x in gapja[:max_pillars])


def build_analysis_entry_id(step: int) -> str:
    """현재 세션 기준으로 항목 ID(짧은 해시). 같은 사주·같은 조건이면 동일 ID."""
    parts: list[str] = [
        str(int(step)),
        M.session_user_display_name(),
        _gapja_key(st.session_state.get("u_gapja")),
    ]
    if int(step) == 4:
        parts.append(
            str(
                st.session_state.get("partner_name_snapshot")
                or st.session_state.get("p_name")
                or ""
            ).strip()
        )
        parts.append(_gapja_key(st.session_state.get("p_gapja")))
    if int(step) == 6:
        parts.append(M.now_kst().date().isoformat())
        parts.append(str(st.session_state.get("step6_today_pick") or "직장"))
    if int(step) == 7:
        parts.append(M.now_kst().date().isoformat())
    if int(step) == 8:
        parts.append(str(st.session_state.get("step8_tarot_signature") or ""))
    raw = "|".join(parts).encode("utf-8", errors="replace")
    digest = hashlib.sha256(raw).hexdigest()[:20]
    return f"s{int(step)}-{digest}"


def _bookmark_store() -> dict[str, dict[str, object]]:
    return st.session_state.setdefault("saju_analysis_bookmarks_v1", {})


def _step_from_entry_id(entry_id: str) -> int | None:
    head = str(entry_id or "").split("-", 1)[0]
    if not head.startswith("s"):
        return None
    try:
        return int(head[1:])
    except ValueError:
        return None


def build_all_memos_download_text() -> str:
    """세션에 남은 분석 메모를 텍스트 다운로드용으로 묶습니다."""
    store = _bookmark_store()
    merged: dict[str, dict[str, object]] = {
        str(k): dict(v)
        for k, v in store.items()
        if isinstance(k, str) and isinstance(v, dict)
    }

    # 아직 on_change 저장 전인 현재 위젯 값도 함께 반영합니다.
    for key, value in st.session_state.items():
        sk = str(key)
        if sk.startswith("saju_bm_memo__"):
            bid = sk.replace("saju_bm_memo__", "", 1)
            rec = dict(merged.get(bid, {}))
            rec["memo"] = str(value or "")
            star_key = f"saju_bm_star__{bid}"
            rec["star"] = bool(st.session_state.get(star_key, rec.get("star", False)))
            merged[bid] = rec

    rows: list[tuple[int, str, dict[str, object]]] = []
    for bid, rec in merged.items():
        memo = str(rec.get("memo") or "").strip()
        if not memo and not bool(rec.get("star", False)):
            continue
        step = _step_from_entry_id(bid) or 99
        rows.append((step, bid, rec))

    now = M.now_kst().strftime("%Y-%m-%d %H:%M:%S")
    name = M.session_user_display_name()
    lines: list[str] = [
        "사주까기 분석 메모 모음",
        f"이름: {name}",
        f"다운로드: {now}",
        "",
    ]
    if not rows:
        lines.append("저장된 메모가 없습니다.")
        return "\n".join(lines)

    for step, bid, rec in sorted(rows, key=lambda x: (x[0], x[1])):
        label = _STEP_LABELS.get(step, f"STEP {step}")
        star = "예" if bool(rec.get("star", False)) else "아니오"
        memo = str(rec.get("memo") or "").strip() or "(메모 없음)"
        lines.extend(
            [
                f"[{label}]",
                f"즐겨찾기: {star}",
                memo,
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def render_all_memos_download_button(*, key: str = "step11_all_memos_download") -> None:
    """STEP11에서 전체 분석 메모를 내려받는 버튼(모바일 2열 배치용)."""
    text = build_all_memos_download_text()
    date_key = M.now_kst().strftime("%Y%m%d")
    st.download_button(
        label="📝 전체 분석 메모 내려받기",
        data=("\ufeff" + text).encode("utf-8"),
        file_name=f"saju_memos_{date_key}.txt",
        mime="text/plain;charset=utf-8",
        key=key,
        use_container_width=True,
        type="secondary",
    )


def _persist_bookmark_step(step: int) -> None:
    """즐겨찾기·메모를 세션 북마크 dict에 반영(인앱 WebView에서 제자리 dict 갱신 이슈 회피용 전체 대입)."""
    bid = build_analysis_entry_id(step)
    sk = f"saju_bm_star__{bid}"
    mk = f"saju_bm_memo__{bid}"
    base = st.session_state.get("saju_analysis_bookmarks_v1")
    bm = dict(base) if isinstance(base, dict) else {}
    bm[bid] = {
        "star": bool(st.session_state.get(sk, False)),
        "memo": str(st.session_state.get(mk, "")),
    }
    st.session_state["saju_analysis_bookmarks_v1"] = bm


def render_analysis_favorite_memo_band(*, step: int) -> None:
    """⭐ + 메모 입력줄. ``premium_analysis_shell`` 안 맨 위에 두는 것을 권장합니다."""
    bid = build_analysis_entry_id(step)
    store = _bookmark_store()
    rec = store.get(bid)
    if not isinstance(rec, dict):
        rec = {"star": False, "memo": ""}
    star0 = bool(rec.get("star"))
    memo0 = str(rec.get("memo") or "")

    star_key = f"saju_bm_star__{bid}"
    memo_key = f"saju_bm_memo__{bid}"

    # 분석 ID(bid)가 바뀌면(STEP2 재저장 등) 이전 위젯 세션 키를 제거해 상태 꼬임·세션 오염을 방지합니다.
    track = f"_saju_bm_tracked_bid_{int(step)}"
    prev_bid = st.session_state.get(track)
    if prev_bid is not None and prev_bid != bid:
        st.session_state.pop(f"saju_bm_star__{prev_bid}", None)
        st.session_state.pop(f"saju_bm_memo__{prev_bid}", None)
    st.session_state[track] = bid

    # 수평 ``st.container``는 React removeChild 오류가 보고되어, 항상 columns로 고정합니다.
    with st.container(key=f"saju_fav_memo_band_step{int(step)}"):
        r1, r2 = st.columns([0.22, 0.78])
        with r1:
            st.checkbox(
                "⭐ 즐겨찾기",
                value=star0,
                key=star_key,
                on_change=_persist_bookmark_step,
                args=(int(step),),
            )
        with r2:
            M.text_area_no_autofill(
                "메모",
                value=memo0,
                height=78,
                max_chars=800,
                key=memo_key,
                label_visibility="collapsed",
                placeholder=MEMO_DOWNLOAD_GUIDE,
                on_change=_persist_bookmark_step,
                args=(int(step),),
            )
