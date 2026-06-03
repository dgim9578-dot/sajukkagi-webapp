"""FastAPI 앱 — ``uvicorn saju_app.api.app:app --reload --port 8000``"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from saju_app.api.briefing_router import router as briefing_router

app = FastAPI(
    title="사주프로 Briefing API",
    version="1.0.0",
    description="3D 사주 브리핑·프로필 연동 REST API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(briefing_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
