"""영속화(storage) 파사드 — 루트 ``saju_storage.py`` (+ 확장 모듈) 위임."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
_ROOT_STR = str(_ROOT)
if _ROOT_STR not in sys.path:
    sys.path.insert(0, _ROOT_STR)

# 구 importlib 별칭 캐시 제거
for _stale in ("saju_root_storage", "saju_storage_root_impl"):
    sys.modules.pop(_stale, None)

# 확장 모듈이 등록되도록 saju_storage 를 완전히 로드
if "saju_storage" in sys.modules:
    importlib.reload(sys.modules["saju_storage"])
else:
    import saju_storage  # noqa: F401

import saju_storage as _mod  # noqa: E402


def __getattr__(name: str) -> Any:
    return getattr(_mod, name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(dir(_mod)))


def delete_user_profile(fingerprint: str) -> int:
    """단일 ``user_profiles`` 삭제."""
    direct = getattr(_mod, "delete_user_profile", None)
    if callable(direct):
        return int(direct(fingerprint))
    fp = str(fingerprint or "").strip()
    if not fp:
        return 0
    backend_fn = getattr(_mod, "storage_backend", None)
    backend = str(backend_fn()) if callable(backend_fn) else "sqlite"
    if backend == "redis":
        rfn = getattr(_mod, "redis_delete_user_profile", None)
        if callable(rfn):
            rfn(fp)
            return 1
        return 0
    sfn = getattr(_mod, "sqlite_delete_user_profile", None)
    if callable(sfn):
        return int(sfn(fp))
    return 0
