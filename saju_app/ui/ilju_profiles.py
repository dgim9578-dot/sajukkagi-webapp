"""60일주 장문 DB (data/saju_interpretation/ilju_60.json) 로더."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from saju_app.ui.ilju_data import ILJU_JSON_PATH, build_ilju_db, write_ilju_json

_ILJU_JSON = ILJU_JSON_PATH


def _normalize_entry(entry: dict[str, Any]) -> dict[str, str]:
    return {
        "personality": str(entry.get("personality") or "").strip(),
        "career": str(entry.get("career") or "").strip(),
        "relationship": str(entry.get("relationship") or "").strip(),
    }


def _is_usable(prof: dict[str, str] | None) -> bool:
    if not prof:
        return False
    return any(len(str(prof.get(k) or "")) >= 80 for k in ("personality", "career", "relationship"))


def _ensure_ilju_json_on_disk() -> None:
    if _ILJU_JSON.is_file():
        return
    try:
        write_ilju_json(_ILJU_JSON)
    except Exception:
        pass


@lru_cache(maxsize=1)
def _load_ilju_db() -> dict[str, dict[str, Any]]:
    _ensure_ilju_json_on_disk()
    if _ILJU_JSON.is_file():
        try:
            raw = json.loads(_ILJU_JSON.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and raw:
                db = {str(k): v for k, v in raw.items() if isinstance(v, dict)}
                if db:
                    return db
        except (OSError, json.JSONDecodeError):
            pass
    return build_ilju_db()


def get_ilju_profile(ilju: str) -> dict[str, str]:
    """일주 키(예: 己巳) → personality, career, relationship (없으면 빈 문자열)."""
    key = str(ilju or "").strip()
    empty = {"personality": "", "career": "", "relationship": ""}
    if len(key) < 2:
        return empty

    entry = _load_ilju_db().get(key)
    if isinstance(entry, dict):
        prof = _normalize_entry(entry)
        if _is_usable(prof):
            return prof

    try:
        mem = build_ilju_db().get(key)
        if isinstance(mem, dict):
            prof = _normalize_entry(mem)
            if _is_usable(prof):
                return prof
    except Exception:
        pass

    return empty


def reload_ilju_db() -> int:
    _load_ilju_db.cache_clear()
    return len(_load_ilju_db())
