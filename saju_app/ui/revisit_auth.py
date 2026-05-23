"""홈(STEP1) 재방문 비밀번호 — 목록 노출 없이 본인 기록만 불러오기."""

from __future__ import annotations

import streamlit as st

from saju_app.persistence import storage as saju_storage
from saju_app.ui import components as M
from saju_app.ui import extras_integration as X


def render_revisit_home_header() -> None:
    """재방문 섹션 제목·안내만 (입력·버튼은 STEP1 CTA 행)."""
    with st.container(key="step1_revisit_auth"):
        X.render_colored_header_or_fallback(
            label="재방문",
            description="재 방문자는 비밀번호를 입력하세요",
            color_name="violet-70",
        )


def render_revisit_home_header_and_pin() -> None:
    """하위 호환."""
    render_revisit_home_header()


def process_revisit_login(pin: str) -> None:
    """「내 기록 불러오기」 클릭 시 비밀번호 검증·프로필 복원."""
    pin_norm = saju_storage.normalize_revisit_pin(pin)
    err = saju_storage.validate_revisit_pin(pin_norm)
    if err:
        st.error(err)
        return
    rec = saju_storage.get_user_profile_by_revisit_pin(pin_norm)
    if not rec:
        st.error(
            "등록된 재방문 비밀번호가 없거나 일치하지 않습니다. "
            "STEP2에서 비밀번호·확인을 입력한 뒤 「저장하고 사주 분석 시작하기」를 눌러 "
            "「재방문 비밀번호가 설정되었습니다」 메시지가 나온 뒤 다시 시도해 주세요."
        )
        return
    if not M.apply_user_profile_record_to_session(rec, dest_step=3):
        st.error(
            "비밀번호는 맞지만 프로필을 불러오지 못했습니다. "
            "STEP2에서 생년월일·시간을 다시 저장한 뒤 재시도해 주세요."
        )


def render_revisit_home_block() -> None:
    """하위 호환."""
    render_revisit_home_header()
