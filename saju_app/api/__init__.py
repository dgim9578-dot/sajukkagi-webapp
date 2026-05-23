"""REST API (FastAPI) — Streamlit 앱과 별도 실행."""

from saju_app.api.briefing_router import router as briefing_router

__all__ = ["briefing_router"]
