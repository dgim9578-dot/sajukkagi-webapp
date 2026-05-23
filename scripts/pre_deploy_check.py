"""배포 전 자동 점검 — ``python scripts/pre_deploy_check.py``"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAIL = 0


def ok(msg: str) -> None:
    print(f"  OK  {msg}")


def warn(msg: str) -> None:
    print(f"  WARN  {msg}")


def fail(msg: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {msg}")


def check_entry() -> None:
    app = ROOT / "app.py"
    requirements = ROOT / "requirements.txt"
    if not app.is_file():
        fail("app.py 없음")
    else:
        ok("app.py 진입점")
    if not requirements.is_file():
        fail("requirements.txt 없음")
    else:
        ok("requirements.txt")


def check_secrets_not_tracked() -> None:
    secrets = ROOT / ".streamlit" / "secrets.toml"
    gitignore = ROOT / ".gitignore"
    if secrets.is_file():
        text = gitignore.read_text(encoding="utf-8", errors="replace")
        if ".streamlit/secrets.toml" in text:
            ok("secrets.toml 이 .gitignore 에 등록됨")
        else:
            fail(".gitignore 에 .streamlit/secrets.toml 추가 필요")
    else:
        warn("로컬 secrets.toml 없음 — 배포 시 Streamlit Secrets 에 입력")


def check_runtime() -> None:
    rt = ROOT / "runtime.txt"
    if rt.is_file():
        ok(f"runtime.txt: {rt.read_text(encoding='utf-8').strip()}")
    else:
        warn("runtime.txt 없음 — Streamlit Cloud 기본 Python 사용")


def compile_python() -> None:
    targets = [
        ROOT / "app.py",
        ROOT / "saju_app",
        ROOT / "saju",
        ROOT / "saju_storage.py",
    ]
    for t in targets:
        if t.is_file():
            try:
                ast.parse(t.read_text(encoding="utf-8"), filename=str(t))
            except SyntaxError as e:
                fail(f"구문 오류 {t}: {e}")
                return
        elif t.is_dir():
            for py in t.rglob("*.py"):
                if "venv" in py.parts or "node_modules" in py.parts:
                    continue
                try:
                    ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
                except SyntaxError as e:
                    fail(f"구문 오류 {py}: {e}")
                    return
    ok("Python 구문 검사 통과")


def import_smoke() -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    try:
        import saju_app.app  # noqa: F401
        import saju_app.ui.steps.router  # noqa: F401
    except Exception as e:
        fail(f"import 실패: {e}")
        return
    ok("핵심 모듈 import")


def check_local_db_ignored() -> None:
    gitignore = ROOT / ".gitignore"
    text = gitignore.read_text(encoding="utf-8", errors="replace")
    for needle in ("saju_app.db", "step2_form_prefill.json", "consultation_chat_archive.jsonl"):
        if needle in text:
            ok(f".gitignore: {needle}")
        else:
            warn(f".gitignore 에 {needle} 없음 — 개인정보 유출 위험")


def main() -> int:
    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        print("=== 사주까기 배포 전 점검 ===\n")
        check_entry()
        check_secrets_not_tracked()
        check_runtime()
        compile_python()
        import_smoke()
        check_local_db_ignored()
        print()
        if FAIL:
            print(f"결과: {FAIL}건 실패 — 수정 후 다시 실행하세요.")
        else:
            print("결과: 배포 준비 OK (WARN 은 확인 권장)")
    text = buf.getvalue()
    print(text, end="")
    report = ROOT / "scripts" / "pre_deploy_report.txt"
    report.write_text(text, encoding="utf-8")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
