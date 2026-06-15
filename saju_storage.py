"""
사주프로 — 상담/채팅/프리필 영속화 백엔드.

환경 변수
---------
SAJU_STORAGE
    `sqlite` (기본) | `redis`
SAJU_SQLITE_PATH
    SQLite DB 파일 경로 (기본: 앱 폴더의 `saju_app.db`)
REDIS_URL
    `SAJU_STORAGE=redis` 일 때만 (예: redis://localhost:6379/0)
SAJU_REDIS_ROOM_TTL_SEC
    Redis 방 메시지·라벨 키 TTL(초). **미설정 시 기본 14일**.
    ``0`` 을 명시하면 만료 없음(영구, 메모리 증가 위험).

런타임에 읽은 값만 모아 보려면 ``get_config()`` (같은 모듈)를 사용하세요.

SQLite 모드에서는 STEP11 방 단위로 행을 갱신해 JSON 전체를 매번 덮어쓰지 않습니다.
연결은 **스레드당 1개**를 재사용하고(WAL), 스키마·레거시 이관은 **프로세스당 1회**만 수행합니다.
``_storage_rlock``(재진입 가능)으로 동시 쓰기를 직렬화해 ``SQLITE_BUSY``·중첩 호출 데드락을 줄입니다.
gunicorn/uvicorn **worker마다 별도 프로세스**이므로 worker 수만큼 DB 연결이 생깁니다(정상).
대규모 동시 쓰기가 필요하면 Postgres/SQLAlchemy Async 전환을 검토하세요.
``user_profiles`` 테이블에 본인·상대(입력 시)의 **이름·생년월일 구성·사주 간지**를
``fingerprint``(이름 + 생일·시간 JSON → sha256) 단위로 upsert 합니다.
상담 아카이브(`chat_archive`)는 **JSONL 파일이 아닌** 테이블에 append-only `INSERT`만 하며,
`session_id` 컬럼 + `idx_chat_archive_session` 인덱스로 조회·삭제합니다.
최근 N건 조회는 `pandas.read_sql_query`로 한 번에 가져온 뒤 JSON만 파싱합니다(`load_consultation_archive_records`).
세션 삭제는 `DELETE FROM chat_archive WHERE session_id=?` 한 번이며 **전체 파일/테이블 재작성이 없습니다**.
오래된 아카이브는 ``archive_prune_old_records(days=180)`` 또는 ``scripts/archive_prune.py`` 로 주기 삭제하세요.
레거시 `consultation_chat_archive.jsonl` 은 최초 1회 SQLite로 이관됩니다.

Redis 모드의 상담 아카이브는 단일 LIST+전체 재작성 대신,
**ZSET(시간순) + 행 문자열 키 + session_id별 SET(행 id)** 로 append·`DELETE`에 가깝게 분리합니다.
Redis 클라이언트는 프로세스당 하나만 캐시하며, 구 LIST 레이아웃 → v2 이관은 **최초 연결 직후 한 번**만 수행합니다.

Supabase 등 원격 Postgres는 스키마가 같다면 DATABASE_URL + SQLAlchemy로
이 모듈을 확장하면 됩니다. (아카이브 조회는 Pandas가 있으면 사용·없으면 표준 sqlite3 경로로 fallback)
"""

from __future__ import annotations

import atexit
import functools
import hashlib
import html
import secrets
import json
import logging
import os
import re
import sqlite3
import threading
import time
import uuid
import datetime as _dt
from zoneinfo import ZoneInfo
from typing import Any, Callable, Concatenate, ParamSpec, TypeVar

log = logging.getLogger(__name__)


def clear_all_user_input_sessions():
    """외부 사용자 데이터 오염 및 무작위 노출을 막기 위해
    서버 메모리와 저장소의 임시 프리필 데이터를 강제로 전면 소각하는 프로용 초기화 함수"""
    try:
        import streamlit as st

        # 1. 브라우저에 남아있는 모든 사용자 입력값(key)을 완전히 삭제
        for k in list(st.session_state.keys()):
            del st.session_state[k]

        # 2. 백엔드 저장소에 임시로 저장되었던 프리필(Prefill) 흔적 제거
        sqlite_kvs_delete_prefix("step2_prefill")
        sqlite_kvs_delete("admin_outbox")

        # 3. 변경 사항 즉시 반영
        st.success("모든 사용자 정보와 세션 버퍼가 강력하게 초기화되었습니다.")
    except Exception:
        pass

    # ============================== 스크롤 문제 해결 (최종 끝판왕 버전) ==============================
    st.set_page_config(
        page_title="사주까기 - 무료 사주풀이",
        page_icon="🔮",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # 브라우저의 모든 레벨에서 스크롤을 강제로 열어버리는 CSS
    st.markdown(
        """
        <style>
            /* 1. 최상위 브라우저 창 및 스크롤바 강제 표시 */
            html, body {
                overflow-y: scroll !important;
                overflow-x: hidden !important;
                height: auto !important;
                min-height: 100vh !important;
            }

            /* 2. Streamlit 내부 모든 뷰 컨테이너의 스크롤 제약 해제 */
            [data-testid="stAppViewContainer"], 
            .stApp, 
            [data-testid="stMain"],
            .main,
            [data-testid="stAppViewBlockContainer"] {
                overflow-y: visible !important;
                overflow-x: hidden !important;
                height: auto !important;
                max-height: none !important;
                min-height: 100vh !important;
            }

            /* 3. 콘텐츠 정렬 및 하단 여백 확보 */
            .main .block-container {
                padding-top: 2rem !important;
                padding-bottom: 10rem !important;
                overflow-y: visible !important;
                max-height: none !important;
            }

            /* 4. 상단 헤더가 스크롤을 방해하지 않도록 위치 고정 해제 */
            [data-testid="stHeader"] {
                position: absolute !important;
                background: transparent !important;
            }
        </style>
    """,
        unsafe_html=True,
    )


# ==============================================================================================

P_sql = ParamSpec("P_sql")
R_sql = TypeVar("R_sql")


def _now_kst_iso() -> str:
    return _dt.datetime.now(tz=ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")


def _parse_archive_payload_rows(raw_rows: list[Any]) -> list[dict[str, Any]]:
    """chat_archive.payload_json 문자열들 → dict (역순 보정은 호출 전에 끝낸 상태)."""
    out: list[dict[str, Any]] = []
    for raw in raw_rows:
        if not raw:
            continue
        try:
            if isinstance(raw, (bytes, bytearray)):
                s = raw.decode("utf-8", "replace")
            else:
                s = str(raw)
            obj = json.loads(s)
            if isinstance(obj, dict):
                out.append(obj)
        except Exception:
            continue
    return out


def _masked_contact(value: Any) -> str:
    """타임라인/목록용 연락처 최소 노출. 상세 방 라벨에는 원본을 유지합니다."""
    text = str(value or "").strip()
    if not text:
        return ""
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) >= 7:
        return f"{digits[:3]}-****-{digits[-4:]}"
    if len(text) <= 4:
        return "*" * len(text)
    return f"{text[:2]}***{text[-2:]}"


STEM_ELEMENT: dict[str, str] = {
    "甲": "木",
    "乙": "木",
    "丙": "火",
    "丁": "火",
    "戊": "土",
    "己": "土",
    "庚": "金",
    "辛": "金",
    "壬": "水",
    "癸": "水",
}
STEM_YIN_YANG: dict[str, str] = {
    "甲": "양",
    "乙": "음",
    "丙": "양",
    "丁": "음",
    "戊": "양",
    "己": "음",
    "庚": "양",
    "辛": "음",
    "壬": "양",
    "癸": "음",
}
BRANCH_ELEMENT: dict[str, str] = {
    "寅": "木",
    "卯": "木",
    "巳": "火",
    "午": "火",
    "辰": "土",
    "戌": "土",
    "丑": "土",
    "未": "土",
    "申": "金",
    "酉": "金",
    "亥": "水",
    "子": "水",
}
BRANCH_HIDDEN_STEMS: dict[str, list[str]] = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "戊", "庚"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
}
ELEMENT_COLORS: dict[str, dict[str, str]] = {
    "木": {"name": "목", "color": "#22C55E", "soft": "#DCFCE7"},
    "火": {"name": "화", "color": "#EF4444", "soft": "#FEE2E2"},
    "土": {"name": "토", "color": "#D4AF37", "soft": "#FEF3C7"},
    "金": {"name": "금", "color": "#E5E7EB", "soft": "#F8FAFC"},
    "水": {"name": "수", "color": "#111827", "soft": "#DBEAFE"},
}


def _element_generates(src: str) -> str:
    return {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}.get(src, "")


def _element_controls(src: str) -> str:
    return {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}.get(src, "")


def _ten_god(day_stem: str, target_stem: str) -> str:
    d_el = STEM_ELEMENT.get(day_stem, "")
    t_el = STEM_ELEMENT.get(target_stem, "")
    if not d_el or not t_el:
        return ""
    same_polarity = STEM_YIN_YANG.get(day_stem) == STEM_YIN_YANG.get(target_stem)
    if d_el == t_el:
        return "비견" if same_polarity else "겁재"
    if _element_generates(d_el) == t_el:
        return "식신" if same_polarity else "상관"
    if _element_generates(t_el) == d_el:
        return "편인" if same_polarity else "정인"
    if _element_controls(d_el) == t_el:
        return "편재" if same_polarity else "정재"
    if _element_controls(t_el) == d_el:
        return "편관" if same_polarity else "정관"
    return ""


def build_gapja_design_meta(gapja: list[str]) -> dict[str, Any]:
    """UI 차트/컬러링을 위한 간지 구조화 메타데이터."""
    pillars = [str(x or "") for x in list(gapja or [])]
    day_stem = pillars[2][0] if len(pillars) > 2 and len(pillars[2]) >= 1 else ""
    labels = ("year", "month", "day", "hour")
    element_counts = {el: 0 for el in ("木", "火", "土", "金", "水")}
    ten_god_counts: dict[str, int] = {}
    out_pillars: list[dict[str, Any]] = []

    def add_element(el: str, weight: int = 1) -> None:
        if el in element_counts:
            element_counts[el] += int(weight)

    def add_ten(ten: str) -> None:
        if ten:
            ten_god_counts[ten] = ten_god_counts.get(ten, 0) + 1

    for idx, pillar in enumerate(pillars[:4]):
        stem = pillar[0] if len(pillar) >= 1 else ""
        branch = pillar[1] if len(pillar) >= 2 else ""
        stem_el = STEM_ELEMENT.get(stem, "")
        branch_el = BRANCH_ELEMENT.get(branch, "")
        add_element(stem_el)
        add_element(branch_el)
        stem_ten = _ten_god(day_stem, stem) if day_stem and stem else ""
        add_ten(stem_ten)
        hidden_rows: list[dict[str, str]] = []
        for hidden in BRANCH_HIDDEN_STEMS.get(branch, []):
            h_el = STEM_ELEMENT.get(hidden, "")
            h_ten = _ten_god(day_stem, hidden) if day_stem else ""
            add_element(h_el)
            add_ten(h_ten)
            hidden_rows.append(
                {
                    "stem": hidden,
                    "element": h_el,
                    "element_name": ELEMENT_COLORS.get(h_el, {}).get("name", ""),
                    "ten_god": h_ten,
                    "color": ELEMENT_COLORS.get(h_el, {}).get("color", ""),
                }
            )
        out_pillars.append(
            {
                "index": idx,
                "slot": labels[idx] if idx < len(labels) else str(idx),
                "pillar": pillar,
                "stem": {
                    "char": stem,
                    "element": stem_el,
                    "element_name": ELEMENT_COLORS.get(stem_el, {}).get("name", ""),
                    "yin_yang": STEM_YIN_YANG.get(stem, ""),
                    "ten_god": stem_ten,
                    "color": ELEMENT_COLORS.get(stem_el, {}).get("color", ""),
                    "soft_color": ELEMENT_COLORS.get(stem_el, {}).get("soft", ""),
                },
                "branch": {
                    "char": branch,
                    "element": branch_el,
                    "element_name": ELEMENT_COLORS.get(branch_el, {}).get("name", ""),
                    "color": ELEMENT_COLORS.get(branch_el, {}).get("color", ""),
                    "soft_color": ELEMENT_COLORS.get(branch_el, {}).get("soft", ""),
                    "hidden_stems": hidden_rows,
                },
            }
        )
    return {
        "version": 1,
        "day_stem": day_stem,
        "palette": ELEMENT_COLORS,
        "pillars": out_pillars,
        "element_counts": element_counts,
        "ten_god_counts": ten_god_counts,
    }


_THEME_KEY_SLUG: dict[str, str] = {
    "木": "wood",
    "火": "fire",
    "土": "earth",
    "金": "metal",
    "水": "water",
}

THEME_CONFIG: dict[str, dict[str, Any]] = {
    "木": {
        "name": "목기운",
        "emoji": "🌳🌱",
        "gradient": "from-emerald-400 to-green-500",
        "accent": "#10b981",
        "primary_soft": "#d1fae5",
        "gradient_css": "linear-gradient(135deg, #10b981, #34d399)",
        "bg_pattern": "leaf",
        "font_weight": "medium",
        "vibe": "성장형, 자유로운",
    },
    "火": {
        "name": "화기운",
        "emoji": "🔥",
        "gradient": "from-red-400 to-orange-500",
        "accent": "#ef4444",
        "primary_soft": "#fee2e2",
        "gradient_css": "linear-gradient(135deg, #ef4444, #f97316)",
        "bg_pattern": "flame",
        "font_weight": "semibold",
        "vibe": "열정적, 밝고 강렬",
    },
    "土": {
        "name": "토기운",
        "emoji": "🏔️🌾",
        "gradient": "from-amber-400 to-yellow-600",
        "accent": "#d4af37",
        "primary_soft": "#fef3c7",
        "gradient_css": "linear-gradient(135deg, #d4af37, #fbbf24)",
        "bg_pattern": "earth",
        "font_weight": "medium",
        "vibe": "안정적, 신뢰와 실속",
    },
    "金": {
        "name": "금기운",
        "emoji": "✨⚔️",
        "gradient": "from-slate-300 to-gray-400",
        "accent": "#94a3b8",
        "primary_soft": "#f1f5f9",
        "gradient_css": "linear-gradient(135deg, #94a3b8, #cbd5e1)",
        "bg_pattern": "metal",
        "font_weight": "semibold",
        "vibe": "결단형, 원칙과 정리",
    },
    "水": {
        "name": "수기운",
        "emoji": "💧🌊",
        "gradient": "from-blue-500 to-indigo-600",
        "accent": "#3b82f6",
        "primary_soft": "#dbeafe",
        "gradient_css": "linear-gradient(135deg, #3b82f6, #6366f1)",
        "bg_pattern": "wave",
        "font_weight": "normal",
        "vibe": "지혜형, 유연하고 깊은",
    },
}

_THEME_DEFAULT = THEME_CONFIG["土"]

_STEM_NICKNAME: dict[str, str] = {
    "甲": "큰 나무",
    "乙": "부드러운 풀",
    "丙": "뜨거운 태양",
    "丁": "따뜻한 촛불",
    "戊": "넓은 산",
    "己": "기름진 땅",
    "庚": "단단한 쇠",
    "辛": "정제된 보석",
    "壬": "큰 강",
    "癸": "맑은 이슬",
}


def get_theme_config(element: str) -> dict[str, Any]:
    """대표 오행(木火土金水) UI 테마 설정."""
    return dict(THEME_CONFIG.get(str(element or ""), _THEME_DEFAULT))


def element_theme_slug(element_or_slug: str) -> str:
    """``木`` 또는 ``wood`` → CSS ``data-theme`` 슬러그."""
    raw = str(element_or_slug or "").strip()
    if raw in _THEME_KEY_SLUG:
        return _THEME_KEY_SLUG[raw]
    if raw in _THEME_KEY_SLUG.values():
        return raw
    if "_" in raw:
        head = raw.split("_", 1)[0]
        if head in _THEME_KEY_SLUG.values():
            return head
    return "earth"


def element_theme_css_block() -> str:
    """``[data-theme="wood"]`` 등 오행별 CSS 변수 (--primary, --gradient)."""
    chunks: list[str] = [
        "/* saju element themes — THEME_CONFIG */",
    ]
    for el, slug in _THEME_KEY_SLUG.items():
        cfg = THEME_CONFIG.get(el, _THEME_DEFAULT)
        primary = str(cfg.get("accent") or "#d4af37")
        soft = str(
            cfg.get("primary_soft") or ELEMENT_COLORS.get(el, {}).get("soft", "#fef3c7")
        )
        grad = str(
            cfg.get("gradient_css") or f"linear-gradient(135deg, {primary}, {primary})"
        )
        chunks.append(
            f'[data-theme="{slug}"] {{\n'
            f"  --primary: {primary};\n"
            f"  --primary-soft: {soft};\n"
            f"  --gradient: {grad};\n"
            f"  --saju-theme-primary: {primary};\n"
            f"  --saju-theme-primary-soft: {soft};\n"
            f"  --saju-theme-gradient: {grad};\n"
            f"}}"
        )
    chunks.append("""
[data-theme] .saju-theme-accent { color: var(--primary); }
[data-theme] .saju-theme-soft-bg { background: var(--primary-soft); }
[data-theme] .saju-theme-gradient-bar {
  background: var(--gradient);
  border-radius: 6px;
}
[data-theme] .saju-step3-life-core-h.saju-theme-accent {
  color: var(--primary);
  border-bottom: 2px solid var(--primary);
}
""")
    return "\n".join(chunks)


def get_theme_key(dominant_element: str, day_stem: str) -> str:
    """CSS/테마 식별자 (예: ``wood_甲``)."""
    slug = _THEME_KEY_SLUG.get(str(dominant_element or ""), "earth")
    stem = str(day_stem or "").strip()
    return f"{slug}_{stem}" if stem else slug


def get_theme_emoji(dominant_element: str, day_stem: str) -> str:
    """대표 오행 + 일간 보조 이모지."""
    base = str(get_theme_config(dominant_element).get("emoji") or "☯️")
    stem_extra = {
        "甲": "🌱",
        "乙": "🍃",
        "丙": "☀️",
        "丁": "🕯️",
        "戊": "⛰️",
        "己": "🌾",
        "庚": "⚔️",
        "辛": "💎",
        "壬": "🌊",
        "癸": "💦",
    }.get(str(day_stem or ""), "")
    return f"{base}{stem_extra}" if stem_extra else base


def get_saju_nickname(dominant_element: str, day_stem: str) -> str:
    """오행·일간 조합 별칭."""
    el_nick = str(get_theme_config(dominant_element).get("name") or "균형기운")
    stem_nick = _STEM_NICKNAME.get(str(day_stem or ""), "")
    if stem_nick:
        return f"{el_nick} · {stem_nick}"
    return el_nick


def get_theme_vibe(dominant_element: str) -> str:
    """대표 오행 한 줄 무드."""
    return str(get_theme_config(dominant_element).get("vibe") or "균형과 조화의 기운")


def build_saju_theme_meta(gapja: list[str]) -> dict[str, Any]:
    """간지 메타 + UI 테마(색·별칭·무드)를 한 번에 반환."""
    meta = build_gapja_design_meta(gapja)

    pillars = [str(x or "") for x in list(gapja or [])[:4]]
    day_stem = (
        pillars[2][0]
        if len(pillars) > 2 and len(pillars[2]) >= 1
        else str(meta.get("day_stem") or "")
    )

    element_counts = meta.get("element_counts")
    if not isinstance(element_counts, dict) or not element_counts:
        element_counts = {el: 0 for el in ("木", "火", "土", "金", "水")}

    day_element = STEM_ELEMENT.get(day_stem, "木")

    def _count_score(el: str) -> tuple[int, int]:
        """(점수, 일간 오행 일치 시 우선)"""
        return (int(element_counts.get(el, 0) or 0), 1 if el == day_element else 0)

    dominant_element = max(element_counts, key=_count_score)
    day_polarity = STEM_YIN_YANG.get(day_stem, "양")
    palette = ELEMENT_COLORS.get(dominant_element, ELEMENT_COLORS["土"])
    cfg = get_theme_config(dominant_element)

    theme = {
        "dominant_element": dominant_element,
        "day_stem": day_stem,
        "day_element": day_element,
        "day_polarity": day_polarity,
        "primary_color": str(cfg.get("accent") or palette.get("color", "#D4AF37")),
        "soft_color": palette.get("soft", "#FEF3C7"),
        "theme_key": element_theme_slug(dominant_element),
        "theme_id": get_theme_key(dominant_element, day_stem),
        "emoji": get_theme_emoji(dominant_element, day_stem),
        "nickname": get_saju_nickname(dominant_element, day_stem),
        "vibe": get_theme_vibe(dominant_element),
        "name": cfg.get("name"),
        "gradient": cfg.get("gradient"),
        "accent": cfg.get("accent"),
        "primary_soft": cfg.get("primary_soft"),
        "gradient_css": cfg.get("gradient_css"),
        "bg_pattern": cfg.get("bg_pattern"),
        "font_weight": cfg.get("font_weight"),
        "slug": element_theme_slug(dominant_element),
    }
    return {**meta, "theme": theme, "theme_config": cfg}


def _read_archive_payloads_pandas(
    conn: sqlite3.Connection, sql: str, params: tuple[Any, ...]
) -> list[str]:
    try:
        import pandas as pd
    except ImportError:
        cur = conn.execute(sql, params)
        return [str(r[0]) for r in cur.fetchall() if r and r[0] is not None]
    df = pd.read_sql_query(sql, conn, params=params)
    if df is None or df.empty or "payload_json" not in df.columns:
        return []
    return [
        str(x) for x in df["payload_json"].tolist() if x is not None and str(x) != ""
    ]


# ---------------------------------------------------------------------------
# session_id 검증 (UUID v4 — 하이픈 유무 모두 허용, 저장은 32자 hex)
# ---------------------------------------------------------------------------

_SESSION_ID_MAX_LEN = 36
_SESSION_ID_WHITELIST_RE = re.compile(r"^[0-9a-fA-F\-]+$")
_SESSION_ID_UUID4_HYPHEN_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
_SESSION_ID_UUID4_HEX32_RE = re.compile(
    r"^[0-9a-f]{12}4[0-9a-f]{3}[89ab][0-9a-f]{3}[0-9a-f]{12}$",
    re.IGNORECASE,
)


class InvalidSessionIdError(ValueError):
    """``session_id`` 가 UUID v4 화이트리스트·길이 규칙을 만족하지 않을 때."""


def normalize_session_id(
    session_id: str | None, *, required: bool = True
) -> str | None:
    """``session_id`` 를 검증하고 소문자 32자 hex(UUID v4)로 정규화합니다."""
    raw = str(session_id or "").strip()
    if not raw:
        if required:
            raise InvalidSessionIdError("session_id is empty")
        return None
    if len(raw) > _SESSION_ID_MAX_LEN:
        raise InvalidSessionIdError(
            f"session_id exceeds maximum length ({_SESSION_ID_MAX_LEN})"
        )
    if not _SESSION_ID_WHITELIST_RE.match(raw):
        raise InvalidSessionIdError("session_id contains disallowed characters")
    lowered = raw.lower()
    if _SESSION_ID_UUID4_HYPHEN_RE.match(lowered):
        hex32 = lowered.replace("-", "")
    elif _SESSION_ID_UUID4_HEX32_RE.match(lowered):
        hex32 = lowered
    else:
        raise InvalidSessionIdError("session_id must be UUID version 4")
    return hex32


def coalesce_session_id(session_id: str | None) -> str | None:
    """검증 실패 시 None 반환(로그만 남김). 읽기·삭제·잘못된 입력 방어용."""
    try:
        return normalize_session_id(session_id, required=True)
    except InvalidSessionIdError as exc:
        log.warning("Rejected invalid session_id %r: %s", session_id, exc)
        return None


# ---------------------------------------------------------------------------
# 아카이브 payload — XSS·인젝션 위험 문자 정리 (저장 전)
# ---------------------------------------------------------------------------

_ARCHIVE_CONTENT_MAX_LEN = 16_000
_ARCHIVE_SHORT_TEXT_MAX_LEN = 512
_ARCHIVE_CTRL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_ARCHIVE_SCRIPT_TAG_RE = re.compile(
    r"<\s*/?\s*(?:script|style|iframe|object|embed|link|meta)\b[^>]*>",
    re.IGNORECASE,
)
_ARCHIVE_ANY_TAG_RE = re.compile(r"<[^>]+>")
_ARCHIVE_URI_SCHEME_RE = re.compile(r"(?i)\b(?:javascript|vbscript|data)\s*:")
_ARCHIVE_EVENT_HANDLER_RE = re.compile(r"(?i)\bon[a-z]+\s*=")
_ARCHIVE_ROLE_WHITELIST = frozenset({"user", "assistant", "admin", "system", ""})


def _archive_scalar_to_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, _dt.datetime):
        return value.isoformat(timespec="seconds")
    if isinstance(value, _dt.date):
        return value.isoformat()
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8", errors="replace")
        except Exception:
            return ""
    return str(value)


def sanitize_archive_text(
    value: Any, *, max_len: int = _ARCHIVE_CONTENT_MAX_LEN
) -> str:
    """사용자 입력 등 문자열을 아카이브 JSON에 넣기 전 정리합니다."""
    s = _archive_scalar_to_str(value)
    s = s.replace("\x00", "")
    s = _ARCHIVE_CTRL_CHARS_RE.sub("", s)
    s = _ARCHIVE_SCRIPT_TAG_RE.sub("", s)
    s = _ARCHIVE_URI_SCHEME_RE.sub("", s)
    s = _ARCHIVE_EVENT_HANDLER_RE.sub("", s)
    s = _ARCHIVE_ANY_TAG_RE.sub("", s)
    s = html.escape(s, quote=True)
    limit = max(1, int(max_len))
    if len(s) > limit:
        s = s[:limit] + "\u2026"
    return s


def sanitize_archive_record(record: dict[str, Any] | None) -> dict[str, Any]:
    """아카이브 행 dict의 문자열 필드를 재귀적으로 정리합니다. ``session_id``는 제외."""
    if not isinstance(record, dict):
        return {}
    out: dict[str, Any] = {}
    for key, val in record.items():
        k = str(key)
        if k == "session_id":
            continue
        if isinstance(val, bool):
            out[k] = bool(val)
            continue
        if isinstance(val, (int, float)) and k not in ("msg_index",):
            out[k] = val
            continue
        if isinstance(val, dict):
            out[k] = sanitize_archive_record(val)
            continue
        if isinstance(val, list):
            cleaned: list[Any] = []
            for item in val:
                if isinstance(item, dict):
                    cleaned.append(sanitize_archive_record(item))
                elif isinstance(item, (str, bytes)) or item is not None:
                    cleaned.append(sanitize_archive_text(item))
                else:
                    cleaned.append(item)
            out[k] = cleaned
            continue
        if k == "role":
            role = sanitize_archive_text(val, max_len=64).lower()
            out[k] = role if role in _ARCHIVE_ROLE_WHITELIST else "user"
            continue
        if k in ("u_name", "contact", "room_key", "consultation_type", "ts"):
            out[k] = sanitize_archive_text(val, max_len=_ARCHIVE_SHORT_TEXT_MAX_LEN)
            continue
        if k in ("content", "msg"):
            out[k] = sanitize_archive_text(val, max_len=_ARCHIVE_CONTENT_MAX_LEN)
            continue
        if (
            isinstance(val, (str, bytes))
            or isinstance(val, (_dt.datetime, _dt.date))
            or val is not None
        ):
            out[k] = sanitize_archive_text(val)
        else:
            out[k] = val
    return out


# ---------------------------------------------------------------------------
# 설정
# ---------------------------------------------------------------------------

# 재진입 가능: 통합 API가 sqlite_* 를 연쇄 호출해도 데드락 방지.
_storage_rlock = threading.RLock()
# 구버전·핫리로드 캐시가 ``_storage_lock`` 이름을 참조할 때 NameError 방지.
_storage_lock = _storage_rlock
_sqlite_bootstrap_lock = threading.Lock()
_sqlite_bootstrapped = False
_sqlite_thread_conns: dict[int, sqlite3.Connection] = {}
_sqlite_thread_conns_lock = threading.Lock()

# Redis 아카이브 레거시 LIST → v2 이관은 클라이언트 최초 생성 시 1회(싱글톤 락 안에서 완료).
_redis_migrated = False

# Redis 클라이언트는 프로세스당 하나만 생성(연결 풀 재사용).
_redis: Any = None
_redis_singleton_lock = threading.Lock()
_redis_fail_count = 0
_redis_backoff_until = 0.0
_redis_last_error = ""

# ---------------------------------------------------------------------------
# Redis — 키 네임스페이스·고정 키 (`room_key` 등 동적 부분은 아래 `_r_key_*` 헬퍼)
# ---------------------------------------------------------------------------
_NS = "saju:v1"
_ARCH_V2_MARKER = f"{_NS}:arch:v2_marker"
_ARCH_TIMELINE = f"{_NS}:arch:tl"
_ARCH_LEGACY_LIST = f"{_NS}:archive:lines"
_R_KEY_ROOM_INDEX = f"{_NS}:room_keys"
_R_KEY_UPROF_TL = f"{_NS}:uprof:tl"

# Redis 채팅 방 TTL: 미설정 기본 14일(7~30일 권장). ``0`` 만 명시적 영구 보관.
_DEFAULT_REDIS_ROOM_TTL_SEC = 14 * 24 * 3600
_MAX_REDIS_ROOM_TTL_SEC = 90 * 24 * 3600


def _r_key_uprof(fp: str) -> str:
    return f"{_NS}:uprof:p:{str(fp or '').strip()}"


def _birth_fingerprint_facets(birth: dict[str, Any]) -> dict[str, Any]:
    """fingerprint용 생일·시간 요소를 정규화합니다."""
    if not isinstance(birth, dict):
        birth = {}
    enriched = _birth_with_time_adjustment_meta(birth)
    return {
        "y": int(enriched.get("year", 0) or 0),
        "m": int(enriched.get("month", 0) or 0),
        "d": int(enriched.get("day", 0) or 0),
        "time_str": str(enriched.get("time_str", "") or "").strip(),
        "lunar": bool(enriched.get("lunar", False)),
        "leap_month": bool(enriched.get("leap_month", False)),
    }


def user_profile_fingerprint(*, display_name: str, birth: dict[str, Any]) -> str:
    """이름·생일·시간으로 프로필 키(sha256 hex)를 만듭니다."""
    name_n = str(display_name or "").strip().lower()
    stable = {
        "name": name_n,
        **_birth_fingerprint_facets(birth),
    }
    raw = json.dumps(stable, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


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


def _birth_with_time_adjustment_meta(birth: dict[str, Any]) -> dict[str, Any]:
    """upsert 직전에 birth_json에서 구(舊) 시각 보정 메타를 제거합니다."""
    if not isinstance(birth, dict):
        return {}
    out = dict(birth)
    for key in _LEGACY_BIRTH_META_KEYS:
        out.pop(key, None)
    return out


def _app_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _redis_enabled() -> bool:
    return (os.environ.get("SAJU_STORAGE") or "sqlite").strip().lower() == "redis"


def _redis_timeout(name: str, default: float) -> float:
    try:
        return max(0.2, float((os.environ.get(name) or str(default)).strip()))
    except ValueError:
        return default


def _redis_note_success() -> None:
    global _redis_fail_count, _redis_backoff_until, _redis_last_error
    _redis_fail_count = 0
    _redis_backoff_until = 0.0
    _redis_last_error = ""


def _redis_note_failure(exc: BaseException | str) -> None:
    """Redis 장애를 기록하고 짧은 exponential backoff 동안 재시도를 멈춥니다."""
    global _redis, _redis_fail_count, _redis_backoff_until, _redis_last_error
    _redis = None
    _redis_fail_count = min(_redis_fail_count + 1, 8)
    base = _redis_timeout("SAJU_REDIS_BACKOFF_BASE_SEC", 0.5)
    cap = _redis_timeout("SAJU_REDIS_BACKOFF_MAX_SEC", 30.0)
    delay = min(cap, base * (2 ** max(0, _redis_fail_count - 1)))
    _redis_backoff_until = time.time() + delay
    _redis_last_error = str(exc)
    log.warning("Redis unavailable; falling back to SQLite for %.1fs: %s", delay, exc)


def redis_fault_state() -> dict[str, Any]:
    """관리/디버그용 Redis 장애 상태."""
    remain = max(0.0, _redis_backoff_until - time.time())
    return {
        "enabled": _redis_enabled(),
        "healthy": _redis is not None and remain <= 0.0,
        "fail_count": int(_redis_fail_count),
        "backoff_remaining_sec": round(remain, 2),
        "last_error": _redis_last_error,
    }


_T = TypeVar("_T")


def _redis_read_fallback(
    sqlite_result: _T,
    redis_call: Callable[[], _T],
    *,
    prefer_redis_when: Callable[[_T], bool] | None = None,
) -> _T:
    """읽기: SQLite를 기본으로 두고 Redis는 보조. Redis 실패 시 ``sqlite_result`` 로 복귀."""
    if not _redis_enabled():
        return sqlite_result
    try:
        redis_result = redis_call()
    except Exception as e:
        _redis_note_failure(e)
        return sqlite_result
    if prefer_redis_when is not None:
        if prefer_redis_when(redis_result):
            return redis_result
        return sqlite_result
    if redis_result:
        return redis_result
    return sqlite_result


def storage_backend() -> str:
    # SQLite를 앱의 안전 저장소로 사용합니다. Redis는 연결 가능할 때만 미러/가속 경로로 붙습니다.
    return "sqlite+redis" if _redis_enabled() and _redis_client() else "sqlite"


def _sqlite_path() -> str:
    p = (os.environ.get("SAJU_SQLITE_PATH") or "").strip()
    if p:
        return p
    return os.path.join(_app_dir(), "saju_app.db")


def _get_redis():
    """``REDIS_URL`` 기준 Redis 클라이언트를 한 번만 만들고 재사용합니다.

    최초 연결 직후(다른 스레드가 같은 클라이언트를 보기 전) 아카이브 v2 마이그레이션을
    한 번만 수행합니다.
    """
    global _redis, _redis_migrated
    if not _redis_enabled():
        return None
    if _redis_backoff_until > time.time():
        return None
    if _redis is not None:
        return _redis
    with _redis_singleton_lock:
        if _redis_backoff_until > time.time():
            return None
        if _redis is not None:
            return _redis
        url = (os.environ.get("REDIS_URL") or "").strip()
        if not url:
            return None
        try:
            import redis

            _redis = redis.from_url(
                url,
                decode_responses=True,
                socket_connect_timeout=_redis_timeout(
                    "SAJU_REDIS_CONNECT_TIMEOUT_SEC", 1.5
                ),
                socket_timeout=_redis_timeout("SAJU_REDIS_SOCKET_TIMEOUT_SEC", 2.0),
                health_check_interval=30,
                retry_on_timeout=True,
            )
            _redis.ping()
            _redis_note_success()
        except Exception as e:
            _redis_note_failure(e)
            return None
        if _redis is not None and not _redis_migrated:
            try:
                _redis_archive_migrate_legacy_if_needed(_redis)
            except Exception:
                log.exception("Redis archive legacy migration failed on connect")
                _redis_note_failure("Redis archive migration failed")
                return None
            _redis_migrated = True
        return _redis


def _redis_client():
    """기존 호출부 호환 이름. 실제 클라이언트는 ``_get_redis()``에서 캐시합니다."""
    return _get_redis()


def redis_room_ttl_sec() -> int:
    """Redis 채팅 방 ``messages``/``label`` 키 TTL(초). 미설정=14일, ``0``=영구."""
    raw = (os.environ.get("SAJU_REDIS_ROOM_TTL_SEC") or "").strip()
    if raw == "":
        return _DEFAULT_REDIS_ROOM_TTL_SEC
    try:
        value = int(raw)
    except ValueError:
        log.warning("Invalid SAJU_REDIS_ROOM_TTL_SEC=%r; using default", raw)
        return _DEFAULT_REDIS_ROOM_TTL_SEC
    if value < 0:
        return _DEFAULT_REDIS_ROOM_TTL_SEC
    if value == 0:
        return 0
    return min(value, _MAX_REDIS_ROOM_TTL_SEC)


def _format_ttl_human(seconds: int) -> str:
    if seconds <= 0:
        return "만료 없음(영구)"
    days, rem = divmod(int(seconds), 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    parts: list[str] = []
    if days:
        parts.append(f"{days}일")
    if hours:
        parts.append(f"{hours}시간")
    if minutes or not parts:
        parts.append(f"{minutes}분")
    return " ".join(parts)


def redis_room_ttl_monitor(*, sample_limit: int = 40) -> dict[str, Any]:
    """관리자용: 설정 TTL·방별 남은 TTL 샘플."""
    configured = redis_room_ttl_sec()
    lim = max(1, min(int(sample_limit), 200))
    out: dict[str, Any] = {
        "configured_ttl_sec": configured,
        "configured_ttl_human": _format_ttl_human(configured),
        "permanent_storage": configured <= 0,
        "default_if_unset_sec": _DEFAULT_REDIS_ROOM_TTL_SEC,
        "redis_enabled": _redis_enabled(),
        "redis_connected": False,
        "room_index_size": 0,
        "rooms_without_ttl": 0,
        "rooms_with_ttl": 0,
        "rooms_missing_keys": 0,
        "sample": [],
    }
    r = _redis_client()
    if not r:
        return out
    out["redis_connected"] = True
    try:
        room_keys = sorted(
            (str(k) for k in (r.smembers(_R_KEY_ROOM_INDEX) or [])), reverse=True
        )
        out["room_index_size"] = len(room_keys)
        sample_rows: list[dict[str, Any]] = []
        for rk in room_keys[:lim]:
            msg_key = _r_key_room_msgs(rk)
            label_key = _r_key_room_label(rk)
            msg_ttl = int(r.ttl(msg_key))
            label_ttl = int(r.ttl(label_key))
            if msg_ttl == -2:
                out["rooms_missing_keys"] += 1
            elif msg_ttl == -1:
                out["rooms_without_ttl"] += 1
            elif msg_ttl >= 0:
                out["rooms_with_ttl"] += 1
            sample_rows.append(
                {
                    "room_key": rk,
                    "msg_ttl_sec": msg_ttl,
                    "msg_ttl_human": (
                        _format_ttl_human(msg_ttl)
                        if msg_ttl > 0
                        else ("만료 없음" if msg_ttl == -1 else "키 없음")
                    ),
                    "label_ttl_sec": label_ttl,
                }
            )
        out["sample"] = sample_rows
        try:
            info = r.info("memory") or {}
            out["redis_used_memory_human"] = str(info.get("used_memory_human") or "")
        except Exception:
            pass
    except Exception as exc:
        out["error"] = str(exc)
        log.warning("redis_room_ttl_monitor failed: %s", exc)
    return out


def get_config() -> dict[str, Any]:
    """스토리지 관련 환경·경로를 한 곳에서 읽습니다."""
    redis_ttl = redis_room_ttl_sec()
    return {
        "storage": storage_backend(),
        "sqlite_path": _sqlite_path(),
        "sqlite": sqlite_connection_diagnostics(),
        "redis_ttl": redis_ttl,
        "redis_ttl_human": _format_ttl_human(redis_ttl),
        "redis_ttl_permanent": redis_ttl <= 0,
        "redis_fault": redis_fault_state(),
        "app_dir": _app_dir(),
    }


# ---------------------------------------------------------------------------
# SQLite 스키마
# ---------------------------------------------------------------------------

_SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS chat_room (
    room_key TEXT PRIMARY KEY,
    messages_json TEXT NOT NULL DEFAULT '[]',
    label_json TEXT,
    updated_at TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS kv (
    k TEXT PRIMARY KEY,
    v TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS chat_archive (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL DEFAULT '',
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_chat_archive_session ON chat_archive(session_id);
CREATE INDEX IF NOT EXISTS idx_archive_created ON chat_archive(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_archive_session_created ON chat_archive(session_id, created_at);
CREATE TABLE IF NOT EXISTS global_chat_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_ts TEXT NOT NULL DEFAULT '',
    room_key TEXT NOT NULL DEFAULT '',
    u_name TEXT NOT NULL DEFAULT '',
    contact TEXT NOT NULL DEFAULT '',
    msg_index INTEGER NOT NULL DEFAULT 0,
    role TEXT NOT NULL DEFAULT '',
    msg TEXT NOT NULL DEFAULT '',
    is_manual INTEGER NOT NULL DEFAULT 0
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_global_chat_log_room_msg ON global_chat_log(room_key, msg_index);
CREATE INDEX IF NOT EXISTS idx_global_chat_log_id ON global_chat_log(id);
CREATE TABLE IF NOT EXISTS user_profiles (
    fingerprint TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    birth_json TEXT NOT NULL,
    gapja_json TEXT NOT NULL,
    gapja_meta_json TEXT NOT NULL DEFAULT '{}',
    summer_time INTEGER NOT NULL DEFAULT 0,
    view_count INTEGER NOT NULL DEFAULT 0,
    last_consulted_at TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT ''
);
"""


def _sqlite_busy_timeout_ms() -> int:
    try:
        return max(
            1000,
            int((os.environ.get("SAJU_SQLITE_BUSY_TIMEOUT_MS") or "30000").strip()),
        )
    except ValueError:
        return 30000


def _sqlite_connect() -> sqlite3.Connection:
    """스레드 전용 연결(``check_same_thread=True`` 기본). WAL + busy_timeout."""
    busy_ms = _sqlite_busy_timeout_ms()
    conn = sqlite3.connect(
        _sqlite_path(),
        timeout=busy_ms / 1000.0,
        check_same_thread=True,
    )
    conn.row_factory = sqlite3.Row
    conn.execute(f"PRAGMA busy_timeout={busy_ms};")
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def _sqlite_ensure_bootstrapped(conn: sqlite3.Connection) -> None:
    """스키마·레거시 JSON 이관 — 프로세스당 1회."""
    global _sqlite_bootstrapped
    if _sqlite_bootstrapped:
        return
    with _sqlite_bootstrap_lock:
        if _sqlite_bootstrapped:
            return
        _sqlite_init(conn)
        _migrate_json_files_to_sqlite_once(conn, _app_dir())
        _sqlite_bootstrapped = True


def _sqlite_acquire_connection() -> sqlite3.Connection:
    """현재 스레드용 SQLite 연결(없으면 생성·부트스트랩)."""
    tid = threading.get_ident()
    with _sqlite_thread_conns_lock:
        conn = _sqlite_thread_conns.get(tid)
        if conn is None:
            conn = _sqlite_connect()
            _sqlite_ensure_bootstrapped(conn)
            _sqlite_thread_conns[tid] = conn
        return conn


def _sqlite_release_all_connections() -> None:
    with _sqlite_thread_conns_lock:
        for conn in _sqlite_thread_conns.values():
            try:
                conn.close()
            except Exception:
                pass
        _sqlite_thread_conns.clear()


def sqlite_connection_diagnostics() -> dict[str, Any]:
    """운영·디버그: 스레드별 연결 수·부트스트랩 여부."""
    with _sqlite_thread_conns_lock:
        n_conns = len(_sqlite_thread_conns)
    return {
        "wal": True,
        "thread_local_connections": n_conns,
        "bootstrapped": bool(_sqlite_bootstrapped),
        "serialize_writes": True,
        "lock": "RLock",
        "busy_timeout_ms": _sqlite_busy_timeout_ms(),
    }


atexit.register(_sqlite_release_all_connections)


def _sqlite_init(conn: sqlite3.Connection) -> None:
    conn.executescript(_SQLITE_SCHEMA)
    conn.commit()
    _ensure_chat_archive_session_column(conn)
    _ensure_global_chat_log_table(conn)
    _ensure_user_profiles_gapja_meta_column(conn)
    _ensure_user_profiles_usage_columns(conn)
    _ensure_user_profiles_revisit_pin_column(conn)


def _ensure_user_profiles_revisit_pin_column(conn: sqlite3.Connection) -> None:
    """재방문 전용 비밀번호 해시(평문 저장 없음)."""
    try:
        cols = {
            row[1]
            for row in conn.execute("PRAGMA table_info(user_profiles)").fetchall()
        }
    except Exception:
        cols = set()
    try:
        if "revisit_pin_hash" not in cols:
            conn.execute(
                "ALTER TABLE user_profiles ADD COLUMN revisit_pin_hash TEXT NOT NULL DEFAULT ''"
            )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_user_profiles_revisit_pin "
            "ON user_profiles(revisit_pin_hash) WHERE revisit_pin_hash != ''"
        )
        conn.commit()
    except Exception:
        log.exception("user_profiles revisit_pin_hash column ensure failed")


def _ensure_chat_archive_session_column(conn: sqlite3.Connection) -> None:
    """기존 DB(`chat_archive`에 `session_id` 없음)에 컬럼·인덱스 추가 및 payload에서 백필.

    예전 스키마는 `id` 대신 `rowid`만 있을 수 있어, 백필은 ``rowid`` 기준으로 합니다.
    ``ALTER`` 실패를 무시하면 이후 ``INSERT ... session_id`` 가 계속 깨지므로 로그를 남깁니다.
    """
    try:
        exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='chat_archive'"
        ).fetchone()
    except Exception:
        return
    if not exists:
        return
    try:
        cols = {
            row[1] for row in conn.execute("PRAGMA table_info(chat_archive)").fetchall()
        }
    except Exception:
        return
    if not cols:
        return
    if "session_id" not in cols:
        try:
            conn.execute(
                "ALTER TABLE chat_archive ADD COLUMN session_id TEXT NOT NULL DEFAULT ''"
            )
            conn.commit()
        except sqlite3.OperationalError as e:
            em = str(e).lower()
            if "duplicate column" not in em:
                log.warning(
                    "chat_archive: session_id 컬럼 추가 실패(수동으로 DB를 점검하세요): %s",
                    e,
                )
        try:
            cols = {
                row[1]
                for row in conn.execute("PRAGMA table_info(chat_archive)").fetchall()
            }
        except Exception:
            cols = set()
        if "session_id" not in cols:
            log.error(
                "chat_archive 테이블에 session_id 컬럼이 없습니다. "
                "앱을 종료한 뒤 DB 백업 후 "
                "`ALTER TABLE chat_archive ADD COLUMN session_id TEXT NOT NULL DEFAULT '';` "
                "를 실행하거나 새 DB 파일로 시작하세요."
            )
            return
        for row in conn.execute("SELECT rowid, payload_json FROM chat_archive"):
            try:
                obj = json.loads(row[1])
                sid = str(obj.get("session_id") or "").strip()
                conn.execute(
                    "UPDATE chat_archive SET session_id = ? WHERE rowid = ?",
                    (sid, int(row[0])),
                )
            except Exception:
                continue
        conn.commit()
    try:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_chat_archive_session ON chat_archive(session_id)"
        )
        conn.commit()
    except Exception:
        log.exception("chat_archive session index ensure failed")
    try:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_chat_archive_session_created "
            "ON chat_archive(session_id, created_at)"
        )
        conn.commit()
    except Exception:
        log.exception("chat_archive session/created index ensure failed")


def _ensure_global_chat_log_table(conn: sqlite3.Connection) -> None:
    """관리자 공용 타임라인을 대형 KV JSON 대신 append-only 테이블로 유지합니다."""
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS global_chat_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_ts TEXT NOT NULL DEFAULT '',
                room_key TEXT NOT NULL DEFAULT '',
                u_name TEXT NOT NULL DEFAULT '',
                contact TEXT NOT NULL DEFAULT '',
                msg_index INTEGER NOT NULL DEFAULT 0,
                role TEXT NOT NULL DEFAULT '',
                msg TEXT NOT NULL DEFAULT '',
                is_manual INTEGER NOT NULL DEFAULT 0
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_global_chat_log_room_msg
                ON global_chat_log(room_key, msg_index);
            CREATE INDEX IF NOT EXISTS idx_global_chat_log_id ON global_chat_log(id);
            """)
        conn.commit()
    except Exception:
        log.exception("global_chat_log table ensure failed")


def _ensure_user_profiles_usage_columns(conn: sqlite3.Connection) -> None:
    """프로필 목록 UX용 조회수/최근 상담일 컬럼을 기존 DB에 추가합니다."""
    try:
        cols = {
            row[1]
            for row in conn.execute("PRAGMA table_info(user_profiles)").fetchall()
        }
    except Exception:
        cols = set()
    try:
        if "view_count" not in cols:
            conn.execute(
                "ALTER TABLE user_profiles ADD COLUMN view_count INTEGER NOT NULL DEFAULT 0"
            )
        if "last_consulted_at" not in cols:
            conn.execute(
                "ALTER TABLE user_profiles ADD COLUMN last_consulted_at TEXT NOT NULL DEFAULT ''"
            )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_user_profiles_last_consulted "
            "ON user_profiles(last_consulted_at)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_user_profiles_updated ON user_profiles(updated_at)"
        )
        conn.commit()
    except Exception:
        log.exception("user_profiles usage columns ensure failed")


def _ensure_user_profiles_gapja_meta_column(conn: sqlite3.Connection) -> None:
    """기존 프로필 DB에 디자인용 간지 메타데이터 컬럼을 추가합니다."""
    try:
        cols = {
            row[1]
            for row in conn.execute("PRAGMA table_info(user_profiles)").fetchall()
        }
    except Exception:
        cols = set()
    try:
        if "gapja_meta_json" not in cols:
            conn.execute(
                "ALTER TABLE user_profiles ADD COLUMN gapja_meta_json TEXT NOT NULL DEFAULT '{}'"
            )
        conn.commit()
    except Exception:
        log.exception("user_profiles gapja_meta_json column ensure failed")


def _migrate_json_files_to_sqlite(conn: sqlite3.Connection, app_dir: str) -> None:
    """레거시 JSON/JSONL 파일이 있으면 SQLite로 한 번 이관(멱등)."""
    bus_path = os.path.join(app_dir, "step11_shared_chat_bus.json")
    if os.path.isfile(bus_path):
        try:
            with open(bus_path, encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d, dict):
                rooms = d.get("rooms") or {}
                labels = d.get("labels") or {}
                if isinstance(rooms, dict):
                    for rk, msgs in rooms.items():
                        if not rk or not isinstance(msgs, list):
                            continue
                        lab = labels.get(rk) if isinstance(labels, dict) else None
                        conn.execute(
                            "INSERT OR REPLACE INTO chat_room(room_key, messages_json, label_json, updated_at) VALUES (?,?,?,?)",
                            (
                                str(rk),
                                json.dumps(msgs, ensure_ascii=False, default=str),
                                (
                                    json.dumps(lab, ensure_ascii=False, default=str)
                                    if lab is not None
                                    else None
                                ),
                                "",
                            ),
                        )
        except Exception:
            pass

    pre_path = os.path.join(app_dir, "step2_form_prefill.json")
    if os.path.isfile(pre_path):
        try:
            os.remove(pre_path)
        except OSError:
            pass
        try:
            conn.execute("DELETE FROM kv WHERE k = ?", ("step2_prefill",))
        except Exception:
            pass

    arch_path = os.path.join(app_dir, "consultation_chat_archive.jsonl")
    if os.path.isfile(arch_path):
        try:
            _ensure_chat_archive_session_column(conn)
            with open(arch_path, encoding="utf-8") as f:
                for ln in f:
                    ln = ln.strip()
                    if not ln:
                        continue
                    try:
                        obj = json.loads(ln)
                    except Exception:
                        continue
                    sid = str(obj.get("session_id") or "").strip()
                    conn.execute(
                        "INSERT INTO chat_archive(session_id, payload_json, created_at) VALUES (?,?,?)",
                        (sid, ln, str(obj.get("ts") or "")),
                    )
        except Exception:
            pass

    out_path = os.path.join(app_dir, "step12_admin_reply_outbox.json")
    if os.path.isfile(out_path):
        try:
            with open(out_path, encoding="utf-8") as f:
                raw = f.read()
            conn.execute(
                "INSERT OR REPLACE INTO kv(k,v,updated_at) VALUES (?,?,?)",
                ("admin_outbox", raw, ""),
            )
        except Exception:
            pass

    conn.commit()


def _migrate_json_files_to_sqlite_once(conn: sqlite3.Connection, app_dir: str) -> None:
    row = conn.execute("SELECT 1 FROM kv WHERE k = ?", ("_storage_v1_init",)).fetchone()
    if row:
        return
    _migrate_json_files_to_sqlite(conn, app_dir)
    conn.execute(
        "INSERT OR REPLACE INTO kv(k, v, updated_at) VALUES (?,?,?)",
        ("_storage_v1_init", "1", ""),
    )
    conn.commit()


def _sqlite_try_commit(conn: sqlite3.Connection) -> None:
    """열린 트랜잭션이 있을 때만 commit(순수 조회 경로의 no-op commit 감소)."""
    if getattr(conn, "in_transaction", True):
        conn.commit()


def _with_sqlite(
    fn: Callable[Concatenate[sqlite3.Connection, P_sql], R_sql],
) -> Callable[P_sql, R_sql]:
    """스레드별 연결 재사용 + RLock 직렬화. 호출마다 connect/close 하지 않습니다."""

    @functools.wraps(fn)
    def wrapper(*args: P_sql.args, **kwargs: P_sql.kwargs) -> R_sql:
        with _storage_rlock:
            conn = _sqlite_acquire_connection()
            try:
                result = fn(conn, *args, **kwargs)
                _sqlite_try_commit(conn)
                return result
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass
                log.exception("SQLite storage: %s failed", fn.__qualname__)
                raise

    return wrapper


# ---------------------------------------------------------------------------
# SQLite 구현체
# ---------------------------------------------------------------------------


@_with_sqlite
def sqlite_load_bus_dict(conn) -> dict[str, Any]:
    rooms: dict[str, Any] = {}
    labels: dict[str, Any] = {}
    for row in conn.execute(
        "SELECT room_key, messages_json, label_json FROM chat_room"
    ):
        rk = str(row["room_key"])
        try:
            rooms[rk] = json.loads(row["messages_json"] or "[]")
        except Exception:
            rooms[rk] = []
        if row["label_json"]:
            try:
                labels[rk] = json.loads(row["label_json"])
            except Exception:
                labels[rk] = {}
    return {"rooms": rooms, "labels": labels}


@_with_sqlite
def sqlite_upsert_chat_room(
    conn, room_key: str, messages: list[Any], label: dict[str, Any] | None
) -> None:
    rk = str(room_key or "").strip()
    if not rk:
        return
    msg_json = json.dumps(messages or [], ensure_ascii=False, default=str)
    lab_json = (
        json.dumps(label, ensure_ascii=False, default=str)
        if label is not None
        else None
    )
    conn.execute(
        "INSERT OR REPLACE INTO chat_room(room_key, messages_json, label_json, updated_at) VALUES (?,?,?,?)",
        (rk, msg_json, lab_json, _now_kst_iso()),
    )
    conn.commit()


@_with_sqlite
def sqlite_get_chat_room(
    conn, room_key: str
) -> tuple[list[Any], dict[str, Any] | None]:
    rk = str(room_key or "").strip()
    if not rk:
        return [], None
    row = conn.execute(
        "SELECT messages_json, label_json FROM chat_room WHERE room_key = ?",
        (rk,),
    ).fetchone()
    if not row:
        return [], None
    try:
        msgs = json.loads(row["messages_json"] or "[]")
        if not isinstance(msgs, list):
            msgs = []
    except Exception:
        msgs = []
    lab = None
    if row["label_json"]:
        try:
            lab = json.loads(row["label_json"])
        except Exception:
            lab = None
    return msgs, lab


@_with_sqlite
def sqlite_list_room_keys(conn, limit: int = 500) -> list[str]:
    lim = max(1, min(int(limit), 2000))
    cur = conn.execute(
        "SELECT room_key FROM chat_room ORDER BY updated_at DESC, room_key ASC LIMIT ?",
        (lim,),
    )
    return [str(r[0]) for r in cur.fetchall() if r and r[0]]


@_with_sqlite
def sqlite_list_chat_room_summaries(conn, limit: int = 120) -> list[dict[str, Any]]:
    """관리자 UI용: 방 키·라벨·메시지 개수·갱신 시각(최근 순)."""
    lim = max(1, min(int(limit), 500))
    out: list[dict[str, Any]] = []
    for row in conn.execute(
        "SELECT room_key, label_json, messages_json, updated_at FROM chat_room "
        "ORDER BY updated_at DESC, room_key ASC LIMIT ?",
        (lim,),
    ):
        rk = str(row["room_key"])
        lab: dict[str, Any] | None = None
        if row["label_json"]:
            try:
                raw = json.loads(row["label_json"])
                lab = raw if isinstance(raw, dict) else None
            except Exception:
                lab = None
        u_name = str((lab or {}).get("u_name") or "")
        contact = str((lab or {}).get("contact") or "")
        user_gapja = str(
            (lab or {}).get("user_gapja") or (lab or {}).get("user_ilju") or ""
        )
        consultation_type = str((lab or {}).get("consultation_type") or "미분류")
        try:
            msgs = json.loads(row["messages_json"] or "[]")
            msg_count = len(msgs) if isinstance(msgs, list) else 0
        except Exception:
            msg_count = 0
        out.append(
            {
                "room_key": rk,
                "u_name": u_name,
                "contact": contact,
                "user_gapja": user_gapja,
                "consultation_type": consultation_type,
                "msg_count": msg_count,
                "updated_at": str(row["updated_at"] or ""),
            }
        )
    return out


@_with_sqlite
def sqlite_clear_chat_room(conn, room_key: str) -> None:
    rk = str(room_key or "").strip()
    if not rk:
        return
    conn.execute("DELETE FROM chat_room WHERE room_key = ?", (rk,))
    _ensure_global_chat_log_table(conn)
    conn.execute("DELETE FROM global_chat_log WHERE room_key = ?", (rk,))
    conn.commit()


@_with_sqlite
def sqlite_clear_all_chat_rooms(conn) -> tuple[int, int]:
    """모든 상담 방 + 공용 채팅 로그 행 삭제."""
    cur_room = conn.execute("DELETE FROM chat_room")
    _ensure_global_chat_log_table(conn)
    cur_log = conn.execute("DELETE FROM global_chat_log")
    conn.commit()
    return int(cur_room.rowcount or 0), int(cur_log.rowcount or 0)


@_with_sqlite
def sqlite_kvs_delete_prefix(conn, prefix: str) -> None:
    p = str(prefix or "").strip()
    if not p:
        return
    conn.execute("DELETE FROM kv WHERE k LIKE ?", (p + "%",))
    conn.commit()


@_with_sqlite
def sqlite_kvs_delete(conn, key: str) -> None:
    conn.execute("DELETE FROM kv WHERE k = ?", (key,))
    conn.commit()


@_with_sqlite
def sqlite_kvs_get(conn, key: str) -> str | None:
    row = conn.execute("SELECT v FROM kv WHERE k = ?", (key,)).fetchone()
    return str(row[0]) if row else None


@_with_sqlite
def sqlite_kvs_set(conn, key: str, value: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO kv(k, v, updated_at) VALUES (?,?,?)",
        (key, value, ""),
    )
    conn.commit()


@_with_sqlite
def sqlite_append_global_chat_log_events(
    conn,
    room_key: str,
    messages: list[Any],
    label: dict[str, Any] | None,
    *,
    cap: int = 5000,
) -> None:
    """공용 상담 타임라인을 메시지별 행으로 추가합니다."""
    rk = str(room_key or "").strip()
    if not rk:
        return
    msgs = list(messages or [])
    if not msgs:
        return
    _ensure_global_chat_log_table(conn)
    row = conn.execute(
        "SELECT MAX(msg_index) FROM global_chat_log WHERE room_key = ?",
        (rk,),
    ).fetchone()
    prev = int(row[0]) + 1 if row and row[0] is not None else 0
    if len(msgs) < prev:
        prev = 0
    tail = msgs[prev:]
    if not tail:
        return
    lab = label if isinstance(label, dict) else {}
    ts = _now_kst_iso()
    u_name = str(lab.get("u_name") or "")
    contact = _masked_contact(lab.get("contact") or "")
    rows: list[tuple[Any, ...]] = []
    for i, m in enumerate(tail, start=prev):
        if not isinstance(m, dict):
            continue
        rows.append(
            (
                ts,
                rk,
                u_name,
                contact,
                int(i),
                str(m.get("role") or ""),
                str(m.get("msg") or ""),
                1 if bool(m.get("is_manual", False)) else 0,
            )
        )
    if rows:
        conn.executemany(
            """
            INSERT OR REPLACE INTO global_chat_log(
                sync_ts, room_key, u_name, contact, msg_index, role, msg, is_manual
            ) VALUES (?,?,?,?,?,?,?,?)
            """,
            rows,
        )
        conn.execute(
            """
            DELETE FROM global_chat_log
            WHERE id NOT IN (
                SELECT id FROM global_chat_log ORDER BY id DESC LIMIT ?
            )
            """,
            (max(1, int(cap)),),
        )
        conn.commit()


@_with_sqlite
def sqlite_list_global_chat_log(conn, *, max_lines: int = 400) -> list[dict[str, Any]]:
    _ensure_global_chat_log_table(conn)
    n = max(1, min(int(max_lines), 2000))
    rows = conn.execute(
        """
        SELECT sync_ts, room_key, u_name, contact, msg_index, role, msg, is_manual
        FROM global_chat_log
        ORDER BY id DESC
        LIMIT ?
        """,
        (n,),
    ).fetchall()
    out: list[dict[str, Any]] = []
    for row in reversed(rows):
        out.append(
            {
                "sync_ts": str(row["sync_ts"] or ""),
                "room_key": str(row["room_key"] or ""),
                "u_name": str(row["u_name"] or ""),
                "contact": _masked_contact(row["contact"] or ""),
                "msg_index": int(row["msg_index"] or 0),
                "role": str(row["role"] or ""),
                "msg": str(row["msg"] or ""),
                "is_manual": bool(int(row["is_manual"] or 0)),
            }
        )
    return out


@_with_sqlite
def sqlite_archive_append(conn, record: dict[str, Any]) -> None:
    _ensure_chat_archive_session_column(conn)
    row = dict(record)
    if not str(row.get("ts") or "").strip():
        row["ts"] = _now_kst_iso()
    sid = coalesce_session_id(str(row.get("session_id") or ""))
    if not sid:
        log.warning("sqlite_archive_append skipped: invalid session_id")
        return
    row["session_id"] = sid
    line = json.dumps(row, ensure_ascii=False, default=str)
    ts = str(row.get("ts") or "")
    try:
        conn.execute(
            "INSERT INTO chat_archive(session_id, payload_json, created_at) VALUES (?,?,?)",
            (sid, line, ts),
        )
    except sqlite3.OperationalError as e1:
        em = str(e1).lower()
        if "session_id" in em or "no such column" in em:
            _ensure_chat_archive_session_column(conn)
            try:
                conn.execute(
                    "INSERT INTO chat_archive(session_id, payload_json, created_at) VALUES (?,?,?)",
                    (sid, line, ts),
                )
                conn.commit()
                return
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute(
                    "INSERT INTO chat_archive(payload_json, created_at) VALUES (?,?)",
                    (line, ts),
                )
                conn.commit()
                return
            except sqlite3.OperationalError as e2:
                log.exception("sqlite_archive_append: 레거시 2컬럼 INSERT도 실패")
                raise e1 from e2
        raise
    conn.commit()


@_with_sqlite
def sqlite_archive_load_recent(conn, max_rows: int) -> list[dict[str, Any]]:
    n = max(1, int(max_rows))
    sql = "SELECT payload_json FROM chat_archive ORDER BY id DESC LIMIT ?"
    raw_rows = _read_archive_payloads_pandas(conn, sql, (n,))
    raw_rows.reverse()
    return _parse_archive_payload_rows(raw_rows)


@_with_sqlite
def sqlite_archive_load_session(
    conn, session_id: str, max_rows: int
) -> list[dict[str, Any]]:
    sid = coalesce_session_id(session_id)
    if not sid:
        return []
    n = max(1, int(max_rows))
    sql = (
        "SELECT payload_json FROM chat_archive WHERE session_id = ? "
        "ORDER BY id DESC LIMIT ?"
    )
    raw_rows = _read_archive_payloads_pandas(conn, sql, (sid, n))
    raw_rows.reverse()
    return _parse_archive_payload_rows(raw_rows)


@_with_sqlite
def sqlite_archive_delete_session(conn, session_id: str) -> int:
    sid = coalesce_session_id(session_id)
    if not sid:
        return 0
    cur = conn.execute("DELETE FROM chat_archive WHERE session_id = ?", (sid,))
    conn.commit()
    return int(cur.rowcount or 0)


@_with_sqlite
def sqlite_archive_prune_before(
    conn, cutoff_iso: str, *, batch_size: int = 2000
) -> int:
    """``created_at``(ISO, KST)가 ``cutoff_iso`` 보다 오래된 행을 배치로 삭제합니다."""
    cutoff = str(cutoff_iso or "").strip()
    if not cutoff:
        return 0
    batch = max(50, min(int(batch_size), 10_000))
    total = 0
    while True:
        cur = conn.execute(
            """
            DELETE FROM chat_archive
            WHERE rowid IN (
                SELECT rowid FROM chat_archive
                WHERE COALESCE(TRIM(created_at), '') != ''
                  AND created_at < ?
                ORDER BY rowid ASC
                LIMIT ?
            )
            """,
            (cutoff, batch),
        )
        n = int(cur.rowcount or 0)
        conn.commit()
        total += n
        if n < batch:
            break
    return total


@_with_sqlite
def sqlite_archive_count(conn) -> int:
    row = conn.execute("SELECT COUNT(*) FROM chat_archive").fetchone()
    return int(row[0] if row else 0)


@_with_sqlite
def sqlite_vacuum(conn) -> None:
    conn.execute("VACUUM")
    conn.commit()


@_with_sqlite
def sqlite_clear_all(conn) -> None:
    conn.executescript(
        "DELETE FROM chat_room; DELETE FROM kv; DELETE FROM chat_archive; "
        "DELETE FROM global_chat_log; DELETE FROM user_profiles;"
    )
    conn.commit()


@_with_sqlite
def sqlite_upsert_user_profile(
    conn,
    fingerprint: str,
    display_name: str,
    birth: dict[str, Any],
    gapja: list[str],
) -> None:
    fp = str(fingerprint or "").strip()
    if not fp or not display_name.strip():
        return
    birth = _birth_with_time_adjustment_meta(birth)
    bj = json.dumps(birth or {}, ensure_ascii=False, default=str)
    gapja_list = [str(x) for x in list(gapja or [])]
    gj = json.dumps(gapja_list, ensure_ascii=False, default=str)
    gm = json.dumps(
        build_gapja_design_meta(gapja_list), ensure_ascii=False, default=str
    )
    st = 0
    ts = _now_kst_iso()
    _ensure_user_profiles_gapja_meta_column(conn)
    _ensure_user_profiles_usage_columns(conn)
    _ensure_user_profiles_revisit_pin_column(conn)
    conn.execute(
        """
        INSERT INTO user_profiles(
            fingerprint, display_name, birth_json, gapja_json, gapja_meta_json, summer_time,
            view_count, last_consulted_at, created_at, updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(fingerprint) DO UPDATE SET
            display_name = excluded.display_name,
            birth_json = excluded.birth_json,
            gapja_json = excluded.gapja_json,
            gapja_meta_json = excluded.gapja_meta_json,
            summer_time = excluded.summer_time,
            view_count = COALESCE(user_profiles.view_count, 0) + 1,
            last_consulted_at = excluded.last_consulted_at,
            updated_at = excluded.updated_at
        """,
        (fp, str(display_name).strip(), bj, gj, gm, st, 1, ts, ts, ts),
    )
    conn.commit()


@_with_sqlite
def sqlite_list_user_profiles(conn, limit: int = 80) -> list[dict[str, Any]]:
    lim = max(1, min(int(limit), 500))
    _ensure_user_profiles_gapja_meta_column(conn)
    _ensure_user_profiles_usage_columns(conn)
    rows = conn.execute(
        """
        SELECT fingerprint, display_name, birth_json, gapja_json, gapja_meta_json, summer_time,
               view_count, last_consulted_at, created_at, updated_at
        FROM user_profiles
        ORDER BY
            CASE WHEN last_consulted_at = '' THEN updated_at ELSE last_consulted_at END DESC,
            view_count DESC,
            updated_at DESC,
            fingerprint DESC
        LIMIT ?
        """,
        (lim,),
    ).fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        try:
            birth = json.loads(row["birth_json"] or "{}")
        except Exception:
            birth = {}
        try:
            gapja = json.loads(row["gapja_json"] or "[]")
        except Exception:
            gapja = []
        try:
            gapja_meta = json.loads(row["gapja_meta_json"] or "{}")
        except Exception:
            gapja_meta = {}
        if not isinstance(gapja_meta, dict) or not gapja_meta:
            gapja_meta = build_gapja_design_meta([str(x) for x in list(gapja or [])])
        out.append(
            {
                "fingerprint": str(row["fingerprint"]),
                "display_name": str(row["display_name"]),
                "birth": birth,
                "gapja": gapja,
                "gapja_meta": gapja_meta,
                "view_count": int(row["view_count"] or 0),
                "last_consulted_at": str(row["last_consulted_at"] or ""),
                "created_at": str(row["created_at"] or ""),
                "updated_at": str(row["updated_at"] or ""),
            }
        )
    return out


def _sqlite_fetch_user_profile_row(
    conn: sqlite3.Connection, fingerprint: str
) -> dict[str, Any] | None:
    """``@_with_sqlite`` 래퍼 밖에서 conn을 직접 넘길 때 사용(중첩 호출 버그 방지)."""
    fp = str(fingerprint or "").strip()
    if not fp:
        return None
    _ensure_user_profiles_gapja_meta_column(conn)
    _ensure_user_profiles_usage_columns(conn)
    row = conn.execute(
        """
        SELECT fingerprint, display_name, birth_json, gapja_json, gapja_meta_json, summer_time,
               view_count, last_consulted_at, created_at, updated_at
        FROM user_profiles WHERE fingerprint = ?
        """,
        (fp,),
    ).fetchone()
    if not row:
        return None
    try:
        birth = json.loads(row["birth_json"] or "{}")
    except Exception:
        birth = {}
    try:
        gapja = json.loads(row["gapja_json"] or "[]")
    except Exception:
        gapja = []
    try:
        gapja_meta = json.loads(row["gapja_meta_json"] or "{}")
    except Exception:
        gapja_meta = {}
    if not isinstance(gapja_meta, dict) or not gapja_meta:
        gapja_meta = build_gapja_design_meta([str(x) for x in list(gapja or [])])
    return {
        "fingerprint": str(row["fingerprint"]),
        "display_name": str(row["display_name"]),
        "birth": birth,
        "gapja": gapja,
        "gapja_meta": gapja_meta,
        "view_count": int(row["view_count"] or 0),
        "last_consulted_at": str(row["last_consulted_at"] or ""),
        "created_at": str(row["created_at"] or ""),
        "updated_at": str(row["updated_at"] or ""),
    }


@_with_sqlite
def sqlite_get_user_profile(conn, fingerprint: str) -> dict[str, Any] | None:
    return _sqlite_fetch_user_profile_row(conn, fingerprint)


@_with_sqlite
def sqlite_touch_user_profile(conn, fingerprint: str) -> int:
    fp = str(fingerprint or "").strip()
    if not fp:
        return 0
    _ensure_user_profiles_usage_columns(conn)
    cur = conn.execute(
        """
        UPDATE user_profiles
        SET view_count = COALESCE(view_count, 0) + 1,
            last_consulted_at = ?,
            updated_at = ?
        WHERE fingerprint = ?
        """,
        (_now_kst_iso(), _now_kst_iso(), fp),
    )
    conn.commit()
    return int(cur.rowcount or 0)


def _redis_arch_row_key(row_id: str) -> str:
    return f"{_NS}:arch:r:{row_id}"


def _redis_arch_sess_set_key(session_id: str) -> str:
    sid = coalesce_session_id(session_id) or "_none"
    return f"{_NS}:arch:s:{sid}"


def _redis_archive_migrate_legacy_if_needed(r) -> None:
    """구버전 단일 LIST(archive:lines)를 v2 구조로 일회 이관 후 LIST 삭제."""
    try:
        if r.get(_ARCH_V2_MARKER):
            return
    except Exception:
        return
    try:
        if r.exists(_ARCH_LEGACY_LIST):
            lines = r.lrange(_ARCH_LEGACY_LIST, 0, -1) or []
            for ln in lines:
                if not ln:
                    continue
                try:
                    obj = json.loads(ln)
                except Exception:
                    continue
                sid = str(obj.get("session_id") or "").strip() or "_none"
                if not str(obj.get("ts") or "").strip():
                    obj["ts"] = _now_kst_iso()
                line = json.dumps(obj, ensure_ascii=False, default=str)
                rid = str(uuid.uuid4())
                score = time.time() * 1000.0
                p = r.pipeline()
                p.set(_redis_arch_row_key(rid), line)
                p.zadd(_ARCH_TIMELINE, {rid: score})
                p.sadd(_redis_arch_sess_set_key(sid), rid)
                p.execute()
            r.delete(_ARCH_LEGACY_LIST)
    except Exception as e:
        _redis_note_failure(e)
    finally:
        try:
            r.set(_ARCH_V2_MARKER, "1")
        except Exception:
            pass


def _r_key_room_msgs(rk: str) -> str:
    return f"{_NS}:room:{rk}:messages"


def _r_key_room_label(rk: str) -> str:
    return f"{_NS}:room:{rk}:label"


def redis_load_bus_dict() -> dict[str, Any]:
    r = _redis_client()
    if not r:
        return {"rooms": {}, "labels": {}}
    rooms: dict[str, Any] = {}
    labels: dict[str, Any] = {}
    try:
        keys = list(r.smembers(_R_KEY_ROOM_INDEX) or [])
        for rk in keys:
            rk = str(rk)
            raw = r.get(_r_key_room_msgs(rk))
            if raw:
                try:
                    rooms[rk] = json.loads(raw)
                except Exception:
                    rooms[rk] = []
            lr = r.get(_r_key_room_label(rk))
            if lr:
                try:
                    labels[rk] = json.loads(lr)
                except Exception:
                    pass
    except Exception as e:
        _redis_note_failure(e)
        return {"rooms": {}, "labels": {}}
    return {"rooms": rooms, "labels": labels}


def redis_upsert_chat_room(
    room_key: str, messages: list[Any], label: dict[str, Any] | None
) -> None:
    r = _redis_client()
    if not r:
        return
    rk = str(room_key or "").strip()
    if not rk:
        return
    try:
        pipe = r.pipeline()
        pipe.set(
            _r_key_room_msgs(rk),
            json.dumps(messages or [], ensure_ascii=False, default=str),
        )
        if label is not None:
            pipe.set(
                _r_key_room_label(rk),
                json.dumps(label, ensure_ascii=False, default=str),
            )
        pipe.sadd(_R_KEY_ROOM_INDEX, rk)
        ttl = redis_room_ttl_sec()
        if ttl > 0:
            pipe.expire(_r_key_room_msgs(rk), ttl)
            if label is not None:
                pipe.expire(_r_key_room_label(rk), ttl)
        pipe.execute()
    except Exception:
        pass


def redis_list_room_keys(limit: int = 500) -> list[str]:
    r = _redis_client()
    if not r:
        return []
    lim = max(1, min(int(limit), 2000))
    try:
        keys = [str(k) for k in (r.smembers(_R_KEY_ROOM_INDEX) or [])]
        keys.sort(reverse=True)
        return keys[:lim]
    except Exception as e:
        _redis_note_failure(e)
        return []


def redis_list_chat_room_summaries(limit: int = 120) -> list[dict[str, Any]]:
    lim = max(1, min(int(limit), 500))
    try:
        keys = redis_list_room_keys(lim)
        out: list[dict[str, Any]] = []
        for rk in keys:
            msgs, lab = redis_get_chat_room(rk)
            u_name = (
                str((lab or {}).get("u_name") or "") if isinstance(lab, dict) else ""
            )
            contact = (
                str((lab or {}).get("contact") or "") if isinstance(lab, dict) else ""
            )
            user_gapja = (
                str((lab or {}).get("user_gapja") or (lab or {}).get("user_ilju") or "")
                if isinstance(lab, dict)
                else ""
            )
            consultation_type = (
                str((lab or {}).get("consultation_type") or "미분류")
                if isinstance(lab, dict)
                else "미분류"
            )
            msg_count = len(msgs) if isinstance(msgs, list) else 0
            out.append(
                {
                    "room_key": rk,
                    "u_name": u_name,
                    "contact": contact,
                    "user_gapja": user_gapja,
                    "consultation_type": consultation_type,
                    "msg_count": msg_count,
                    "updated_at": "",
                }
            )
        return out
    except Exception as e:
        _redis_note_failure(e)
        return []


def redis_get_chat_room(room_key: str) -> tuple[list[Any], dict[str, Any] | None]:
    r = _redis_client()
    if not r:
        return [], None
    rk = str(room_key or "").strip()
    if not rk:
        return [], None
    try:
        raw = r.get(_r_key_room_msgs(rk))
        msgs = json.loads(raw) if raw else []
        if not isinstance(msgs, list):
            msgs = []
        lab_raw = r.get(_r_key_room_label(rk))
        lab = json.loads(lab_raw) if lab_raw else None
        return msgs, lab if isinstance(lab, dict) else None
    except Exception as e:
        _redis_note_failure(e)
        return [], None


def redis_clear_chat_room(room_key: str) -> None:
    r = _redis_client()
    if not r:
        return
    rk = str(room_key or "").strip()
    if not rk:
        return
    try:
        r.delete(_r_key_room_msgs(rk), _r_key_room_label(rk))
        r.srem(_R_KEY_ROOM_INDEX, rk)
        r.hdel(_R_KEY_GLOBAL_CHAT_CURSOR, rk)
    except Exception as e:
        _redis_note_failure(e)


def redis_clear_all_chat_rooms() -> int:
    """Redis에 등록된 모든 상담 방·공용 채팅 로그 삭제."""
    r = _redis_client()
    if not r:
        return 0
    try:
        keys = [str(k) for k in (r.smembers(_R_KEY_ROOM_INDEX) or [])]
        if keys:
            pipe = r.pipeline()
            for rk in keys:
                pipe.delete(_r_key_room_msgs(rk), _r_key_room_label(rk))
            pipe.delete(_R_KEY_ROOM_INDEX)
            pipe.execute()
        r.delete(_R_KEY_GLOBAL_CHAT_LOG, _R_KEY_GLOBAL_CHAT_CURSOR)
        return len(keys)
    except Exception as e:
        _redis_note_failure(e)
        return 0


def redis_kvs_get(key: str) -> str | None:
    r = _redis_client()
    if not r:
        return None
    try:
        return r.get(f"{_NS}:kv:{key}")
    except Exception as e:
        _redis_note_failure(e)
        return None


def redis_kvs_set(key: str, value: str) -> None:
    r = _redis_client()
    if not r:
        return
    try:
        r.set(f"{_NS}:kv:{key}", value)
    except Exception as e:
        _redis_note_failure(e)


def redis_kvs_delete(key: str) -> None:
    r = _redis_client()
    if not r:
        return
    try:
        r.delete(f"{_NS}:kv:{key}")
    except Exception as e:
        _redis_note_failure(e)


def redis_archive_append(record: dict[str, Any]) -> None:
    r = _redis_client()
    if not r:
        return
    row = dict(record)
    if not str(row.get("ts") or "").strip():
        row["ts"] = _now_kst_iso()
    sid = coalesce_session_id(str(row.get("session_id") or ""))
    if not sid:
        log.warning("redis_archive_append skipped: invalid session_id")
        return
    row["session_id"] = sid
    line = json.dumps(row, ensure_ascii=False, default=str)
    rid = str(uuid.uuid4())
    score = time.time() * 1000.0
    try:
        p = r.pipeline()
        p.set(_redis_arch_row_key(rid), line)
        p.zadd(_ARCH_TIMELINE, {rid: score})
        p.sadd(_redis_arch_sess_set_key(sid), rid)
        p.execute()
    except Exception as e:
        _redis_note_failure(e)


def redis_archive_load_recent(max_rows: int) -> list[dict[str, Any]]:
    r = _redis_client()
    if not r:
        return []
    n = max(1, int(max_rows))
    try:
        row_ids = r.zrevrange(_ARCH_TIMELINE, 0, n - 1) or []
        if not row_ids:
            return []
        keys = [_redis_arch_row_key(rid) for rid in row_ids]
        chunks = r.mget(keys) or []
        out: list[dict[str, Any]] = []
        for ln in reversed(chunks):
            if not ln:
                continue
            try:
                o = json.loads(ln)
                if isinstance(o, dict):
                    out.append(o)
            except Exception:
                continue
        return out
    except Exception as e:
        _redis_note_failure(e)
        return []


def redis_archive_load_session_recent(
    session_id: str, max_rows: int
) -> list[dict[str, Any]]:
    """세션별 아카이브(최근순). 세트에 담긴 row id → mget 후 ts 기준 정렬."""
    r = _redis_client()
    if not r:
        return []
    sid = coalesce_session_id(session_id)
    if not sid:
        return []
    n = max(1, int(max_rows))
    skey = _redis_arch_sess_set_key(sid)
    try:
        row_ids = list(r.smembers(skey) or [])
    except Exception as e:
        _redis_note_failure(e)
        return []
    if not row_ids:
        return []
    try:
        keys = [_redis_arch_row_key(rid) for rid in row_ids]
        chunks = r.mget(keys) or []
    except Exception as e:
        _redis_note_failure(e)
        return []
    parsed: list[dict[str, Any]] = []
    for ln in chunks:
        if not ln:
            continue
        try:
            o = json.loads(ln)
            if isinstance(o, dict):
                parsed.append(o)
        except Exception:
            continue
    parsed.sort(key=lambda d: str(d.get("ts") or ""), reverse=True)
    return parsed[:n]


def _redis_archive_remove_row_ids(r: Any, row_ids: list[str]) -> int:
    removed = 0
    for rid in row_ids:
        rid_s = str(rid or "").strip()
        if not rid_s:
            continue
        sid = "_none"
        try:
            raw = r.get(_redis_arch_row_key(rid_s))
            if raw:
                obj = json.loads(raw)
                if isinstance(obj, dict):
                    sid = (
                        coalesce_session_id(str(obj.get("session_id") or "")) or "_none"
                    )
        except Exception:
            pass
        try:
            p = r.pipeline()
            p.delete(_redis_arch_row_key(rid_s))
            p.zrem(_ARCH_TIMELINE, rid_s)
            if sid != "_none":
                p.srem(_redis_arch_sess_set_key(sid), rid_s)
            p.execute()
            removed += 1
        except Exception:
            try:
                r.delete(_redis_arch_row_key(rid_s))
                r.zrem(_ARCH_TIMELINE, rid_s)
                removed += 1
            except Exception:
                pass
    return removed


def redis_archive_prune_before(cutoff_ms: float, *, batch_size: int = 2000) -> int:
    """Redis v2 타임라인에서 ``cutoff_ms`` 이전 점수(밀리초) 행을 배치 삭제합니다."""
    r = _redis_client()
    if not r:
        return 0
    batch = max(50, min(int(batch_size), 10_000))
    total = 0
    try:
        while True:
            row_ids = r.zrangebyscore(
                _ARCH_TIMELINE, 0, float(cutoff_ms), start=0, num=batch
            )
            if not row_ids:
                break
            ids = [str(x) for x in row_ids]
            total += _redis_archive_remove_row_ids(r, ids)
            if len(ids) < batch:
                break
    except Exception as e:
        _redis_note_failure(e)
        log.exception("redis_archive_prune_before failed")
    return total


def redis_archive_delete_session(session_id: str) -> int:
    r = _redis_client()
    if not r:
        return 0
    sid = coalesce_session_id(session_id)
    if not sid:
        return 0
    skey = _redis_arch_sess_set_key(sid)
    try:
        row_ids = list(r.smembers(skey) or [])
    except Exception as e:
        _redis_note_failure(e)
        return 0
    if not row_ids:
        return 0
    try:
        p = r.pipeline()
        for rid in row_ids:
            p.delete(_redis_arch_row_key(rid))
            p.zrem(_ARCH_TIMELINE, rid)
        p.delete(skey)
        p.execute()
    except Exception as e:
        _redis_note_failure(e)
        return 0
    return len(row_ids)


def redis_clear_all() -> None:
    r = _redis_client()
    if not r:
        return
    try:
        for k in r.scan_iter(f"{_NS}:*"):
            r.delete(k)
        # 전체 삭제로 v2 마커까지 제거됨 → 아카이브 경로와 동일하게 마커·빈 상태 복구
        _redis_archive_migrate_legacy_if_needed(r)
    except Exception as e:
        _redis_note_failure(e)


def redis_upsert_user_profile(
    fingerprint: str,
    display_name: str,
    birth: dict[str, Any],
    gapja: list[str],
) -> None:
    r = _redis_client()
    if not r:
        return
    fp = str(fingerprint or "").strip()
    if not fp or not str(display_name or "").strip():
        return
    birth = _birth_with_time_adjustment_meta(birth)
    ts = _now_kst_iso()
    doc = {
        "fingerprint": fp,
        "display_name": str(display_name).strip(),
        "birth": birth or {},
        "gapja": [str(x) for x in list(gapja or [])],
        "gapja_meta": build_gapja_design_meta([str(x) for x in list(gapja or [])]),
        "view_count": 1,
        "last_consulted_at": ts,
        "updated_at": ts,
    }
    try:
        prev = r.get(_r_key_uprof(fp))
        if prev:
            try:
                old = json.loads(prev)
                if isinstance(old, dict) and str(old.get("created_at") or "").strip():
                    doc["created_at"] = old["created_at"]
                if isinstance(old, dict):
                    doc["view_count"] = int(old.get("view_count") or 0) + 1
                    old_pin = str(old.get("revisit_pin_hash") or "").strip()
                    if old_pin:
                        doc["revisit_pin_hash"] = old_pin
            except Exception:
                pass
        if "created_at" not in doc:
            doc["created_at"] = ts
        line = json.dumps(doc, ensure_ascii=False, default=str)
        p = r.pipeline()
        p.set(_r_key_uprof(fp), line)
        p.zadd(_R_KEY_UPROF_TL, {fp: time.time() * 1000.0})
        p.execute()
    except Exception as e:
        _redis_note_failure(e)
        log.exception("redis_upsert_user_profile failed")


def redis_list_user_profiles(limit: int = 80) -> list[dict[str, Any]]:
    r = _redis_client()
    if not r:
        return []
    lim = max(1, min(int(limit), 500))
    try:
        fps = r.zrevrange(_R_KEY_UPROF_TL, 0, lim - 1) or []
        out: list[dict[str, Any]] = []
        for fp in fps:
            fp = str(fp)
            raw = r.get(_r_key_uprof(fp))
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except Exception:
                continue
            if not isinstance(obj, dict):
                continue
            birth = obj.get("birth") if isinstance(obj.get("birth"), dict) else {}
            out.append(
                {
                    "fingerprint": fp,
                    "display_name": str(obj.get("display_name") or ""),
                    "birth": birth,
                    "gapja": (
                        obj.get("gapja") if isinstance(obj.get("gapja"), list) else []
                    ),
                    "gapja_meta": (
                        obj.get("gapja_meta")
                        if isinstance(obj.get("gapja_meta"), dict)
                        else build_gapja_design_meta(
                            obj.get("gapja")
                            if isinstance(obj.get("gapja"), list)
                            else []
                        )
                    ),
                    "view_count": int(obj.get("view_count") or 0),
                    "last_consulted_at": str(obj.get("last_consulted_at") or ""),
                    "created_at": str(obj.get("created_at") or ""),
                    "updated_at": str(obj.get("updated_at") or ""),
                }
            )
        return out
    except Exception as e:
        _redis_note_failure(e)
        return []


def redis_get_user_profile(fingerprint: str) -> dict[str, Any] | None:
    r = _redis_client()
    if not r:
        return None
    fp = str(fingerprint or "").strip()
    if not fp:
        return None
    try:
        raw = r.get(_r_key_uprof(fp))
    except Exception as e:
        _redis_note_failure(e)
        return None
    if not raw:
        return None
    try:
        obj = json.loads(raw)
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    birth = obj.get("birth") if isinstance(obj.get("birth"), dict) else {}
    return {
        "fingerprint": fp,
        "display_name": str(obj.get("display_name") or ""),
        "birth": birth,
        "gapja": obj.get("gapja") if isinstance(obj.get("gapja"), list) else [],
        "gapja_meta": (
            obj.get("gapja_meta")
            if isinstance(obj.get("gapja_meta"), dict)
            else build_gapja_design_meta(
                obj.get("gapja") if isinstance(obj.get("gapja"), list) else []
            )
        ),
        "view_count": int(obj.get("view_count") or 0),
        "last_consulted_at": str(obj.get("last_consulted_at") or ""),
        "created_at": str(obj.get("created_at") or ""),
        "updated_at": str(obj.get("updated_at") or ""),
    }


def redis_touch_user_profile(fingerprint: str) -> int:
    r = _redis_client()
    if not r:
        return 0
    fp = str(fingerprint or "").strip()
    if not fp:
        return 0
    try:
        raw = r.get(_r_key_uprof(fp))
        if not raw:
            return 0
        obj = json.loads(raw)
        if not isinstance(obj, dict):
            return 0
        ts = _now_kst_iso()
        obj["view_count"] = int(obj.get("view_count") or 0) + 1
        obj["last_consulted_at"] = ts
        obj["updated_at"] = ts
        p = r.pipeline()
        p.set(_r_key_uprof(fp), json.dumps(obj, ensure_ascii=False, default=str))
        p.zadd(_R_KEY_UPROF_TL, {fp: time.time() * 1000.0})
        p.execute()
        return 1
    except Exception as e:
        _redis_note_failure(e)
        return 0


# ---------------------------------------------------------------------------
# 통합 API (app.py에서 호출)
# ---------------------------------------------------------------------------


def load_shared_chat_bus() -> dict[str, Any]:
    try:
        sqlite_bus = sqlite_load_bus_dict()
        if not isinstance(sqlite_bus, dict):
            sqlite_bus = {"rooms": {}, "labels": {}}
    except Exception:
        log.exception("sqlite load_shared_chat_bus failed")
        sqlite_bus = {"rooms": {}, "labels": {}}
    return _redis_read_fallback(
        sqlite_bus,
        redis_load_bus_dict,
        prefer_redis_when=lambda d: isinstance(d, dict)
        and bool(d.get("rooms") or d.get("labels")),
    )


_GLOBAL_CHAT_SYNC_LOG_KEY = "global_chat_sync_log_v1"
_GLOBAL_CHAT_SYNC_CURSOR_KEY = "global_chat_sync_cursor_v1"
_R_KEY_GLOBAL_CHAT_LOG = f"{_NS}:global_chat_log"
_R_KEY_GLOBAL_CHAT_CURSOR = f"{_NS}:global_chat_cursor"


def redis_append_global_chat_log_events(
    room_key: str,
    messages: list[Any],
    label: dict[str, Any] | None,
    *,
    cap: int = 5000,
) -> None:
    r = _redis_client()
    if not r:
        return
    rk = str(room_key or "").strip()
    if not rk:
        return
    msgs = list(messages or [])
    if not msgs:
        return
    try:
        raw_prev = r.hget(_R_KEY_GLOBAL_CHAT_CURSOR, rk)
        prev = int(raw_prev or 0)
    except Exception as e:
        _redis_note_failure(e)
        return
    if len(msgs) < prev:
        prev = 0
    tail = msgs[prev:]
    if not tail:
        return
    lab = label if isinstance(label, dict) else {}
    ts = _now_kst_iso()
    u_name = str(lab.get("u_name") or "")
    contact = _masked_contact(lab.get("contact") or "")
    lines: list[str] = []
    for i, m in enumerate(tail, start=prev):
        if not isinstance(m, dict):
            continue
        lines.append(
            json.dumps(
                {
                    "sync_ts": ts,
                    "room_key": rk,
                    "u_name": u_name,
                    "contact": contact,
                    "msg_index": int(i),
                    "role": str(m.get("role") or ""),
                    "msg": str(m.get("msg") or ""),
                    "is_manual": bool(m.get("is_manual", False)),
                },
                ensure_ascii=False,
                default=str,
            )
        )
    if not lines:
        return
    try:
        p = r.pipeline()
        p.lpush(_R_KEY_GLOBAL_CHAT_LOG, *lines)
        p.ltrim(_R_KEY_GLOBAL_CHAT_LOG, 0, max(1, int(cap)) - 1)
        p.hset(_R_KEY_GLOBAL_CHAT_CURSOR, rk, len(msgs))
        p.execute()
    except Exception as e:
        _redis_note_failure(e)


def redis_list_global_chat_log(*, max_lines: int = 400) -> list[dict[str, Any]]:
    r = _redis_client()
    if not r:
        return []
    n = max(1, min(int(max_lines), 2000))
    try:
        chunks = r.lrange(_R_KEY_GLOBAL_CHAT_LOG, 0, n - 1) or []
    except Exception as e:
        _redis_note_failure(e)
        return []
    out: list[dict[str, Any]] = []
    for raw in reversed(chunks):
        try:
            obj = json.loads(raw)
            if isinstance(obj, dict):
                out.append(obj)
        except Exception:
            continue
    return out


def append_global_chat_sync_events(
    room_key: str,
    messages: list[Any],
    label: dict[str, Any] | None,
) -> None:
    """관리자용 공용 타임라인을 행 단위로 추가합니다."""
    sqlite_append_global_chat_log_events(room_key, messages, label, cap=5000)
    if _redis_enabled():
        redis_append_global_chat_log_events(room_key, messages, label, cap=5000)


def list_global_chat_sync_log(*, max_lines: int = 400) -> list[dict[str, Any]]:
    """관리자용: 공용 동기 로그 최근 N건(시간순 저장 → 최신이 끝)."""
    rows = _redis_read_fallback(
        sqlite_list_global_chat_log(max_lines=max_lines),
        lambda: redis_list_global_chat_log(max_lines=max_lines),
    )
    if rows:
        return rows
    legacy = kv_get_json(_GLOBAL_CHAT_SYNC_LOG_KEY)
    if not isinstance(legacy, list) or not legacy:
        return []
    n = max(1, min(int(max_lines), 2000))
    return [x for x in legacy if isinstance(x, dict)][-n:]


def upsert_shared_chat_room(
    room_key: str, messages: list[Any], label: dict[str, Any] | None
) -> None:
    """공유 상담 방 저장. SQLite를 먼저 쓰고 Redis는 가능할 때만 미러링합니다."""
    sqlite_upsert_chat_room(room_key, messages, label)
    if _redis_enabled():
        try:
            redis_upsert_chat_room(room_key, messages, label)
        except Exception as e:
            _redis_note_failure(e)
    try:
        append_global_chat_sync_events(room_key, messages, label)
    except Exception:
        log.exception("append_global_chat_sync_events failed")


def get_shared_chat_room(room_key: str) -> tuple[list[Any], dict[str, Any] | None]:
    sqlite_result = sqlite_get_chat_room(room_key)
    return _redis_read_fallback(
        sqlite_result,
        lambda: redis_get_chat_room(room_key),
        prefer_redis_when=lambda t: bool(t[0]) or t[1] is not None,
    )


def clear_shared_chat_room(room_key: str) -> None:
    sqlite_clear_chat_room(room_key)
    if _redis_enabled():
        redis_clear_chat_room(room_key)


def clear_all_shared_chat_rooms(*, include_archive: bool = True) -> dict[str, int]:
    """모든 상담 방 채팅·공용 로그(및 선택 시 아카이브) 삭제."""
    rooms_sqlite = 0
    log_sqlite = 0
    try:
        rooms_sqlite, log_sqlite = sqlite_clear_all_chat_rooms()
    except Exception:
        log.exception("clear_all_shared_chat_rooms: sqlite failed")
    rooms_redis = 0
    if _redis_enabled():
        rooms_redis = redis_clear_all_chat_rooms()
    archive_rows = 0
    if include_archive:
        try:
            archive_rows = int(sqlite_archive_clear_all() or 0)
        except Exception:
            log.exception("clear_all_shared_chat_rooms: sqlite archive failed")
        if _redis_enabled():
            try:
                r = _redis_client()
                if r:
                    _redis_archive_clear_all_strict(r)
            except Exception as e:
                _redis_note_failure(e)
    return {
        "rooms_sqlite": rooms_sqlite,
        "log_sqlite": log_sqlite,
        "rooms_redis": rooms_redis,
        "archive_rows": archive_rows,
    }


def list_chat_room_keys(limit: int = 500) -> list[str]:
    """관리자 UI용: 최근 갱신 순 방 키 목록(전체 JSON 버스 로드 없이 SQLite는 인덱스 스캔)."""
    return _redis_read_fallback(
        sqlite_list_room_keys(limit),
        lambda: redis_list_room_keys(limit),
    )


def list_chat_room_summaries(limit: int = 120) -> list[dict[str, Any]]:
    """관리자 UI용: 방별 이름·연락처·메시지 수 등 요약(최근 갱신 순)."""
    return _redis_read_fallback(
        sqlite_list_chat_room_summaries(limit),
        lambda: redis_list_chat_room_summaries(limit),
    )


def kv_get_json(key: str) -> Any | None:
    raw: str | None
    raw = sqlite_kvs_get(key)
    if (raw is None or raw == "") and _redis_enabled():
        raw = redis_kvs_get(key)
    if raw is None or raw == "":
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def kv_set_json(key: str, obj: Any) -> None:
    s = json.dumps(obj, ensure_ascii=False, default=str)
    sqlite_kvs_set(key, s)
    if _redis_enabled():
        redis_kvs_set(key, s)


def kv_delete_json(key: str) -> None:
    sqlite_kvs_delete(key)
    if _redis_enabled():
        redis_kvs_delete(key)


def kv_delete_json_prefix(prefix: str) -> None:
    sqlite_kvs_delete_prefix(prefix)
    # Redis 미러는 STEP2 prefill 전용 prefix 삭제 시 생략(키 스캔 비용)


def save_session_draft(session_id: str, draft: dict[str, Any]) -> None:
    """세션별 현재 STEP/UI draft를 KV에 저장합니다."""
    sid = coalesce_session_id(session_id)
    if not sid:
        return
    rec = {
        "session_id": sid,
        "saved_at": _now_kst_iso(),
        **dict(draft or {}),
    }
    kv_set_json(f"session:{sid}:current_step", rec)


def load_session_draft(session_id: str) -> dict[str, Any] | None:
    """세션별 current step/draft를 읽습니다 (세션 ID 일치 시에만)."""
    raw = str(session_id or "").strip()
    sid = coalesce_session_id(raw) if raw else None
    rec: Any | None = None
    if sid:
        rec = kv_get_json(f"session:{sid}:current_step")
    return dict(rec) if isinstance(rec, dict) else None


def clear_session_draft(session_id: str) -> None:
    sid = coalesce_session_id(session_id)
    if sid:
        kv_set_json(f"session:{sid}:current_step", {})


def upsert_user_profile(
    *,
    display_name: str,
    birth: dict[str, Any],
    gapja: list[str],
) -> str | None:
    """이름·생일(`birth`)·사주 간지(`gapja`)를 ``user_profiles``에 저장합니다.

    동일 인물(이름 정규화 + 생일 구성 동일)은 ``fingerprint``로 합쳐져 갱신됩니다.
    저장 실패 시에도 앱 흐름을 막지 않도록 예외를 삼킵니다.

    Returns
    -------
    str | None
        성공 시 fingerprint, 실패 시 None.
    """
    try:
        fp = user_profile_fingerprint(display_name=display_name, birth=birth)
        sqlite_upsert_user_profile(fp, display_name, birth, gapja)
        if _redis_enabled():
            redis_upsert_user_profile(fp, display_name, birth, gapja)
        return fp
    except Exception:
        log.exception("upsert_user_profile failed for %s", display_name)
        return None


def list_user_profiles(limit: int = 80) -> list[dict[str, Any]]:
    """최근 갱신 순 프로필 목록(관리·디버그용)."""
    return _redis_read_fallback(
        sqlite_list_user_profiles(limit),
        lambda: redis_list_user_profiles(limit),
    )


def get_user_profile(fingerprint: str) -> dict[str, Any] | None:
    """단일 프로필 조회. 없으면 None."""
    fp = str(fingerprint or "").strip()
    if not fp:
        return None
    return _redis_read_fallback(
        sqlite_get_user_profile(fp),
        lambda: redis_get_user_profile(fp),
        prefer_redis_when=lambda rec: rec is not None,
    )


def touch_user_profile(fingerprint: str) -> int:
    """프로필을 실제로 열람/상담에 사용했을 때 조회수와 최근 상담일을 갱신합니다."""
    fp = str(fingerprint or "").strip()
    if not fp:
        return 0
    n = sqlite_touch_user_profile(fp)
    if _redis_enabled():
        try:
            redis_touch_user_profile(fp)
        except Exception as e:
            _redis_note_failure(e)
    return int(n)


_REVISIT_PIN_MIN_LEN = 6
_REVISIT_PIN_MAX_LEN = 32
_R_KEY_REVISIT_PIN = "revisit_pin:"


def _revisit_pin_pepper() -> bytes:
    raw = str(os.environ.get("SAJU_REVISIT_PEPPER") or "").strip()
    if raw:
        return raw.encode("utf-8")
    return hashlib.sha256(f"saju-revisit:{_app_dir()}".encode("utf-8")).digest()


def normalize_revisit_pin(pin: str) -> str:
    return str(pin or "").strip()


def validate_revisit_pin(pin: str) -> str | None:
    """신규 설정용 — 유효하면 None, 아니면 한글 오류 메시지."""
    p = normalize_revisit_pin(pin)
    if len(p) < _REVISIT_PIN_MIN_LEN:
        return f"비밀번호는 {_REVISIT_PIN_MIN_LEN}자 이상이어야 합니다."
    if len(p) > _REVISIT_PIN_MAX_LEN:
        return f"비밀번호는 {_REVISIT_PIN_MAX_LEN}자 이하여야 합니다."
    if not any(ch.isdigit() for ch in p):
        return "비밀번호에 숫자를 포함해 주세요."
    if not any(not ch.isalnum() for ch in p):
        return "비밀번호에 특수문자를 포함해 주세요."
    return None


def validate_revisit_pin_lookup(pin: str) -> str | None:
    """로그인 조회용 — 기존 짧은 비밀번호도 허용."""
    p = normalize_revisit_pin(pin)
    if not p:
        return "비밀번호를 입력해 주세요."
    if len(p) > _REVISIT_PIN_MAX_LEN:
        return f"비밀번호는 {_REVISIT_PIN_MAX_LEN}자 이하여야 합니다."
    return None


def revisit_pin_lookup_key(pin: str) -> str:
    """DB·Redis 조회용 일방향 키(평문 저장 없음)."""
    p = normalize_revisit_pin(pin)
    return hashlib.sha256(_revisit_pin_pepper() + p.encode("utf-8")).hexdigest()


@_with_sqlite
def sqlite_get_user_profile_by_revisit_pin(conn, pin: str) -> dict[str, Any] | None:
    if validate_revisit_pin_lookup(pin):
        return None
    lookup = revisit_pin_lookup_key(pin)
    _ensure_user_profiles_revisit_pin_column(conn)
    row = conn.execute(
        "SELECT fingerprint FROM user_profiles WHERE revisit_pin_hash = ? LIMIT 1",
        (lookup,),
    ).fetchone()
    if not row:
        return None
    return _sqlite_fetch_user_profile_row(conn, str(row["fingerprint"]))


@_with_sqlite
def sqlite_set_profile_revisit_pin(
    conn, fingerprint: str, pin: str
) -> tuple[bool, str]:
    fp = str(fingerprint or "").strip()
    err = validate_revisit_pin(pin)
    if err:
        return False, err
    if not fp:
        return False, "프로필을 찾을 수 없습니다."
    if not _sqlite_fetch_user_profile_row(conn, fp):
        return False, "먼저 사주 정보를 저장한 뒤 비밀번호를 설정해 주세요."
    lookup = revisit_pin_lookup_key(pin)
    _ensure_user_profiles_revisit_pin_column(conn)
    other = conn.execute(
        "SELECT fingerprint FROM user_profiles WHERE revisit_pin_hash = ? AND fingerprint != ?",
        (lookup, fp),
    ).fetchone()
    if other:
        return False, "이미 사용 중인 비밀번호입니다. 다른 비밀번호를 정해 주세요."
    conn.execute(
        "UPDATE user_profiles SET revisit_pin_hash = ?, updated_at = ? WHERE fingerprint = ?",
        (lookup, _now_kst_iso(), fp),
    )
    conn.commit()
    if _redis_enabled():
        try:
            redis_set_profile_revisit_pin(fp, lookup)
        except Exception as e:
            _redis_note_failure(e)
    return True, "재방문 비밀번호가 설정되었습니다."


def redis_set_profile_revisit_pin(fingerprint: str, lookup_key: str) -> None:
    r = _redis_client()
    if not r:
        return
    fp = str(fingerprint or "").strip()
    lk = str(lookup_key or "").strip()
    if not fp or not lk:
        return
    try:
        prev_raw = r.get(_r_key_uprof(fp))
        if prev_raw:
            try:
                old = json.loads(prev_raw)
                old_lk = (
                    str(old.get("revisit_pin_hash") or "")
                    if isinstance(old, dict)
                    else ""
                )
                if old_lk and old_lk != lk:
                    r.delete(f"{_R_KEY_REVISIT_PIN}{old_lk}")
            except Exception:
                pass
        doc_raw = r.get(_r_key_uprof(fp))
        if doc_raw:
            doc = json.loads(doc_raw)
            if isinstance(doc, dict):
                doc["revisit_pin_hash"] = lk
                r.set(
                    _r_key_uprof(fp), json.dumps(doc, ensure_ascii=False, default=str)
                )
        r.set(f"{_R_KEY_REVISIT_PIN}{lk}", fp)
    except Exception as e:
        _redis_note_failure(e)


def redis_get_user_profile_by_revisit_pin(pin: str) -> dict[str, Any] | None:
    r = _redis_client()
    if not r or validate_revisit_pin_lookup(pin):
        return None
    lk = revisit_pin_lookup_key(pin)
    try:
        fp = r.get(f"{_R_KEY_REVISIT_PIN}{lk}")
        if not fp:
            return None
        return redis_get_user_profile(str(fp))
    except Exception as e:
        _redis_note_failure(e)
        return None


def set_profile_revisit_pin(*, fingerprint: str, pin: str) -> tuple[bool, str]:
    """프로필에 재방문 비밀번호를 설정합니다."""
    return sqlite_set_profile_revisit_pin(fingerprint, pin)


def get_user_profile_by_revisit_pin(pin: str) -> dict[str, Any] | None:
    """비밀번호로 본인 프로필만 조회(홈 목록 노출 없음)."""
    if validate_revisit_pin_lookup(pin):
        return None
    # SQLite(해시·프로필)가 기준 — Redis는 SQLite에 없을 때만 보조
    rec = sqlite_get_user_profile_by_revisit_pin(pin)
    if rec is not None:
        return rec
    if not _redis_enabled():
        return None
    try:
        return redis_get_user_profile_by_revisit_pin(pin)
    except Exception as e:
        _redis_note_failure(e)
        return None


def save_user_profile_with_revisit_pin(
    *,
    display_name: str,
    birth: dict[str, Any],
    gapja: list[str],
    pin: str,
) -> tuple[str | None, bool, str]:
    """프로필 upsert와 재방문 비밀번호 설정을 한 번에 처리합니다."""
    fp = user_profile_fingerprint(display_name=display_name, birth=birth)
    gj = [str(x) for x in list(gapja or [])]
    if len(gj) < 3:
        return None, False, "사주 간지가 부족해 프로필을 저장하지 못했습니다."
    try:
        sqlite_upsert_user_profile(fp, display_name, birth, gj)
        ok, msg = sqlite_set_profile_revisit_pin(fp, pin)
        if ok and _redis_enabled():
            try:
                redis_upsert_user_profile(fp, display_name, birth, gj)
                redis_set_profile_revisit_pin(fp, revisit_pin_lookup_key(pin))
            except Exception as e:
                _redis_note_failure(e)
        return fp, ok, msg
    except Exception:
        log.exception("save_user_profile_with_revisit_pin failed for %s", display_name)
        return None, False, "재방문 비밀번호 저장 중 오류가 발생했습니다."


@_with_sqlite
def sqlite_delete_user_profile(conn, fingerprint: str) -> int:
    fp = str(fingerprint or "").strip()
    if not fp:
        return 0
    _ensure_user_profiles_revisit_pin_column(conn)
    row = conn.execute(
        "SELECT revisit_pin_hash FROM user_profiles WHERE fingerprint = ?",
        (fp,),
    ).fetchone()
    old_lk = str(row["revisit_pin_hash"] or "") if row else ""
    cur = conn.execute("DELETE FROM user_profiles WHERE fingerprint = ?", (fp,))
    conn.commit()
    if old_lk and _redis_enabled():
        try:
            r = _redis_client()
            if r:
                r.delete(f"{_R_KEY_REVISIT_PIN}{old_lk}")
        except Exception:
            pass
    return int(cur.rowcount or 0)


def redis_delete_user_profile(fingerprint: str) -> None:
    r = _redis_client()
    if not r:
        return
    fp = str(fingerprint or "").strip()
    if not fp:
        return
    try:
        r.delete(_r_key_uprof(fp))
        r.zrem(_R_KEY_UPROF_TL, fp)
    except Exception:
        log.exception("redis_delete_user_profile failed")


def delete_user_profile(fingerprint: str) -> int:
    """단일 사용자 프로필 삭제. SQLite는 삭제된 행 수(0이면 없던 키)."""
    fp = str(fingerprint or "").strip()
    if not fp:
        return 0
    n = sqlite_delete_user_profile(fp)
    if _redis_enabled():
        redis_delete_user_profile(fp)
    return int(n)


def load_consultation_archive_records(
    max_rows: int = 4000, session_id: str | None = None
) -> list[dict[str, Any]]:
    """
    상담(채팅) 아카이브 최근 N건.

    대용량 JSONL 전체 스캔 대신 SQLite `chat_archive` + LIMIT(및 선택적 session_id 인덱스)를 사용합니다.
    pandas가 설치돼 있으면 `read_sql_query`로 컬럼을 한 번에 읽고, 없으면 sqlite 커서 경로로 동일 결과를 냅니다.
    """
    mr = max(1, int(max_rows))
    raw_sid = str(session_id or "").strip()
    sid = coalesce_session_id(raw_sid) if raw_sid else None
    if raw_sid and not sid:
        return []
    if sid:
        sqlite_rows = sqlite_archive_load_session(sid, mr)
        return _redis_read_fallback(
            sqlite_rows,
            lambda: redis_archive_load_session_recent(sid, mr),
        )
    sqlite_rows = sqlite_archive_load_recent(mr)
    return _redis_read_fallback(
        sqlite_rows,
        lambda: redis_archive_load_recent(mr),
    )


def archive_append_record(rec: dict[str, Any]) -> None:
    raw = dict(rec or {})
    sid = coalesce_session_id(str(raw.get("session_id") or ""))
    if not sid:
        log.warning("archive_append_record skipped: invalid session_id")
        return
    row = sanitize_archive_record(raw)
    row["session_id"] = sid
    sqlite_archive_append(row)
    if _redis_enabled():
        redis_archive_append(row)


def archive_load_recent(max_lines: int = 4000) -> list[dict[str, Any]]:
    """호환용 별칭: `load_consultation_archive_records(max_rows=…)` 와 동일."""
    return load_consultation_archive_records(max_rows=max_lines, session_id=None)


def archive_prune_old_records(
    days: int = 180,
    *,
    batch_size: int = 2000,
    vacuum_sqlite: bool = False,
) -> dict[str, Any]:
    """오래된 상담 아카이브를 SQLite·Redis에서 정리합니다 (cron/작업 스케줄러용).

    Parameters
    ----------
    days
        보관 일수. 이보다 오래된 ``chat_archive.created_at`` / Redis 타임라인 점수를 삭제합니다.
    batch_size
        한 번에 삭제할 최대 행 수(반복 실행으로 대량 삭제).
    vacuum_sqlite
        SQLite 삭제 후 ``VACUUM`` 실행(디스크 회수, 대용량 시 시간 소요).
    """
    keep_days = max(1, int(days))
    batch = max(50, min(int(batch_size), 10_000))
    cutoff_dt = _dt.datetime.now(tz=ZoneInfo("Asia/Seoul")) - _dt.timedelta(
        days=keep_days
    )
    cutoff_iso = cutoff_dt.isoformat(timespec="seconds")
    cutoff_ms = cutoff_dt.timestamp() * 1000.0

    before_sqlite = sqlite_archive_count()
    sqlite_deleted = sqlite_archive_prune_before(cutoff_iso, batch_size=batch)
    after_sqlite = sqlite_archive_count()

    redis_deleted = 0
    if _redis_enabled():
        redis_deleted = redis_archive_prune_before(cutoff_ms, batch_size=batch)

    vacuum_ran = False
    if vacuum_sqlite and sqlite_deleted > 0:
        try:
            sqlite_vacuum()
            vacuum_ran = True
        except Exception:
            log.exception("sqlite_vacuum after archive prune failed")

    result = {
        "days": keep_days,
        "cutoff_iso": cutoff_iso,
        "batch_size": batch,
        "sqlite_deleted": int(sqlite_deleted),
        "sqlite_rows_before": int(before_sqlite),
        "sqlite_rows_after": int(after_sqlite),
        "redis_deleted": int(redis_deleted),
        "redis_enabled": _redis_enabled(),
        "vacuum_sqlite": bool(vacuum_ran),
        "total_deleted": int(sqlite_deleted) + int(redis_deleted),
    }
    log.info("archive_prune_old_records: %s", result)
    return result


def archive_delete_session(session_id: str) -> int:
    sid = coalesce_session_id(session_id)
    if not sid:
        return 0
    n = sqlite_archive_delete_session(sid)
    if _redis_enabled():
        try:
            redis_archive_delete_session(sid)
        except Exception as e:
            _redis_note_failure(e)
    try:
        box = load_admin_outbox_dict()
        if sid in box:
            box.pop(sid, None)
            save_admin_outbox_dict(box)
    except Exception:
        pass
    return n


def archive_clear_all() -> None:
    """상담(채팅) 아카이브 전체 삭제(방/kv는 유지)."""
    try:
        sqlite_archive_clear_all()
    except Exception:
        pass
    if _redis_enabled():
        # v2 타임라인 + 세션 인덱스 + row 키까지 모두 삭제 (강제 GC)
        try:
            r = _redis_client()
            if not r:
                return
            _redis_archive_clear_all_strict(r)
        except Exception as e:
            _redis_note_failure(e)


@_with_sqlite
def sqlite_archive_clear_all(conn) -> int:
    cur = conn.execute("DELETE FROM chat_archive")
    conn.commit()
    return int(cur.rowcount or 0)


def _redis_archive_clear_all_strict(r) -> None:
    """Redis v2 아카이브를 row key까지 완전 삭제.

    구성:
    - `_ARCH_TIMELINE` (ZSET): row_id 타임라인
    - `_redis_arch_row_key(row_id)` (STRING): payload
    - `_redis_arch_sess_set_key(session_id)` (SET): session_id -> row_id 인덱스
    - `_ARCH_LEGACY_LIST` (LIST): 구버전
    """
    # 1) 타임라인에서 row_id를 청크로 읽어 row 키 삭제
    chunk = 1000
    start = 0
    while True:
        try:
            ids = r.zrange(_ARCH_TIMELINE, start, start + chunk - 1) or []
        except Exception:
            ids = []
        if not ids:
            break
        pipe = r.pipeline()
        for rid in ids:
            if rid:
                pipe.delete(_redis_arch_row_key(str(rid)))
        try:
            pipe.execute()
        except Exception:
            pass
        start += chunk

    # 2) 세션 인덱스 set 키를 SCAN으로 찾아 삭제
    try:
        cursor = 0
        match = f"{_NS}:arch:s:*"
        while True:
            cursor, keys = r.scan(cursor=cursor, match=match, count=500)  # type: ignore
            if keys:
                try:
                    r.delete(*keys)
                except Exception:
                    for k in keys:
                        try:
                            r.delete(k)
                        except Exception:
                            pass
            if int(cursor) == 0:
                break
    except Exception:
        pass

    # 3) 타임라인/레거시/마커 정리
    try:
        r.delete(_ARCH_TIMELINE)
    except Exception:
        pass
    try:
        r.delete(_ARCH_LEGACY_LIST)
    except Exception:
        pass
    try:
        r.set(_ARCH_V2_MARKER, "1")
    except Exception:
        pass


def load_admin_outbox_dict() -> dict[str, Any]:
    d = kv_get_json("admin_outbox")
    return d if isinstance(d, dict) else {}


def save_admin_outbox_dict(data: dict[str, Any]) -> None:
    kv_set_json("admin_outbox", data)


def clear_all_persisted_data() -> None:
    sqlite_clear_all()
    if _redis_enabled():
        redis_clear_all()


# 브리핑 API (구현: saju_briefing_api.py — FastAPI·스크립트는 saju_storage 경유)
def __getattr__(name: str):
    _briefing_exports = {
        "generate_saju_briefing",
        "load_cached_briefing",
        "get_briefing_by_fingerprint",
        "generate_match_briefing",
        "upsert_user_profile_with_briefing",
    }
    if name in _briefing_exports:
        import saju_briefing_api as _b

        return getattr(_b, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
