"""Root launcher for Streamlit.

Run with ``streamlit run app.py``.
앱 본체는 ``saju_app.app:main`` → ``saju_app.ui.steps.router`` 로 위임됩니다.
"""

from __future__ import annotations

import traceback


def _run() -> None:
    try:
        from saju_app.app import main
    except Exception as exc:
        import streamlit as st

        st.error(f"앱 로드 실패: {type(exc).__name__}: {exc}")
        st.code(traceback.format_exc())
        raise
    main()


_run()
